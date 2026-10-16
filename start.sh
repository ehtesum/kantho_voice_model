#!/usr/bin/env bash
set -e

echo "Starting Bengali Voice Note Generator..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
