"""Comparison Agent (P4): cross-paper comparison with citation and condition checks."""
from __future__ import annotations

from typing import Any

from agents.common import BaseAgent, dumps
from app.schemas import (Comparison, ComparisonOut, Contradiction, DimEntry, DimRow, Incompatibility,
                         PaperAnalysis, Position, Statement)


def analyses_payload(analyses: list[PaperAnalysis]) -> list[dict[str, Any]]:
    keys = ["research_problem", "objectives", "methodology", "datasets", "findings",
            "quantitative_results", "limitations", "future_directions"]
    out = []
    for a in analyses:
        d = a.model_dump()
        out.append({"paper_id": a.paper_id, "title": a.title, **{k: d[k] for k in keys}})
    return out


def cited_chunk_ids(analyses: list[PaperAnalysis]) -> set[str]:
    ids: set[str] = set()
    for a in analyses:
        d = a.model_dump()
        for key, val in d.items():
            if key == "research_problem" and val:
                ids.update(val["chunk_ids"])
            elif isinstance(val, list) and val and isinstance(val[0], dict) and "chunk_ids" in val[0]:
                for item in val:
                    ids.update(item["chunk_ids"])
    return ids


class ComparisonAgent(BaseAgent):
    name = "ComparisonAgent"
    prompt_id = "P4"

    def run(self, question: str, analyses: list[PaperAnalysis]) -> Comparison:
        if len(analyses) < 2:
            return Comparison(skipped=True, comparable=False,
                              skip_reason="Comparison needs at least two analysed papers; only one was available.")
        allowed_chunks = cited_chunk_ids(analyses)
        allowed_papers = {a.paper_id for a in analyses}
        raw = self.llm.call_json(self.spec, ComparisonOut, question=question,
                                 analyses_json=dumps(analyses_payload(analyses)))
        rejected = 0

        def ids(lst: list[str]) -> list[str]:
            return [i for i in dict.fromkeys(lst) if i in allowed_chunks]

        def pids(lst: list[str]) -> list[str]:
            return [p for p in dict.fromkeys(lst) if p in allowed_papers]

        table: list[DimRow] = []
        for row in raw.table:
            entries = []
            for e in row.entries:
                c = ids(e.chunk_ids)
                if e.paper_id in allowed_papers and c and e.value.strip():
                    entries.append(DimEntry(paper_id=e.paper_id, value=e.value.strip(), chunk_ids=c))
                else:
                    rejected += 1
            if entries:
                table.append(DimRow(dimension=row.dimension, entries=entries))

        def statements(lst: list[Statement]) -> list[Statement]:
            nonlocal rejected
            out = []
            for s in lst:
                c, p = ids(s.chunk_ids), pids(s.paper_ids)
                if s.text.strip() and c and p:
                    out.append(Statement(text=s.text.strip(), paper_ids=p, chunk_ids=c))
                else:
                    rejected += 1
            return out

        contradictions: list[Contradiction] = []
        for c in raw.contradictions:
            pos = []
            for p in c.positions:
                cid = ids(p.chunk_ids)
                if p.paper_id in allowed_papers and cid and p.statement.strip():
                    pos.append(Position(paper_id=p.paper_id, statement=p.statement.strip(), chunk_ids=cid))
            if len({p.paper_id for p in pos}) >= 2:
                contradictions.append(Contradiction(topic=c.topic, positions=pos,
                                                    conditions_comparable=c.conditions_comparable, explanation=c.explanation))
            else:
                rejected += 1

        incompat = []
        for i in raw.incompatibilities:
            p = pids(i.paper_ids)
            if p and i.reason.strip():
                incompat.append(Incompatibility(paper_ids=p, reason=i.reason.strip()))
            else:
                rejected += 1

        return Comparison(comparable=raw.comparable, comparability_notes=raw.comparability_notes, table=table,
                          similarities=statements(raw.similarities), differences=statements(raw.differences),
                          contradictions=contradictions, incompatibilities=incompat, rejected_items=rejected)
