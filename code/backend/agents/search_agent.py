"""Search Agent (P1): research question -> retrieval plan."""
from __future__ import annotations

from agents.common import BaseAgent, dedupe_keep_order
from app.schemas import QueryUnderstanding


class SearchAgent(BaseAgent):
    name = "SearchAgent"
    prompt_id = "P1"

    def run(self, question: str) -> QueryUnderstanding:
        out = self.llm.call_json(self.spec, QueryUnderstanding, question=question)
        kws = dedupe_keep_order(k.strip().lower() for k in out.keywords if k and k.strip())
        if not kws:
            raise ValueError("Query understanding returned no usable keywords")
        out.keywords = kws[:12]
        return out
