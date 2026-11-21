"""Paper Analyst Agent (P3): structured analysis of ONE paper at a time.

Code-level guarantees: every claim keeps only chunk_ids that were actually supplied for this
paper; claims left without a valid ID are dropped; quantitative results are dropped when
their numbers do not appear in the cited passages. Missing fields are reported, not filled."""
from __future__ import annotations

from typing import Any

from agents.common import BaseAgent, format_passages, unsupported_numbers
from app.schemas import Claim, PaperAnalysis, PaperAnalysisOut, QuantResult

LIST_FIELDS = ["objectives", "methodology", "datasets", "findings", "limitations", "future_directions"]


class PaperAnalystAgent(BaseAgent):
    name = "PaperAnalystAgent"
    prompt_id = "P3"

    def run(self, question: str, paper: dict[str, Any], chunks: list[dict[str, Any]]) -> PaperAnalysis:
        by_id = {c["chunk_id"]: c for c in chunks}
        raw = self.llm.call_json(self.spec, PaperAnalysisOut, question=question, paper_title=paper["title"],
                                 paper_id=paper["paper_id"], passages=format_passages(chunks))
        rejected = 0

        def clean_claim(c: Claim) -> Claim | None:
            nonlocal rejected
            ids = [i for i in dict.fromkeys(c.chunk_ids) if i in by_id]
            if not ids or not c.text.strip():
                rejected += 1
                return None
            return Claim(text=c.text.strip(), chunk_ids=ids)

        data: dict[str, Any] = {}
        data["research_problem"] = clean_claim(raw.research_problem) if raw.research_problem else None
        for f in LIST_FIELDS:
            data[f] = [c for c in (clean_claim(x) for x in getattr(raw, f)) if c]
        quants: list[QuantResult] = []
        for q in raw.quantitative_results:
            ids = [i for i in dict.fromkeys(q.chunk_ids) if i in by_id]
            if not ids or not q.value.strip():
                rejected += 1
                continue
            bad = unsupported_numbers(f"{q.value}", [by_id[i]["text"] for i in ids])
            if bad:
                rejected += 1
                continue
            quants.append(QuantResult(metric=q.metric.strip(), value=q.value.strip(), context=q.context, chunk_ids=ids))
        data["quantitative_results"] = quants

        analysis = PaperAnalysis(
            paper_id=paper["paper_id"], title=paper["title"], filename=paper["filename"],
            chunk_ids_provided=[c["chunk_id"] for c in chunks],
            pages_provided=sorted({c["page"] for c in chunks}), rejected_claims=rejected, **data)
        analysis.missing_fields = [f for f in ["research_problem", *LIST_FIELDS, "quantitative_results"]
                                   if not getattr(analysis, f)]
        if len(analysis.missing_fields) == 8:
            raise ValueError("Paper analysis contained no verifiable content")
        return analysis
