#!/usr/bin/env bash
set -e

echo "Setting up kantho_voice_model environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
echo "Setup complete. Run ./start.sh to launch."
