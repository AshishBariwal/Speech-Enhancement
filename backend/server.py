from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import numpy as np
import torch
import torchaudio
import io
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
import soundfile as sf

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(mongo_url)
db = client[os.getenv("DB_NAME", "speech_enhancement")]

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Model config — change these to match your training args ────
MODEL_CHECKPOINT = ROOT_DIR / "best.pt"   # put best.pt next to server.py
MODEL_SR         = 48_000
MODEL_N_FFT      = 512
MODEL_HOP        = 256
MODEL_CH         = 16
MODEL_EMB_DIM    = 128
MODEL_DF_BINS    = 64
MODEL_DF_ORDER   = 3
# ───────────────────────────────────────────────────────────────

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Load DeepFilterLite model at startup
# ─────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")

# Import model — assumes model.py is in the same folder as server.py
import sys
sys.path.insert(0, str(ROOT_DIR))
from model import DeepFilterLite

model = DeepFilterLite(
    n_fft=MODEL_N_FFT,
    hop=MODEL_HOP,
    ch=MODEL_CH,
    emb_dim=MODEL_EMB_DIM,
    df_bins=MODEL_DF_BINS,
    df_order=MODEL_DF_ORDER,
).to(device)

# Dummy forward pass to initialize lazy GRU layers
with torch.no_grad():
    _dummy = torch.randn(1, MODEL_SR * 2).to(device)
    model(_dummy)
    del _dummy

# Load checkpoint
if MODEL_CHECKPOINT.exists():
    ckpt = torch.load(str(MODEL_CHECKPOINT), map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    logger.info(f"Loaded checkpoint: {MODEL_CHECKPOINT} (epoch {ckpt['epoch']})")
else:
    logger.warning(f"Checkpoint not found at {MODEL_CHECKPOINT} — model running with random weights!")


# ─────────────────────────────────────────────
# Metrics helpers
# ─────────────────────────────────────────────
def compute_snr(clean: np.ndarray, noisy: np.ndarray) -> float:
    noise = noisy - clean
    signal_power = np.sum(clean ** 2)
    noise_power  = np.sum(noise ** 2)
    if noise_power == 0:
        return 100.0
    return float(10 * np.log10(signal_power / noise_power + 1e-8))


def compute_si_sdr(reference: np.ndarray, estimation: np.ndarray) -> float:
    reference  = reference  - np.mean(reference)
    estimation = estimation - np.mean(estimation)
    dot        = np.sum(reference * estimation)
    s_ref_sq   = np.sum(reference ** 2)
    if s_ref_sq == 0:
        return 0.0
    s_target = (dot / s_ref_sq) * reference
    e_noise  = estimation - s_target
    return float(10 * np.log10(np.sum(s_target ** 2) / (np.sum(e_noise ** 2) + 1e-8)))


# ─────────────────────────────────────────────
# Core predict function — uses DeepFilterLite
# ─────────────────────────────────────────────
def predict(wav_path: Path) -> tuple:
    """
    Loads a WAV file, runs DeepFilterLite enhancement,
    returns (enhanced_np_float32, sample_rate, snr, si_sdr).
    """
    # Load audio normalized to float32 in [-1, 1]
    wav_np, file_sr = sf.read(str(wav_path), dtype='float32')

    # Convert to tensor
    wav = torch.from_numpy(wav_np).float()

    # If stereo → mono
    if len(wav.shape) > 1:
        wav = wav.mean(dim=1)

    wav = wav.unsqueeze(0)  # shape: [1, T]

    # Resample to model SR if needed
    if file_sr != MODEL_SR:
        wav = torchaudio.functional.resample(wav, file_sr, MODEL_SR)

    noisy_tensor = wav.squeeze(0).to(device)   # [T]

    # Run model
    with torch.no_grad():
        enhanced_tensor, _, _ = model(noisy_tensor.unsqueeze(0))  # [1, T]

    enhanced_tensor = enhanced_tensor.squeeze(0).cpu().clamp(-1, 1)

    # Align lengths
    min_len = min(noisy_tensor.shape[0], enhanced_tensor.shape[0])
    noisy_np    = noisy_tensor.cpu().numpy()[:min_len].astype(np.float32)
    enhanced_np = enhanced_tensor.numpy()[:min_len].astype(np.float32)

    # Compute metrics
    snr_val    = compute_snr(enhanced_np, noisy_np)
    si_sdr_val = compute_si_sdr(noisy_np, enhanced_np)

    return enhanced_np, MODEL_SR, round(snr_val, 2), round(si_sdr_val, 2)


# ─────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────
class PredictResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_id: str
    snr: float
    si_sdr: float
    original_filename: str
    enhanced_filename: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@api_router.get("/")
async def root():
    return {"message": "DeepFilter-Lite Speech Enhancement API", "device": str(device)}


SUPPORTED_EXTENSIONS = ('.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.webm')

@api_router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    file_id = str(uuid.uuid4())
    temp_input_path = UPLOAD_DIR / f"{file_id}_temp{ext}"
    original_path   = UPLOAD_DIR / f"{file_id}_original.wav"

    content = await file.read()
    with open(temp_input_path, "wb") as f:
        f.write(content)

    # Convert/Read audio file and save as standard WAV
    try:
        try:
            data, sr = sf.read(str(temp_input_path))
            sf.write(str(original_path), data, sr)
        except Exception:
            waveform, sr = torchaudio.load(str(temp_input_path))
            if waveform.ndim > 1:
                data = waveform.t().numpy()
            else:
                data = waveform.numpy()
            sf.write(str(original_path), data, sr)
    except Exception as e:
        logger.error(f"Error processing audio file {file.filename}: {e}")
        if temp_input_path.exists():
            temp_input_path.unlink()
        raise HTTPException(status_code=400, detail=f"Could not process audio file: {str(e)}")
    finally:
        if temp_input_path.exists():
            temp_input_path.unlink()

    doc = {
        "file_id":           file_id,
        "original_filename": file.filename,
        "status":            "uploaded",
        "created_at":        datetime.now(timezone.utc).isoformat(),
    }
    await db.audio_files.insert_one(doc)

    return {"file_id": file_id, "filename": file.filename, "status": "uploaded"}


@api_router.post("/predict/{file_id}", response_model=PredictResponse)
async def predict_enhance(file_id: str):
    original_path = UPLOAD_DIR / f"{file_id}_original.wav"

    if not original_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        enhanced_np, sr, snr_value, si_sdr_value = predict(original_path)
    except Exception as e:
        logger.exception(f"Prediction failed for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

    # Save enhanced WAV
    enhanced_path   = UPLOAD_DIR / f"{file_id}_enhanced.wav"
    enhanced_int16  = (enhanced_np * 32767).astype(np.int16)
    enhanced_tensor = torch.from_numpy(enhanced_int16).unsqueeze(0)
    sf.write(
    str(enhanced_path),
    enhanced_np,   # numpy array
    sr,
    subtype='PCM_16'
    )

    # Update MongoDB
    await db.audio_files.update_one(
        {"file_id": file_id},
        {"$set": {
            "status":            "enhanced",
            "snr":               snr_value,
            "si_sdr":            si_sdr_value,
            "enhanced_filename": f"{file_id}_enhanced.wav",
        }}
    )

    record = await db.audio_files.find_one({"file_id": file_id}, {"_id": 0})

    return PredictResponse(
        file_id=file_id,
        snr=snr_value,
        si_sdr=si_sdr_value,
        original_filename=record.get("original_filename", "unknown.wav"),
        enhanced_filename=f"{file_id}_enhanced.wav",
    )


@api_router.get("/download/{file_id}")
async def download_enhanced(file_id: str):
    enhanced_path = UPLOAD_DIR / f"{file_id}_enhanced.wav"

    if not enhanced_path.exists():
        raise HTTPException(status_code=404, detail="Enhanced audio not found. Run predict first.")

    record       = await db.audio_files.find_one({"file_id": file_id}, {"_id": 0})
    original_name = record.get("original_filename", "enhanced.wav") if record else "enhanced.wav"
    download_name = f"enhanced_{original_name}"

    return FileResponse(
        path=str(enhanced_path),
        media_type="audio/wav",
        filename=download_name,
    )


@api_router.get("/audio/{file_id}/{audio_type}")
async def get_audio(file_id: str, audio_type: str):
    if audio_type not in ("original", "enhanced"):
        raise HTTPException(status_code=400, detail="audio_type must be 'original' or 'enhanced'")

    file_path = UPLOAD_DIR / f"{file_id}_{audio_type}.wav"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"{audio_type} audio not found")

    return FileResponse(path=str(file_path), media_type="audio/wav")


# ─────────────────────────────────────────────
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()