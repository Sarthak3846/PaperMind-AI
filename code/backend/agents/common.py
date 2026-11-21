"""Shared helpers for all agents."""
from __future__ import annotations

import json
import re
from typing import Any, Iterable

from app.llm import LLMService
from app.prompts import PromptLibrary
from retrieval.index import Corpus


class AgentError(Exception):
    """An agent produced nothing usable (after validation)."""


class BaseAgent:
    name = "Agent"
    prompt_id = ""

    def __init__(self, llm: LLMService, prompts: PromptLibrary, corpus: Corpus):
        self.llm = llm
        self.prompts = prompts
        self.corpus = corpus

    @property
    def spec(self):
        return self.prompts.get(self.prompt_id)


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def format_passages(chunks: Iterable[dict[str, Any]]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(f"[chunk_id: {c['chunk_id']} | paper: {c['title']} | page {c['page']}]\n{c['text']}")
    return "\n\n".join(blocks)


_NUM = re.compile(r"\d+\.\d+|\d{2,}")


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUM.findall(text.replace(",", ""))}


def unsupported_numbers(claim_text: str, source_texts: Iterable[str]) -> set[str]:
    """Numbers (decimals or 2+ digit integers) in `claim_text` that do not occur in any source text."""
    src = numbers_in(" ".join(source_texts))
    return numbers_in(claim_text) - src


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
