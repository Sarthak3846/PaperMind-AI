@echo off
rem Start the PaperMind frontend on http://localhost:5173
cd /d "%~dp0..\code\frontend"
if not exist node_modules call npm install
npm run dev
