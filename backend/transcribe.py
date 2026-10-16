import whisper
import os
import json
from pathlib import Path

_model = None
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


def load_model(size: str = "small") -> whisper.Whisper:
    global _model
    if _model is None:
        print(f"[Whisper] Loading '{size}' model...")
        _model = whisper.load_model(size)
        print("[Whisper] Model loaded.")
    return _model


def transcribe_file(audio_path: str, language: str = "bn") -> dict:
    """
    Transcribe a single audio file.
    Returns dict with 'text' and 'segments'.
    language='bn' forces Bengali; set to None for auto-detect.
    """
    model = load_model()
    result = model.transcribe(audio_path, language=language, task="transcribe")
    return {
        "file": os.path.basename(audio_path),
        "text": result["text"].strip(),
        "segments": result.get("segments", []),
    }


def transcribe_folder(recordings_dir: str, output_dir: str) -> list[dict]:
    """
    Transcribe all audio files in recordings_dir.
    Saves a transcript .json alongside each file in output_dir.
    Returns list of transcript dicts.
    """
    recordings_path = Path(recordings_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    audio_files = [
        f for f in recordings_path.iterdir()
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not audio_files:
        return results

    for audio_file in sorted(audio_files):
        transcript_file = output_path / (audio_file.stem + ".json")

        if transcript_file.exists():
            with open(transcript_file, "r", encoding="utf-8") as f:
                result = json.load(f)
        else:
            print(f"[Whisper] Transcribing: {audio_file.name}")
            result = transcribe_file(str(audio_file))
            with open(transcript_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        results.append(result)

    return results


def get_transcripts_summary(transcripts_dir: str) -> list[dict]:
    """Load all existing transcript JSONs from a directory."""
    path = Path(transcripts_dir)
    summaries = []
    for json_file in sorted(path.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        summaries.append({
            "file": data.get("file", json_file.stem),
            "text": data.get("text", ""),
        })
    return summaries
