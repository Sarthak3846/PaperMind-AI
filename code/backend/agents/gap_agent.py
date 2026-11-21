"""Research-Gap Agent (P6): gaps that are explicit vs inferred, scoped to the corpus."""
from __future__ import annotations

import re

from agents.comparison_agent import analyses_payload, cited_chunk_ids
from agents.common import BaseAgent, dumps
from app.schemas import Comparison, Gap, GapsOut, GapsResult, PaperAnalysis

GLOBAL_CLAIM = re.compile(
    r"\b(no (?:prior|previous|existing|other) (?:work|stud(?:y|ies)|research|papers?)|no stud(?:y|ies)|"
    r"has not (?:yet )?been (?:studied|explored|investigated|addressed)|never been|"
    r"(?:is|are) the first|first (?:to|study|work|paper)|novel|unexplored|nobody|"
    r"literature (?:lacks|has no)|completely absent|entirely unexplored)\b", re.I)


class ResearchGapAgent(BaseAgent):
    name = "ResearchGapAgent"
    prompt_id = "P6"

    def run(self, question: str, analyses: list[PaperAnalysis], comparison: Comparison) -> GapsResult:
        allowed_chunks = cited_chunk_ids(analyses)
        allowed_papers = {a.paper_id for a in analyses}
        comp = comparison.model_dump() if not comparison.skipped else {"skipped": True, "reason": comparison.skip_reason}
        raw = self.llm.call_json(self.spec, GapsOut, question=question,
                                 analyses_json=dumps(analyses_payload(analyses)), comparison_json=dumps(comp))
        gaps: list[Gap] = []
        rejected = 0
        for g in raw.gaps:
            chunk_ids = [c for c in dict.fromkeys(g.chunk_ids) if c in allowed_chunks]
            paper_ids = [p for p in dict.fromkeys(g.supporting_paper_ids) if p in allowed_papers]
            for c in chunk_ids:  # papers can also be derived from valid chunk IDs
                ch = self.corpus.chunk(c)
                if ch and ch["paper_id"] in allowed_papers and ch["paper_id"] not in paper_ids:
                    paper_ids.append(ch["paper_id"])
            if not g.title.strip() or not g.description.strip() or not paper_ids:
                rejected += 1
                continue
            basis, note = g.basis, ""
            if basis == "explicit" and not chunk_ids:
                basis, note = "inferred", "Downgraded from 'explicit' to 'inferred': no valid source passage was cited."
            flag = bool(GLOBAL_CLAIM.search(f"{g.title} {g.description} {g.why_it_exists}"))
            if flag:
                note = (note + " " if note else "") + (
                    "Wording suggests an absence across the whole literature. The corpus is small, so read this as "
                    "'the provided papers do not address this', not as proof of novelty.")
            gaps.append(Gap(gap_id=f"G{len(gaps) + 1}", title=g.title.strip(), description=g.description.strip(),
                            why_it_exists=g.why_it_exists.strip(), basis=basis, supporting_paper_ids=paper_ids,
                            chunk_ids=chunk_ids, global_claim_flag=flag, note=note))
        titles = ", ".join(a.title for a in analyses)
        disclaimer = (f"Gaps are derived only from the {len(analyses)} analysed paper(s) ({titles}). "
                      "'Explicit' gaps are stated by the authors; 'inferred' gaps are research opportunities suggested by what "
                      "these papers do or do not cover. Nothing here establishes novelty across the wider literature.")
        return GapsResult(gaps=gaps, scope_disclaimer=disclaimer, rejected_items=rejected)
