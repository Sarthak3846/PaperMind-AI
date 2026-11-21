#!/usr/bin/env bash
# Start the PaperMind backend on http://localhost:8000 (run the one-time setup from the README first).
set -e
cd "$(dirname "$0")/../code/backend"
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
[ -f .env ] || { echo "Missing code/backend/.env - copy .env.example to .env and add GEMINI_API_KEY"; exit 1; }
exec uvicorn app.main:app --reload --port 8000
