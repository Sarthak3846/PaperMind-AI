"""Quick sanity check of your API key and model:  python scripts/check_gemini.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.llm import GeminiBackend, LLMNotConfigured  # noqa: E402

s = get_settings()
print(f"Model: {s.gemini_model}")
try:
    out = GeminiBackend(s).generate(system="Reply with JSON only.", user='Return {"ok": true}',
                                    temperature=0, json_mode=True)
    print("Gemini replied:", out.strip()[:200])
    print("OK - your key and model work.")
except LLMNotConfigured as e:
    print("NOT CONFIGURED:", e); sys.exit(1)
except Exception as e:  # noqa: BLE001
    print("FAILED:", e)
    print("If the model was retired, set GEMINI_MODEL (and optionally GEMINI_FALLBACK_MODEL) in .env")
    sys.exit(1)
