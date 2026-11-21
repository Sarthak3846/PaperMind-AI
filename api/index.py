
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "code" / "backend"

sys.path.insert(0, str(BACKEND))

from app.main import app
