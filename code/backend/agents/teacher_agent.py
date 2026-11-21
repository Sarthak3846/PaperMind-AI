"""Teacher Agent (P7): structured literature review; citations restricted to the supplied material."""
from __future__ import annotations

from typing import Any

from agents.comparison_agent import analyses_payload, cited_chunk_ids
from agents.common import AgentError, BaseAgent, dumps
from app.schemas import (Comparison, Evidence, GapsResult, PaperAnalysis, PaperSummary, ReviewOut, ReviewStatement)

SECTIONS = ["research_overview", "cross_paper_synthesis", "agreements_and_contradictions",
            "research_gaps", "limitations", "conclusion"]


class TeacherAgent(BaseAgent):
    name = "TeacherAgent"
    prompt_id = "P7"

    def run(self, question: str, analyses: list[PaperAnalysis], comparison: Comparison,
            gaps: GapsResult, evidence: list[Evidence]) -> ReviewOut:
        allowed = set(cited_chunk_ids(analyses))
        for e in evidence:
            allowed.add(e.chunk_id)
        for g in gaps.gaps:
            allowed.update(g.chunk_ids)
        comp = comparison.model_dump() if not comparison.skipped else {"skipped": True, "reason": comparison.skip_reason}
        allowed_comp: set[str] = set()
        for s in comparison.similarities + comparison.differences:
            allowed_comp.update(s.chunk_ids)
        for c in comparison.contradictions:
            for p in c.positions:
                allowed_comp.update(p.chunk_ids)
        allowed |= {c for c in allowed_comp if self.corpus.has_chunk(c)}

        ev_payload = [{"evidence_id": e.evidence_id, "paper_id": e.paper_id, "chunk_id": e.chunk_id, "claim": e.claim}
                      for e in evidence]
        raw = self.llm.call_json(
            self.spec, ReviewOut, question=question, analyses_json=dumps(analyses_payload(analyses)),
            comparison_json=dumps(comp), gaps_json=dumps([g.model_dump() for g in gaps.gaps]), evidence_json=dumps(ev_payload))

        counter = 0

        def clean(st: ReviewStatement) -> ReviewStatement | None:
            nonlocal counter
            text = st.text.strip()
            if not text:
                return None
            valid = [c for c in dict.fromkeys(st.chunk_ids) if c in allowed]
            invalid = [c for c in dict.fromkeys(st.chunk_ids) if c not in allowed]
            counter += 1
            return ReviewStatement(text=text, chunk_ids=valid, invalid_chunk_ids=invalid, meta=st.meta, sid=f"S{counter}")

        review = ReviewOut()
        for sec in SECTIONS:
            setattr(review, sec, [s for s in (clean(x) for x in getattr(raw, sec)) if s])
        analysed = {a.paper_id for a in analyses}
        summaries = []
        for ps in raw.paper_summaries:
            if ps.paper_id in analysed:
                sts = [s for s in (clean(x) for x in ps.statements) if s]
                if sts:
                    summaries.append(PaperSummary(paper_id=ps.paper_id, statements=sts))
        review.paper_summaries = summaries
        if counter == 0:
            raise AgentError("The literature review contained no usable statements")
        return review


def all_statements(review: ReviewOut) -> list[ReviewStatement]:
    out: list[ReviewStatement] = []
    for sec in SECTIONS:
        out.extend(getattr(review, sec))
    for ps in review.paper_summaries:
        out.extend(ps.statements)
    return out
