import sys
import torch
import numpy as np
import soundfile as sf                          # pip install soundfile
from scipy.signal import resample_poly          # pip install scipy
from math import gcd
import torchaudio.transforms as T
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  ▶  SET YOUR PATHS HERE
# ══════════════════════════════════════════════════════════════
VOICE_PATH  = r"C:\Users\91892\Downloads\p232_001.wav"   # ← your noisy voice
MODEL_PATH  = r"C:\Users\91892\OneDrive\Documents\deepfilternet\DeepFilterNetUI-speachEnhancement\backend\best.pt"   # ← your checkpoin          # ← your checkpoint
SR  = 48000
# ══════════════════════════════════════════════════════════════

sys.path.insert(0, r"C:\Users\91892\OneDrive\Documents\deepfilternet")
from model import DeepFilterLite

# ── Load / Save using soundfile only (no torchaudio I/O) ──────
def load_wav(path, target_sr):
    data, file_sr = sf.read(path, dtype="float32", always_2d=True)
    data = data.mean(axis=1)                    # stereo → mono
    if file_sr != target_sr:
        g = gcd(file_sr, target_sr)
        data = resample_poly(data, target_sr // g, file_sr // g).astype(np.float32)
    return torch.from_numpy(data)

def save_wav(path, wav_tensor, sr):
    sf.write(str(path), wav_tensor.numpy(), sr)

# ── Load model ─────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

model = DeepFilterLite(
    n_fft=512, hop=256, ch=16, emb_dim=128, df_bins=64, df_order=3
).to(device)

with torch.no_grad():
    model(torch.randn(1, SR * 2).to(device))   # init lazy layers

ckpt = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(ckpt["model_state"])
model.eval()
print(f"✓ Model loaded — {ckpt['epoch']} epochs trained")

# ── Load audio ─────────────────────────────────────────────────
noisy_wav = load_wav(VOICE_PATH, SR)
print(f"✓ Audio loaded — {noisy_wav.shape[0]/SR:.2f}s @ {SR}Hz")

# ── Run enhancement ────────────────────────────────────────────
with torch.no_grad():
    enhanced, _, _ = model(noisy_wav.unsqueeze(0).to(device))
enhanced_wav = enhanced.squeeze(0).cpu().clamp(-1, 1)

out_path = Path(VOICE_PATH).parent / (Path(VOICE_PATH).stem + "_enhanced.wav")
save_wav(out_path, enhanced_wav, SR)
print(f"✓ Enhanced audio saved → {out_path}")

# ── Spectrograms (torchaudio.transforms is fine — no I/O) ─────
def to_db_spec(wav_1d, n_fft=1024, hop=256, top_db=80):
    spec = T.Spectrogram(n_fft=n_fft, hop_length=hop, power=2.0)(wav_1d)
    return T.AmplitudeToDB(top_db=top_db)(spec).numpy()

noisy_db    = to_db_spec(noisy_wav)
enhanced_db = to_db_spec(enhanced_wav)
diff_db     = enhanced_db - noisy_db

noisy_np    = noisy_wav.numpy()
enhanced_np = enhanced_wav.numpy()
t           = np.linspace(0, len(noisy_np) / SR, len(noisy_np))
freqs_khz   = np.linspace(0, SR / 2000, 1024 // 2 + 1)
frames      = np.linspace(0, len(noisy_np) / SR, noisy_db.shape[1])
ext         = [frames[0], frames[-1], freqs_khz[0], freqs_khz[-1]]

# ── Plot ───────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 14), facecolor="#0d0d0d")
fig.suptitle("Speech Enhancement — Spectral Analysis",
             color="white", fontsize=18, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.25,
                       left=0.07, right=0.97, top=0.93, bottom=0.05)

LC, TC = "#aaaaaa", "#888888"

def style_ax(ax, title, xlabel="Time (s)", ylabel="Frequency (kHz)"):
    ax.set_facecolor("#111111")
    ax.set_title(title, color="white", fontsize=11, pad=6, fontweight="semibold")
    ax.set_xlabel(xlabel, color=LC, fontsize=9)
    ax.set_ylabel(ylabel, color=LC, fontsize=9)
    ax.tick_params(colors=TC, labelsize=8)
    for s in ax.spines.values(): s.set_edgecolor("#333333")

def add_cbar(im, ax, label):
    cb = plt.colorbar(im, ax=ax, pad=0.02)
    cb.set_label(label, color=LC, fontsize=8)
    cb.ax.tick_params(colors=TC, labelsize=7)

# Row 0 — Waveforms
ax = fig.add_subplot(gs[0, 0])
ax.plot(t, noisy_np, color="#e05252", linewidth=0.4, alpha=0.85)
ax.axhline(0, color="#555", linewidth=0.5); ax.set_xlim(0, t[-1])
style_ax(ax, "Waveform — Noisy Input", ylabel="Amplitude")

ax = fig.add_subplot(gs[0, 1])
ax.plot(t, enhanced_np, color="#52c0e0", linewidth=0.4, alpha=0.85)
ax.axhline(0, color="#555", linewidth=0.5); ax.set_xlim(0, t[-1])
style_ax(ax, "Waveform — Enhanced Output", ylabel="Amplitude")

# Row 1 — Spectrograms
vmin = min(noisy_db.min(), enhanced_db.min())
vmax = max(noisy_db.max(), enhanced_db.max())

ax = fig.add_subplot(gs[1, 0])
im = ax.imshow(noisy_db, origin="lower", aspect="auto",
               extent=ext, cmap="inferno", vmin=vmin, vmax=vmax)
style_ax(ax, "Spectrogram — Noisy Input")
add_cbar(im, ax, "dB")

ax = fig.add_subplot(gs[1, 1])
im = ax.imshow(enhanced_db, origin="lower", aspect="auto",
               extent=ext, cmap="inferno", vmin=vmin, vmax=vmax)
style_ax(ax, "Spectrogram — Enhanced Output")
add_cbar(im, ax, "dB")

# Row 2 — Difference map + PSD
ax = fig.add_subplot(gs[2, 0])
dlim = np.percentile(np.abs(diff_db), 95)
im = ax.imshow(diff_db, origin="lower", aspect="auto",
               extent=ext, cmap="RdBu_r", vmin=-dlim, vmax=dlim)
style_ax(ax, "Difference Map  (Enhanced − Noisy)")
add_cbar(im, ax, "ΔdB  (blue = suppressed  |  red = boosted)")

ax = fig.add_subplot(gs[2, 1])
pn = noisy_db.mean(axis=1)
pe = enhanced_db.mean(axis=1)
ax.plot(freqs_khz, pn, color="#e05252", linewidth=1.2, label="Noisy",    alpha=0.9)
ax.plot(freqs_khz, pe, color="#52c0e0", linewidth=1.2, label="Enhanced", alpha=0.9)
ax.fill_between(freqs_khz, pn, pe, where=(pe > pn),  alpha=0.15, color="#52c0e0", label="Speech gain")
ax.fill_between(freqs_khz, pn, pe, where=(pe <= pn), alpha=0.15, color="#e05252", label="Noise removed")
style_ax(ax, "Avg Power Spectral Density", xlabel="Frequency (kHz)", ylabel="Power (dB)")
ax.set_facecolor("#111111")
ax.legend(fontsize=8, facecolor="#1a1a1a", edgecolor="#444", labelcolor="white")

out_fig = Path(VOICE_PATH).parent / "enhancement_analysis.png"
plt.savefig(str(out_fig), dpi=150, bbox_inches="tight", facecolor="#0d0d0d")
plt.show()
print(f"\n✓ Plot saved → {out_fig}")

print("\n── Audio Stats ───────────────────────────────────")
print(f"  Noisy RMS    : {noisy_np.std():.5f}")
print(f"  Enhanced RMS : {enhanced_np.std():.5f}")
print(f"  Peak noisy   : {np.abs(noisy_np).max():.5f}")
print(f"  Peak enhanced: {np.abs(enhanced_np).max():.5f}")
print("──────────────────────────────────────────────────")