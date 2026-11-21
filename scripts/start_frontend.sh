#!/usr/bin/env bash
# Start the PaperMind frontend on http://localhost:5173
set -e
cd "$(dirname "$0")/../code/frontend"
[ -d node_modules ] || npm install
exec npm run dev
