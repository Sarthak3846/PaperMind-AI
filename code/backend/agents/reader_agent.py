"""Reader Agent (P2): extracts evidence and *verifies it in code*.

An evidence item is kept only if (a) its chunk_id is one of the retrieved chunks and
(b) its quote really occurs in that chunk. Everything else is rejected and reported."""
from __future__ import annotations

from typing import Any

from agents.common import BaseAgent, format_passages
from app.schemas import Evidence, EvidenceExtraction
from retrieval.index import normalise_for_match, quote_in_chunk


class ReaderAgent(BaseAgent):
    name = "ReaderAgent"
    prompt_id = "P2"

    def run(self, question: str, chunks: list[dict[str, Any]]) -> tuple[list[Evidence], list[dict[str, Any]]]:
        by_id = {c["chunk_id"]: c for c in chunks}
        out = self.llm.call_json(self.spec, EvidenceExtraction, question=question, passages=format_passages(chunks))
        kept: list[Evidence] = []
        rejected: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in out.evidence:
            chunk = by_id.get(item.chunk_id)
            if chunk is None:
                rejected.append({"chunk_id": item.chunk_id, "claim": item.claim, "reason": "unknown_chunk_id"})
                continue
            if not quote_in_chunk(item.quote, chunk["text"]):
                rejected.append({"chunk_id": item.chunk_id, "claim": item.claim, "reason": "quote_not_found_in_chunk"})
                continue
            key = (item.chunk_id, normalise_for_match(item.quote))
            if key in seen:
                continue
            seen.add(key)
            kept.append(Evidence(evidence_id=f"E{len(kept) + 1}", paper_id=chunk["paper_id"], page=chunk["page"],
                                 chunk_id=item.chunk_id, quote=item.quote.strip(), claim=item.claim.strip(), kind=item.kind))
        return kept, rejected
