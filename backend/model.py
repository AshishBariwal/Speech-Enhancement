# paste entire model.py content here
"""
DeepFilter-Lite: Simplified DeepFilterNet-style speech enhancement.
No libdf / pydf / libdfdata dependencies. Pure PyTorch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from typing import Optional, Tuple


# ─────────────────────────────────────────────
# STFT / iSTFT helpers
# ─────────────────────────────────────────────
class STFT(nn.Module):
    def __init__(self, n_fft: int = 512, hop: int = 256):
        super().__init__()
        self.n_fft = n_fft
        self.hop = hop
        self.register_buffer("window", torch.hann_window(n_fft))

    def forward(self, x: Tensor) -> Tensor:
        # x: [B, T]  →  [B, F, frames, 2]
        B, T = x.shape 
        spec = torch.stft(
            x, self.n_fft, self.hop,
            window=self.window,
            return_complex=True,
            normalized=True,
        )  # [B, F, frames]
        return torch.view_as_real(spec)  # [B, F, frames, 2]


class ISTFT(nn.Module):
    def __init__(self, n_fft: int = 512, hop: int = 256):
        super().__init__()
        self.n_fft = n_fft
        self.hop = hop
        self.register_buffer("window", torch.hann_window(n_fft))

    def forward(self, spec_real: Tensor, length: Optional[int] = None) -> Tensor:
        # spec_real: [B, F, frames, 2]
        spec = torch.view_as_complex(spec_real.contiguous())
        return torch.istft(
            spec, self.n_fft, self.hop,
            window=self.window,
            normalized=True,
            length=length,
        )


# ─────────────────────────────────────────────
# Power-law compression (as in your original)
# ─────────────────────────────────────────────
def power_compress(x: Tensor, c: float = 0.5) -> Tensor:
    spec = torch.view_as_complex(x.contiguous())
    mag = spec.abs().clamp_min(1e-12)
    phase = spec.angle()
    comp = mag.pow(c) * torch.exp(1j * phase)
    return torch.view_as_real(comp)


def power_decompress(x: Tensor, c: float = 0.5) -> Tensor:
    spec = torch.view_as_complex(x.contiguous())
    mag = spec.abs().clamp_min(1e-12)
    phase = spec.angle()
    decomp = mag.pow(1.0 / c) * torch.exp(1j * phase)
    return torch.view_as_real(decomp)


# ─────────────────────────────────────────────
# Depthwise separable conv block
# ─────────────────────────────────────────────
class DepthwiseConv2d(nn.Module):
    def __init__(self, ch_in: int, ch_out: int, k: int = 3, stride: int = 1):
        super().__init__()
        pad = k // 2
        self.dw = nn.Conv2d(ch_in, ch_in, k, stride=stride, padding=pad, groups=ch_in)
        self.pw = nn.Conv2d(ch_in, ch_out, 1)
        self.bn = nn.BatchNorm2d(ch_out)
        self.act = nn.ELU(inplace=True)

    def forward(self, x: Tensor) -> Tensor:
        return self.act(self.bn(self.pw(self.dw(x))))


class ConvTransposeBlock(nn.Module):
    def __init__(self, ch_in: int, ch_out: int, k: int = 3):
        super().__init__()
        self.block = nn.Sequential(
            nn.ConvTranspose2d(ch_in, ch_out, kernel_size=(1, k),
                               stride=(1, 2), padding=(0, k // 2),
                               output_padding=(0, 1)),
            nn.BatchNorm2d(ch_out),
            nn.ELU(inplace=True),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.block(x)


# ─────────────────────────────────────────────
# Encoder
# ─────────────────────────────────────────────
class Encoder(nn.Module):
    """
    Encodes magnitude spectrum [B, 1, T, F] into embeddings.
    Uses 3 strided depthwise-sep conv layers to downsample frequency axis.
    """
    def __init__(self, ch: int = 16, emb_dim: int = 128):
        super().__init__()
        # Input: [B, 1, T, F]   (T=time, F=freq bins)
        self.conv0 = DepthwiseConv2d(1,      ch,     k=3, stride=1)   # [B, ch,   T, F]
        self.conv1 = DepthwiseConv2d(ch,     ch * 2, k=3, stride=1)   # [B, ch*2, T, F/2] -- freq stride via pool
        self.pool1 = nn.AvgPool2d((1, 2))
        self.conv2 = DepthwiseConv2d(ch * 2, ch * 4, k=3, stride=1)   # [B, ch*4, T, F/4]
        self.pool2 = nn.AvgPool2d((1, 2))
        self.conv3 = DepthwiseConv2d(ch * 4, ch * 4, k=3, stride=1)   # [B, ch*4, T, F/4]

        self.ch = ch
        self.emb_dim = emb_dim

        # GRU over time for global context
        # We'll set gru_in dynamically in forward (depends on F)
        self._gru_built = False
        self._gru_in = None
        self.gru = None  # built lazily
        self.emb_dim = emb_dim

        # SNR estimator head
        self.lsnr_fc = None  # built lazily

    def _build_gru(self, freq_bins: int):
        gru_in = self.ch * 4 * freq_bins
        self.gru = nn.GRU(gru_in, self.emb_dim, num_layers=1, batch_first=False)
        self.lsnr_fc = nn.Sequential(nn.Linear(self.emb_dim, 1), nn.Sigmoid())
        self._gru_in = gru_in
        self._gru_built = True
        # Move to same device as existing params
        device = self.conv0.dw.weight.device
        self.gru = self.gru.to(device)
        self.lsnr_fc = self.lsnr_fc.to(device)

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
        # x: [B, 1, T, F]
        e0 = self.conv0(x)                    # [B, ch,   T, F]
        e1 = self.pool1(self.conv1(e0))        # [B, ch*2, T, F/2]
        e2 = self.pool2(self.conv2(e1))        # [B, ch*4, T, F/4]
        e3 = self.conv3(e2)                    # [B, ch*4, T, F/4]

        B, C, T, F4 = e3.shape
        if not self._gru_built:
            self._build_gru(F4)

        # Flatten freq+ch → GRU input
        emb_in = e3.permute(2, 0, 1, 3).reshape(T, B, C * F4)  # [T, B, C*F4]
        emb, _ = self.gru(emb_in)                               # [T, B, emb_dim]
        emb = emb.transpose(0, 1)                               # [B, T, emb_dim]

        lsnr = self.lsnr_fc(emb)                                # [B, T, 1]
        return e0, e1, e2, e3, emb, lsnr


# ─────────────────────────────────────────────
# Mask Decoder (ERB-style)
# ─────────────────────────────────────────────
class MaskDecoder(nn.Module):
    """
    Decodes embedding + skip connections → real-valued mask in [0,1].
    Skip connections from encoder (U-Net style).
    """
    def __init__(self, ch: int = 16, emb_dim: int = 128):
        super().__init__()
        self.ch = ch
        self.emb_dim = emb_dim
        self._built = False
        self.fc_emb = None
        self.convt2 = ConvTransposeBlock(ch * 4, ch * 2)
        self.convt1 = ConvTransposeBlock(ch * 2, ch)
        self.conv_out = nn.Sequential(
            nn.Conv2d(ch, 1, kernel_size=3, padding=1),
            nn.Sigmoid()
        )
        # 1x1 pathway convs to align skip channels
        # Note: e2 comes from pool2(conv2(e1)) so has ch*4 channels (not ch*2)
        self.skip2 = nn.Conv2d(ch * 4, ch * 4, 1)
        self.skip1 = nn.Conv2d(ch * 4, ch * 2, 1)   # e2 has ch*4 channels
        self.skip0 = nn.Conv2d(ch,     ch,     1)

    def _build_fc(self, emb_width: int, freq4: int):
        out_dim = emb_width * freq4
        self.fc_emb = nn.Sequential(
            nn.Linear(self.emb_dim, out_dim),
            nn.ReLU(inplace=True),
        )
        device = self.convt2.block[0].weight.device
        self.fc_emb = self.fc_emb.to(device)
        self._built = True
        self._out_dim = out_dim
        self._emb_width = emb_width
        self._freq4 = freq4

    def forward(self, emb: Tensor, e3: Tensor, e2: Tensor, e1: Tensor, e0: Tensor) -> Tensor:
        B, C, T, F4 = e3.shape
        if not self._built:
            self._build_fc(C, F4)

        # Project embedding → spatial
        d = self.fc_emb(emb)                         # [B, T, C*F4]
        d = d.view(B, T, C, F4).permute(0, 2, 1, 3)  # [B, C, T, F4]

        # U-Net decode with skips
        d = self.convt2(self.skip2(e3) + d)           # [B, ch*2, T, F4*2]
        # Align skip e2 size
        d = self._align_and_add(d, self.skip1(e2))
        d = self.convt1(d)                            # [B, ch,   T, F4*4]
        d = self._align_and_add(d, self.skip0(e0))
        m = self.conv_out(d)                          # [B, 1, T, F]
        return m

    @staticmethod
    def _align_and_add(x: Tensor, skip: Tensor) -> Tensor:
        # Align spatial dims if mismatch (can occur with odd sizes)
        if x.shape != skip.shape:
            x = F.interpolate(x, size=skip.shape[2:], mode='nearest')
        return x + skip


# ─────────────────────────────────────────────
# Deep Filtering Decoder (simplified)
# ─────────────────────────────────────────────
class DFDecoder(nn.Module):
    """
    Estimates complex filter coefficients for deep filtering.
    Simplified: single-order complex filter applied in frequency domain.
    """
    def __init__(self, emb_dim: int = 128, df_bins: int = 64, df_order: int = 3):
        super().__init__()
        self.df_bins = df_bins
        self.df_order = df_order
        self.gru = nn.GRU(emb_dim, emb_dim, num_layers=1, batch_first=False)
        self.fc_out = nn.Sequential(
            nn.Linear(emb_dim, df_bins * df_order * 2),
            nn.Tanh()
        )
        self.fc_alpha = nn.Sequential(nn.Linear(emb_dim, 1), nn.Sigmoid())

    def forward(self, emb: Tensor) -> Tuple[Tensor, Tensor]:
        # emb: [B, T, emb_dim]
        h, _ = self.gru(emb.transpose(0, 1))     # [T, B, emb_dim]
        h = h.transpose(0, 1)                     # [B, T, emb_dim]
        alpha = self.fc_alpha(h)                  # [B, T, 1]
        coefs = self.fc_out(h)                    # [B, T, df_bins*order*2]
        B, T, _ = coefs.shape
        coefs = coefs.view(B, T, self.df_order, self.df_bins, 2)
        return coefs, alpha


def apply_df(spec: Tensor, coefs: Tensor, alpha: Tensor, df_bins: int) -> Tensor:
    """
    Apply deep filtering to low-frequency bins.
    spec:  [B, F, T, 2]
    coefs: [B, T, order, df_bins, 2]
    alpha: [B, T, 1]
    """
    B, F, T, _ = spec.shape
    order = coefs.shape[2]

    # Work on low-freq slice: [B, df_bins, T, 2]
    spec_low = spec[:, :df_bins, :, :]

    # Convert to complex for filtering
    spec_cplx = torch.view_as_complex(spec_low.permute(0, 2, 1, 3).contiguous())  # [B, T, df_bins]
    coefs_cplx = torch.view_as_complex(coefs.contiguous())                        # [B, T, order, df_bins]

    # Simple 1-step weighted sum over order (causal approximation)
    filtered = (coefs_cplx * spec_cplx.unsqueeze(2)).sum(dim=2)  # [B, T, df_bins]

    # Blend: alpha controls mix between mask-only and DF output
    alpha_t = alpha.squeeze(-1).unsqueeze(-1)  # [B, T, 1]
    out_cplx = alpha_t * filtered + (1 - alpha_t) * spec_cplx
    out_real = torch.view_as_real(out_cplx).permute(0, 2, 1, 3)  # [B, df_bins, T, 2]

    # Replace low-freq bins in spec
    spec = spec.clone()
    spec[:, :df_bins, :, :] = out_real
    return spec


# ─────────────────────────────────────────────
# Main model
# ─────────────────────────────────────────────
class DeepFilterLite(nn.Module):
    """
    Lightweight DeepFilter-style speech enhancement model.
    No libdf dependency. Pure PyTorch.

    Architecture:
      STFT → power compress →
        Encoder (depthwise conv + GRU) →
          MaskDecoder (U-Net skip) →
          DFDecoder (GRU + complex filter) →
        iSTFT → waveform

    Parameters: ~1.5M  (vs ~3.5M for original DFNet2)
    """
    def __init__(
        self,
        n_fft: int = 512,
        hop: int = 256,
        ch: int = 16,
        emb_dim: int = 128,
        df_bins: int = 64,
        df_order: int = 3,
        compress: float = 0.5,
    ):
        super().__init__()
        self.n_fft = n_fft
        self.hop = hop
        self.compress = compress
        self.df_bins = df_bins

        self.stft = STFT(n_fft, hop)
        self.istft = ISTFT(n_fft, hop)
        self.encoder = Encoder(ch=ch, emb_dim=emb_dim)
        self.mask_dec = MaskDecoder(ch=ch, emb_dim=emb_dim)
        self.df_dec = DFDecoder(emb_dim=emb_dim, df_bins=df_bins, df_order=df_order)

    def forward(self, noisy_wav: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Args:
            noisy_wav: [B, T] waveform at 48kHz
        Returns:
            enhanced_wav: [B, T]
            mask:         [B, 1, T, F]  (for loss)
            lsnr:         [B, T, 1]     (for loss)
        """
        length = noisy_wav.shape[-1]

        # 1. STFT → [B, F, frames, 2]
        spec = self.stft(noisy_wav)

        # 2. Power compression
        spec_c = power_compress(spec, self.compress)

        # 3. Magnitude for encoder input: [B, 1, frames, F]
        mag = spec_c.pow(2).sum(-1).sqrt()           # [B, F, frames]
        enc_in = mag.permute(0, 2, 1).unsqueeze(1)  # [B, 1, frames, F]

        # 4. Encode
        e0, e1, e2, e3, emb, lsnr = self.encoder(enc_in)

        # 5. Mask decode → [B, 1, frames, F]
        mask = self.mask_dec(emb, e3, e2, e1, e0)

        # 6. Apply mask to compressed spec
        # spec_c: [B, F, frames, 2]; mask: [B, 1, frames, F]
        mask_t = mask.squeeze(1).permute(0, 2, 1)  # [B, frames, F]
        spec_masked = spec_c * mask_t.unsqueeze(-1)  # [B, F, frames, 2]

        # 7. Deep filtering on low-freq bins
        coefs, alpha = self.df_dec(emb)
        spec_df = apply_df(spec_masked, coefs, alpha, self.df_bins)

        # 8. Decompress
        spec_out = power_decompress(spec_df, self.compress)

        # 9. iSTFT
        enhanced = self.istft(spec_out, length=length)

        return enhanced, mask, lsnr
