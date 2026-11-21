@echo off
rem Start the PaperMind backend on http://localhost:8000 (run the one-time setup from the README first).
cd /d "%~dp0..\code\backend"
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
if not exist .env (
  echo Missing code\backend\.env - copy .env.example to .env and add GEMINI_API_KEY
  exit /b 1
)
uvicorn app.main:app --reload --port 8000
