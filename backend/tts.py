import os
import uuid
import threading
import torch
from pathlib import Path
from TTS.api import TTS

_tts_model = None
_tts_lock = threading.Lock()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


# FIX BUG-34: race condition — concurrent requests both saw _tts_model is None and loaded the model twice;
# double-checked locking: outer check avoids lock overhead on hot path, inner check prevents duplicate load
def load_model() -> TTS:
    global _tts_model
    if _tts_model is None:
        with _tts_lock:
            if _tts_model is None:
                print(f"[TTS] Loading XTTS v2 on {DEVICE}...")
                _tts_model = TTS(MODEL_NAME, gpu=(DEVICE == "cuda"))
                print("[TTS] Model loaded.")
    return _tts_model


def get_reference_clip(reference_dir: str) -> str | None:
    """
    Return the path of the first valid audio file in the reference folder.
    Preference order: .wav > .mp3 > others.
    """
    ref_path = Path(reference_dir)
    for ext in [".wav", ".mp3", ".m4a", ".ogg", ".flac"]:
        files = sorted(ref_path.glob(f"*{ext}"))
        if files:
            return str(files[0])
    return None


def synthesize(
    text: str,
    reference_dir: str,
    output_dir: str,
    language: str = "bn",
) -> dict:
    """
    Generate speech for `text` using voice cloning from reference_dir.
    Returns dict with output file path and metadata.
    """
    reference_clip = get_reference_clip(reference_dir)
    if reference_clip is None:
        raise FileNotFoundError(
            "No reference audio found in data/reference/. "
            "Please upload at least one .wav or .mp3 clip of your voice."
        )

    tts = load_model()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex[:8]}.wav"
    out_file = str(output_path / filename)

    tts.tts_to_file(
        text=text,
        speaker_wav=reference_clip,
        language=language,
        file_path=out_file,
    )

    return {
        "file": filename,
        "path": out_file,
        "reference_used": os.path.basename(reference_clip),
        "language": language,
        "text": text,
    }
