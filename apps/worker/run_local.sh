#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
