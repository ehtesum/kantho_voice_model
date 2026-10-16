"""
Pre-download all required models before first run.
Run once after setup: python scripts/download_models.py

Downloads:
  - XTTS v2        (~2 GB) -> ~/.cache/huggingface/hub/
  - Whisper base   (~150 MB) -> ~/.cache/whisper/
"""
import sys


def download_xtts():
    print("Downloading XTTS v2 (~2 GB) — this may take several minutes...")
    try:
        from TTS.api import TTS
        TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("  XTTS v2 downloaded.")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Make sure TTS is installed: pip install TTS==0.22.0")
        sys.exit(1)


def download_whisper():
    print("Downloading Whisper base (~150 MB)...")
    try:
        import whisper
        whisper.load_model("base")
        print("  Whisper base downloaded.")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Make sure openai-whisper is installed: pip install openai-whisper")
        sys.exit(1)


if __name__ == "__main__":
    print("=== Model Download ===")
    print("Models will be saved to ~/.cache/ and reused on subsequent runs.\n")
    download_whisper()
    download_xtts()
    print("\nAll models downloaded. You can now run start.bat.")
