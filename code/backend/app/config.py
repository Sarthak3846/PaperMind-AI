"""Central configuration. All paths are relative to the repository root, so the
project runs unchanged on Windows, macOS and Linux."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(BACKEND_DIR / ".env")
load_dotenv()  # also honour a .env in the current working directory


@dataclass(frozen=True)
class Settings:
    dataset_dir: Path
    data_dir: Path
    processed_dir: Path
    manifest_path: Path
    prompts_dir: Path
    prompt_version: str
    gemini_api_key: str
    gemini_model: str
    gemini_fallback_model: str
    llm_max_retries: int
    max_papers_per_query: int
    max_question_chars: int
    cors_origins: tuple[str, ...]


def get_settings() -> Settings:
    """Read settings from the environment on every call (keeps tests simple)."""
    data_dir = BACKEND_DIR / "data"
    dataset_override = os.getenv("PAPERMIND_DATASET_DIR", "").strip()
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return Settings(
        dataset_dir=Path(dataset_override) if dataset_override else REPO_ROOT / "DATASET",
        data_dir=data_dir,
        processed_dir=data_dir / "processed",
        manifest_path=data_dir / "papers_manifest.json",
        prompts_dir=REPO_ROOT / "prompts",
        prompt_version=os.getenv("PROMPT_VERSION", "final").strip() or "final",
        gemini_api_key=(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip(),
        gemini_fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", "").strip(),
        llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
        max_papers_per_query=int(os.getenv("MAX_PAPERS_PER_QUERY", "4")),
        max_question_chars=1000,
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
    )
