"""A scripted stand-in for Gemini, used ONLY by the unit tests.

It reads the real prompt text, so its answers contain real chunk IDs and verbatim quotes from
the corpus. Individual tests override a prompt's behaviour to inject faults (invalid JSON,
fabricated IDs, API errors). Results produced with this fake are NOT evidence about Gemini's
behaviour and must never go into the Milestone 2 test table."""
from __future__ import annotations

import json
import re
from typing import Callable

from app.llm import BackendError

KEYS = {
    "Query Understanding": "P1", "Evidence Extraction": "P2", "Individual Paper Analysis": "P3",
    "Cross-Paper Comparison": "P4", "Evidence Critic": "P5", "Research-Gap Identification": "P6",
    "Teacher Agent": "P7", "Citation Verifier": "P8",
}
PASSAGE = re.compile(r"\[chunk_id: (.+?) \| paper: (.+?) \| page (\d+)\]\n(.*?)(?=\n\n\[chunk_id: |\Z)", re.S)


def which(system: str) -> str:
    for k, v in KEYS.items():
        if k in system:
            return v
    raise AssertionError("unrecognised prompt: " + system[:80])


def _json_after(user: str, label_regex: str):
    m = re.search(label_regex + r"[^\n]*:\n(.*?)(?:\n\n[A-Z][^\n]*:\n|\Z)", user, re.S)
    return json.loads(m.group(1))


class FakeBackend:
    def __init__(self, overrides: dict[str, Callable[[str, str], str]] | None = None):
        self.overrides = overrides or {}
        self.calls: list[str] = []

    def generate(self, *, system, user, temperature, json_mode, model=None) -> str:
        pid = which(system)
        self.calls.append(pid)
        if pid in self.overrides:
            return self.overrides[pid](system, user)
        return json.dumps(getattr(self, "_" + pid.lower())(user))

    # ---- default (well-behaved) answers
    def _p1(self, user):
        q = user.split("Researcher question:")[-1].strip()
        words = [w for w in re.findall(r"[A-Za-z\-]+", q.lower()) if len(w) > 3][:8] or ["rag"]
        return {"task_type": "comparison" if "compare" in q.lower() else "literature_review", "keywords": words,
                "sub_questions": [q], "ambiguities": []}

    def _p2(self, user):
        items = []
        for cid, _t, _p, text in PASSAGE.findall(user)[:8]:
            quote = " ".join(text.split()[:20])
            items.append({"chunk_id": cid, "quote": quote, "claim": "Passage states: " + quote[:60], "kind": "fact"})
        return {"evidence": items}

    def _p5(self, user):
        ev = json.loads(user.split("Evidence items (JSON):\n")[-1])
        return {"validated_ids": [e["evidence_id"] for e in ev], "flagged": [], "contradictions": [], "missing_information": []}

    def _p3(self, user):
        pid = re.search(r"\(paper_id: (.+?)\)", user).group(1)
        chunks = [c[0] for c in PASSAGE.findall(user)]
        c = lambda i: [chunks[min(i, len(chunks) - 1)]]
        return {"research_problem": {"text": f"Problem of {pid}", "chunk_ids": c(0)},
                "objectives": [], "methodology": [{"text": f"Method of {pid}", "chunk_ids": c(1)}],
                "datasets": [], "findings": [{"text": f"Finding of {pid}", "chunk_ids": c(2)}],
                "quantitative_results": [], "limitations": [], "future_directions": []}

    def _analyses(self, user):
        return _json_after(user, r"Paper analyses \(JSON")

    def _p4(self, user):
        an = self._analyses(user)
        first = lambda a: a["research_problem"]["chunk_ids"][0]
        a0, a1 = an[0], an[1]
        return {"comparable": True, "comparability_notes": "Both address retrieval augmentation.",
                "table": [{"dimension": "methodology", "entries": [
                    {"paper_id": a["paper_id"], "value": a["methodology"][0]["text"], "chunk_ids": a["methodology"][0]["chunk_ids"]} for a in an]}],
                "similarities": [{"text": "Both augment a language model with retrieval.", "paper_ids": [a0["paper_id"], a1["paper_id"]],
                                  "chunk_ids": [first(a0), first(a1)]}],
                "differences": [{"text": "They differ in when retrieval is used.", "paper_ids": [a0["paper_id"], a1["paper_id"]],
                                 "chunk_ids": [first(a0), first(a1)]}],
                "contradictions": [{"topic": "Always vs on-demand retrieval", "conditions_comparable": True, "explanation": "Opposing positions.",
                                    "positions": [{"paper_id": a0["paper_id"], "statement": "Retrieve always", "chunk_ids": [first(a0)]},
                                                  {"paper_id": a1["paper_id"], "statement": "Retrieve on demand", "chunk_ids": [first(a1)]}]}],
                "incompatibilities": []}

    def _p6(self, user):
        an = self._analyses(user)
        a = an[0]
        return {"gaps": [{"title": "Evaluation breadth", "description": "The analysed papers evaluate on limited settings.",
                          "why_it_exists": "Authors report limited benchmarks.", "basis": "explicit",
                          "supporting_paper_ids": [a["paper_id"]], "chunk_ids": [a["research_problem"]["chunk_ids"][0]]},
                         {"title": "Cross-domain transfer", "description": "The provided papers do not address transfer across domains.",
                          "why_it_exists": "No cross-domain experiments appear in the analyses.", "basis": "inferred",
                          "supporting_paper_ids": [x["paper_id"] for x in an], "chunk_ids": []}]}

    def _p7(self, user):
        an = self._analyses(user)
        cid = lambda a: a["research_problem"]["chunk_ids"]
        st = lambda t, a: {"text": t, "chunk_ids": cid(a)}
        a0 = an[0]
        return {"research_overview": [st("Overview of retrieval augmentation.", a0)],
                "paper_summaries": [{"paper_id": a["paper_id"], "statements": [st(f"Summary of {a['paper_id']}.", a)]} for a in an],
                "cross_paper_synthesis": [st("Papers share a retrieval component.", a0)],
                "agreements_and_contradictions": [st("Papers differ in retrieval timing.", a0)],
                "research_gaps": [st("Evaluation breadth is limited.", a0)],
                "limitations": [{"text": "This review reads only retrieved passages from a small corpus.", "chunk_ids": [], "meta": True}],
                "conclusion": [st("Retrieval helps knowledge-intensive tasks.", a0)]}

    def _p8(self, user):
        claims = json.loads(user.split("(JSON):\n")[-1])
        return {"verdicts": [{"sid": c["sid"], "verdict": "supported", "reason": "Matches the passage."} for c in claims]}


def noop_sleep(_s):
    return None
