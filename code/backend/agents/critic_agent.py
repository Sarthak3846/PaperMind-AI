"""Critic Agent (P5): decides which evidence may be used downstream."""
from __future__ import annotations

from agents.common import BaseAgent, dumps
from app.schemas import CriticFlag, CriticReport, Evidence


class CriticAgent(BaseAgent):
    name = "CriticAgent"
    prompt_id = "P5"

    def run(self, question: str, evidence: list[Evidence]) -> tuple[CriticReport, list[Evidence]]:
        payload = [{"evidence_id": e.evidence_id, "paper": self.corpus.paper(e.paper_id)["title"] if self.corpus.paper(e.paper_id) else e.paper_id,
                    "page": e.page, "kind": e.kind, "claim": e.claim, "quote": e.quote} for e in evidence]
        report = self.llm.call_json(self.spec, CriticReport, question=question, evidence_json=dumps(payload))
        known = {e.evidence_id for e in evidence}
        validated = [i for i in dict.fromkeys(report.validated_ids) if i in known]
        flagged_ids = {f.evidence_id for f in report.flagged}
        flagged = [f for f in report.flagged if f.evidence_id in known and f.evidence_id not in validated]
        # items the critic never mentioned are NOT trusted
        for e in evidence:
            if e.evidence_id not in validated and e.evidence_id not in {f.evidence_id for f in flagged}:
                flagged.append(CriticFlag(evidence_id=e.evidence_id, reason="Not validated by the critic"))
        cleaned = CriticReport(
            validated_ids=validated, flagged=flagged,
            contradictions=[c for c in report.contradictions if c.strip()],
            missing_information=[m for m in report.missing_information if m.strip()])
        keep = [e for e in evidence if e.evidence_id in set(validated)]
        return cleaned, keep
