"""Loads prompt files from /prompts/<version>/. One file per prompt:

    ---
    id: P1
    name: Research Query Understanding
    step: 1
    temperature: 0.2
    ---
    ## SYSTEM
    ...
    ## USER
    ... {variables} in curly braces ...

Only {lowercase_names} that are supplied are substituted, so JSON examples inside
a prompt (which contain quotes and colons) are never touched."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

PROMPT_FILES = {
    "P1": "P1_query_understanding.md",
    "P2": "P2_evidence_extraction.md",
    "P3": "P3_paper_analysis.md",
    "P4": "P4_cross_paper_comparison.md",
    "P5": "P5_evidence_critic.md",
    "P6": "P6_research_gap_identification.md",
    "P7": "P7_literature_review_synthesis.md",
    "P8": "P8_citation_verification.md",
}
_VAR = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


class PromptError(Exception):
    pass


@dataclass(frozen=True)
class PromptSpec:
    id: str
    name: str
    version: str
    temperature: float
    system: str
    user_template: str

    def variables(self) -> set[str]:
        return set(_VAR.findall(self.user_template)) | set(_VAR.findall(self.system))

    def render(self, **values: str) -> tuple[str, str]:
        missing = self.variables() - set(values)
        if missing:
            raise PromptError(f"{self.id}: missing prompt variables {sorted(missing)}")

        def sub(match: re.Match[str]) -> str:
            return str(values[match.group(1)])

        return _VAR.sub(sub, self.system), _VAR.sub(sub, self.user_template)


def parse_prompt_file(text: str, version: str) -> PromptSpec:
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n(.*)", text, re.S)
    if not m:
        raise PromptError("prompt file must start with a --- front matter block")
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    body = m.group(2)
    parts = re.split(r"^##\s+(SYSTEM|USER)\s*$", body, flags=re.M)
    sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    if "USER" not in sections:
        raise PromptError("prompt file needs a '## USER' section")
    return PromptSpec(
        id=meta.get("id", "?"), name=meta.get("name", "?"), version=version,
        temperature=float(meta.get("temperature", "0.2")),
        system=sections.get("SYSTEM", ""), user_template=sections["USER"],
    )


class PromptLibrary:
    def __init__(self, prompts_dir: Path, version: str):
        self.version = version
        self.dir = Path(prompts_dir) / version
        if not self.dir.is_dir():
            raise PromptError(f"Prompt version folder not found: {self.dir}")
        self._cache: dict[str, PromptSpec] = {}

    def get(self, prompt_id: str) -> PromptSpec:
        if prompt_id not in PROMPT_FILES:
            raise PromptError(f"Unknown prompt id {prompt_id}")
        if prompt_id not in self._cache:
            path = self.dir / PROMPT_FILES[prompt_id]
            if not path.exists():
                raise PromptError(f"Missing prompt file {path}")
            self._cache[prompt_id] = parse_prompt_file(path.read_text(encoding="utf-8"), self.version)
        return self._cache[prompt_id]


@lru_cache(maxsize=8)
def _library(prompts_dir: str, version: str) -> PromptLibrary:
    return PromptLibrary(Path(prompts_dir), version)


def get_library(version: str | None = None) -> PromptLibrary:
    s = get_settings()
    return _library(str(s.prompts_dir), version or s.prompt_version)
