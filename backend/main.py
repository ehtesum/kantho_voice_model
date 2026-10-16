import os
import sys
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from transliterate import process_input
from transcribe import transcribe_folder, get_transcripts_summary
from tts import synthesize

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
REFERENCE_DIR = DATA_DIR / "reference"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
OUTPUT_DIR = BASE_DIR / "output"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in [RECORDINGS_DIR, REFERENCE_DIR, TRANSCRIPTS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Voice Note Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class SynthesizeRequest(BaseModel):
    text: str


@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/api/synthesize")
def api_synthesize(req: SynthesizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    processed = process_input(req.text)
    bengali_text = processed["bengali"]

    try:
        result = synthesize(
            text=bengali_text,
            reference_dir=str(REFERENCE_DIR),
            output_dir=str(OUTPUT_DIR),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return {
        "audio_url": f"/output/{result['file']}",
        "filename": result["file"],
        "original_text": processed["original"],
        "bengali_text": bengali_text,
        "was_transliterated": processed["was_transliterated"],
        "reference_used": result["reference_used"],
    }


_UPLOAD_CHUNK = 65_536
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
_ALLOWED_AUDIO = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}


# FIX BUG-32: path traversal — raw client filename like "../../etc/passwd.wav" wrote outside REFERENCE_DIR
def _safe_audio_dest(upload_dir: Path, raw_filename: str) -> Path:
    safe_name = Path(raw_filename).name  # strip any directory components
    if not safe_name or safe_name.startswith(".") or "/" in safe_name or "\\" in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    suffix = Path(safe_name).suffix.lower()
    if suffix not in _ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")
    return upload_dir / safe_name


# FIX BUG-33: memory exhaustion — `await file.read()` buffered the entire upload; now streams in 64 KB chunks
# FIX BUG-45: `await f.close()` inside `async with` caused harmless double-close on exit; on Windows,
# unlink() inside the block could also fail if the OS held the handle until __aexit__ ran.
# Break out of the loop instead, let the context manager close cleanly, then unlink after.
async def _stream_upload(file: UploadFile, dest: Path) -> None:
    written = 0
    too_large = False
    async with aiofiles.open(dest, "wb") as f:
        while True:
            chunk = await file.read(_UPLOAD_CHUNK)
            if not chunk:
                break
            written += len(chunk)
            if written > _MAX_UPLOAD_BYTES:
                too_large = True
                break
            await f.write(chunk)
    if too_large:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="File too large (max 50 MB).")


@app.post("/api/upload-reference")
async def upload_reference(file: UploadFile = File(...)):
    """Upload a voice recording to use as the voice cloning reference."""
    dest = _safe_audio_dest(REFERENCE_DIR, file.filename)
    await _stream_upload(file, dest)
    return {"message": f"Reference clip '{dest.name}' uploaded.", "file": dest.name}


@app.post("/api/upload-recording")
async def upload_recording(file: UploadFile = File(...)):
    """Upload a training recording to data/recordings/."""
    dest = _safe_audio_dest(RECORDINGS_DIR, file.filename)
    await _stream_upload(file, dest)
    return {"message": f"Recording '{dest.name}' uploaded.", "file": dest.name}


@app.post("/api/transcribe")
def api_transcribe():
    """Auto-transcribe all recordings in data/recordings/ using Whisper."""
    recordings = [f for f in RECORDINGS_DIR.iterdir() if f.is_file()]  # FIX BUG-22: iterdir() yields dirs too; is_file() prevents transcribe crash
    if not recordings:
        raise HTTPException(status_code=400, detail="No recordings found in data/recordings/.")

    results = transcribe_folder(str(RECORDINGS_DIR), str(TRANSCRIPTS_DIR))
    return {"transcribed": len(results), "results": results}


@app.get("/api/transcripts")
def api_get_transcripts():
    summaries = get_transcripts_summary(str(TRANSCRIPTS_DIR))
    return {"transcripts": summaries}


@app.get("/api/reference-status")
def api_reference_status():
    files = [f.name for f in REFERENCE_DIR.iterdir() if f.is_file()]
    return {"has_reference": len(files) > 0, "files": files}


@app.get("/api/output-files")
def api_output_files():
    files = sorted(OUTPUT_DIR.glob("*.wav"), key=os.path.getmtime, reverse=True)
    return {
        "files": [f.name for f in files[:20]],
        "items": [
            {"filename": f.name, "url": f"/output/{f.name}"}
            for f in files[:20]
        ],
    }
