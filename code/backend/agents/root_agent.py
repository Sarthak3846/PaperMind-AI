"""Root Agent: orchestrates the pipeline and emits REAL execution events.

It is plain Python (no LLM call). Rules it enforces:
 * a stage that fails never feeds its error text to the next agent
 * missing evidence ends the run with status 'insufficient_evidence' (no invented answer)
 * every event the UI shows is produced here, at the moment the stage runs
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Iterator

from agents.common import AgentError
from agents.comparison_agent import ComparisonAgent
from agents.critic_agent import CriticAgent
from agents.gap_agent import ResearchGapAgent
from agents.paper_analyst import PaperAnalystAgent
from agents.reader_agent import ReaderAgent
from agents.search_agent import SearchAgent
from agents.teacher_agent import SECTIONS, TeacherAgent, all_statements
from agents.verifier import CitationVerifier, VItem
from app.config import Settings, get_settings
from app.llm import LLMError, LLMService
from app.prompts import PromptLibrary
from app.schemas import Comparison, GapsResult, PaperAnalysis, QueryUnderstanding
from retrieval.index import Corpus, tokenize

TOP_K_CHUNKS = 12


class InvalidRequest(Exception):
    pass


class RootAgent:
    name = "RootAgent"

    def __init__(self, llm: LLMService, corpus: Corpus, prompts: PromptLibrary, settings: Settings | None = None):
        self.llm, self.corpus, self.prompts = llm, corpus, prompts
        self.settings = settings or get_settings()
        self.search = SearchAgent(llm, prompts, corpus)
        self.reader = ReaderAgent(llm, prompts, corpus)
        self.critic = CriticAgent(llm, prompts, corpus)
        self.analyst = PaperAnalystAgent(llm, prompts, corpus)
        self.comparer = ComparisonAgent(llm, prompts, corpus)
        self.gapper = ResearchGapAgent(llm, prompts, corpus)
        self.teacher = TeacherAgent(llm, prompts, corpus)
        self.verifier = CitationVerifier(llm, prompts, corpus)
        self._seq = 0

    # ------------------------------------------------------------------ events
    def _ev(self, type_: str, stage: str, agent: str, message: str, *, prompt: str | None = None,
            data: dict | None = None, duration_ms: int | None = None) -> dict[str, Any]:
        self._seq += 1
        return {"seq": self._seq, "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "type": type_, "stage": stage, "agent": agent, "prompt": prompt, "message": message,
                "data": data or {}, "duration_ms": duration_ms}

    # ------------------------------------------------------------------ main
    def run(self, question: str, paper_ids: list[str] | None = None, max_papers: int = 4) -> Iterator[dict[str, Any]]:
        t_start = time.time()
        self._seq = 0
        warnings: list[str] = []
        res: dict[str, Any] = {
            "status": "failed", "question": question, "message": "", "query_understanding": None, "retrieval": None,
            "evidence": [], "rejected_evidence": [], "critic": None, "paper_analyses": [], "comparison": None,
            "gaps": None, "review": None, "references": [], "sources": {}, "verification": None,
            "warnings": warnings, "error": None, "model": self.settings.gemini_model,
            "prompt_version": self.prompts.version,
        }

        def finish(status: str, message: str, error: dict | None = None) -> dict[str, Any]:
            res.update(status=status, message=message, error=error)
            res["metrics"] = {**self.llm.stats.as_dict(), "elapsed_seconds": round(time.time() - t_start, 2)}
            return self._ev("result", "complete", self.name, message, data={"result": res})

        # -------- 1. validate input
        t0 = time.time()
        try:
            question = self._validate(question, paper_ids)
        except InvalidRequest as exc:
            yield self._ev("stage_error", "validate_input", self.name, str(exc))
            yield finish("failed", str(exc), {"stage": "validate_input", "message": str(exc)})
            return
        res["question"] = question
        selected = list(dict.fromkeys(paper_ids)) if paper_ids else None
        yield self._ev("stage_done", "validate_input", self.name,
                       f"Question accepted. Searching {'the ' + str(len(selected)) + ' selected papers' if selected else 'all ' + str(len(self.corpus.papers)) + ' papers'}.",
                       data={"selected_papers": selected or list(self.corpus.papers)}, duration_ms=_ms(t0))

        # -------- 2. query understanding (P1)
        yield self._ev("stage_start", "query_understanding", self.search.name, "Interpreting the research question", prompt="P1")
        t0 = time.time()
        try:
            qu = self.search.run(question)
            yield self._ev("stage_done", "query_understanding", self.search.name,
                           f"Task type: {qu.task_type}; {len(qu.keywords)} search terms",
                           prompt="P1", data={"task_type": qu.task_type, "keywords": qu.keywords,
                                              "sub_questions": qu.sub_questions, "ambiguities": qu.ambiguities},
                           duration_ms=_ms(t0))
        except (LLMError, ValueError) as exc:
            fallback = list(dict.fromkeys(tokenize(question)))
            msg = f"Query understanding failed ({_short(exc)}). Falling back to the raw question terms."
            warnings.append(msg)
            yield self._ev("stage_warning", "query_understanding", self.search.name, msg, prompt="P1", duration_ms=_ms(t0))
            if not fallback:
                yield self._ev("stage_error", "query_understanding", self.search.name, "No usable search terms in the question")
                yield finish("insufficient_evidence", "The question contains no usable search terms.")
                return
            qu = QueryUnderstanding(task_type="literature_review", keywords=fallback[:12])
        res["query_understanding"] = qu.model_dump()

        # -------- 3. retrieval (BM25, no LLM)
        yield self._ev("stage_start", "retrieval", "Retriever", "Searching the paper index (BM25)")
        t0 = time.time()
        n_sel = len(selected) if selected else 0
        eff_max = min(6, max(max_papers, n_sel)) if selected else max_papers
        hits = self.corpus.retrieve(qu.keywords, paper_ids=selected, top_k=TOP_K_CHUNKS, max_papers=eff_max, mention_text=question)
        if not hits:
            hits = self.corpus.retrieve(question, paper_ids=selected, top_k=TOP_K_CHUNKS, max_papers=eff_max, mention_text=question)
        per_paper: dict[str, list] = {}
        for h in hits:
            per_paper.setdefault(h.chunk["paper_id"], []).append(h)
        res["retrieval"] = {
            "terms": qu.keywords, "n_hits": len(hits),
            "papers": [{"paper_id": p, "title": self.corpus.paper(p)["title"], "hits": len(v),
                        "top_score": round(max(x.score for x in v), 2)} for p, v in per_paper.items()],
            "hits": [{"chunk_id": h.chunk_id, "paper_id": h.chunk["paper_id"], "page": h.chunk["page"],
                      "score": round(h.score, 2), "coverage": round(h.coverage, 2)} for h in hits]}
        if not hits:
            yield self._ev("stage_done", "retrieval", "Retriever", "No passages matched the search terms",
                           data=res["retrieval"], duration_ms=_ms(t0))
            yield finish("insufficient_evidence",
                         "No passages in the selected papers matched this question, so no answer was generated. "
                         "The corpus only covers retrieval-augmented generation research.")
            return
        yield self._ev("stage_done", "retrieval", "Retriever",
                       f"{len(hits)} passages from {len(per_paper)} paper(s)", data=res["retrieval"], duration_ms=_ms(t0))

        # -------- 4. evidence extraction (P2)
        yield self._ev("stage_start", "evidence_extraction", self.reader.name, "Extracting verbatim evidence", prompt="P2")
        t0 = time.time()
        try:
            evidence, rejected = self.reader.run(question, [h.chunk for h in hits])
        except LLMError as exc:
            yield self._ev("stage_error", "evidence_extraction", self.reader.name, _short(exc), prompt="P2")
            yield finish("failed", "Evidence extraction failed, so the pipeline stopped. No unverified text was passed on.",
                         {"stage": "evidence_extraction", "message": str(exc)})
            return
        res["evidence"] = [e.model_dump() for e in evidence]
        res["rejected_evidence"] = rejected
        yield self._ev("stage_done", "evidence_extraction", self.reader.name,
                       f"{len(evidence)} evidence items verified against source text; {len(rejected)} rejected",
                       prompt="P2", data={"kept": len(evidence), "rejected": rejected}, duration_ms=_ms(t0))
        if not evidence:
            yield finish("insufficient_evidence", "No verifiable evidence for this question was found in the retrieved passages.")
            return

        # -------- 5. critic (P5)
        yield self._ev("stage_start", "evidence_critique", self.critic.name, "Critiquing evidence", prompt="P5")
        t0 = time.time()
        try:
            critic, evidence_ok = self.critic.run(question, evidence)
        except LLMError as exc:
            yield self._ev("stage_error", "evidence_critique", self.critic.name, _short(exc), prompt="P5")
            yield finish("failed", "Evidence critique failed, so the pipeline stopped.", {"stage": "evidence_critique", "message": str(exc)})
            return
        res["critic"] = critic.model_dump()
        yield self._ev("stage_done", "evidence_critique", self.critic.name,
                       f"{len(evidence_ok)} of {len(evidence)} items validated; {len(critic.flagged)} flagged",
                       prompt="P5", data={"validated": len(evidence_ok), "flagged": len(critic.flagged),
                                          "contradictions": critic.contradictions, "missing_information": critic.missing_information},
                       duration_ms=_ms(t0))
        if not evidence_ok:
            yield finish("insufficient_evidence",
                         "The critic found no retrieved evidence that is both relevant and well supported. "
                         + ("Missing: " + "; ".join(critic.missing_information) if critic.missing_information else ""))
            return
        res["evidence"] = [e.model_dump() for e in evidence_ok]

        # -------- 6. per-paper analysis (P3)
        counts: dict[str, int] = {}
        for e in evidence_ok:
            counts[e.paper_id] = counts.get(e.paper_id, 0) + 1
        paper_order = sorted(counts, key=lambda p: -counts[p])[:eff_max]
        analyses: list[PaperAnalysis] = []
        for i, pid in enumerate(paper_order, start=1):
            paper = self.corpus.paper(pid)
            yield self._ev("stage_start", "paper_analysis", self.analyst.name,
                           f"Analysing paper {i}/{len(paper_order)}: {paper['title']}", prompt="P3", data={"paper_id": pid})
            t0 = time.time()
            try:
                a = self.analyst.run(question, paper, self.corpus.paper_context(pid, qu.keywords))
                analyses.append(a)
                yield self._ev("stage_done", "paper_analysis", self.analyst.name,
                               f"{paper['title']}: {8 - len(a.missing_fields)}/8 fields populated, {a.rejected_claims} unsupported claims removed",
                               prompt="P3", data={"paper_id": pid, "missing_fields": a.missing_fields, "rejected_claims": a.rejected_claims},
                               duration_ms=_ms(t0))
            except (LLMError, ValueError) as exc:
                msg = f"Analysis of '{paper['title']}' failed and was excluded: {_short(exc)}"
                warnings.append(msg)
                yield self._ev("stage_warning", "paper_analysis", self.analyst.name, msg, prompt="P3", data={"paper_id": pid}, duration_ms=_ms(t0))
        if not analyses:
            yield self._ev("stage_error", "paper_analysis", self.analyst.name, "No paper could be analysed")
            yield finish("failed", "No paper analysis succeeded, so the pipeline stopped.", {"stage": "paper_analysis", "message": "all analyses failed"})
            return
        res["paper_analyses"] = [a.model_dump() for a in analyses]

        # -------- 7. comparison (P4)
        yield self._ev("stage_start", "comparison", self.comparer.name, "Comparing papers", prompt="P4")
        t0 = time.time()
        try:
            comparison = self.comparer.run(question, analyses)
            if comparison.skipped:
                msg = comparison.skip_reason
                warnings.append(msg)
                yield self._ev("stage_warning", "comparison", self.comparer.name, msg, prompt="P4", duration_ms=_ms(t0))
            else:
                yield self._ev("stage_done", "comparison", self.comparer.name,
                               f"{len(comparison.similarities)} similarities, {len(comparison.differences)} differences, "
                               f"{len(comparison.contradictions)} contradictions, {len(comparison.incompatibilities)} incompatibilities; "
                               f"{comparison.rejected_items} unsupported items removed",
                               prompt="P4", data={"comparable": comparison.comparable}, duration_ms=_ms(t0))
        except (LLMError, ValueError) as exc:
            msg = f"Comparison failed and was skipped: {_short(exc)}"
            warnings.append(msg)
            comparison = Comparison(skipped=True, comparable=False, skip_reason=msg)
            yield self._ev("stage_warning", "comparison", self.comparer.name, msg, prompt="P4", duration_ms=_ms(t0))
        res["comparison"] = comparison.model_dump()

        # -------- 8. research gaps (P6)
        yield self._ev("stage_start", "gap_identification", self.gapper.name, "Identifying research gaps", prompt="P6")
        t0 = time.time()
        try:
            gaps = self.gapper.run(question, analyses, comparison)
            yield self._ev("stage_done", "gap_identification", self.gapper.name,
                           f"{len(gaps.gaps)} gaps ({sum(g.basis == 'explicit' for g in gaps.gaps)} explicit, "
                           f"{sum(g.basis == 'inferred' for g in gaps.gaps)} inferred); {gaps.rejected_items} unsupported removed",
                           prompt="P6", data={"count": len(gaps.gaps)}, duration_ms=_ms(t0))
        except (LLMError, ValueError) as exc:
            msg = f"Gap identification failed and was skipped: {_short(exc)}"
            warnings.append(msg)
            gaps = GapsResult(gaps=[], scope_disclaimer="Gap identification did not run.")
            yield self._ev("stage_warning", "gap_identification", self.gapper.name, msg, prompt="P6", duration_ms=_ms(t0))
        res["gaps"] = gaps.model_dump()

        # -------- 9. literature review (P7)
        yield self._ev("stage_start", "literature_review", self.teacher.name, "Synthesising the literature review", prompt="P7")
        t0 = time.time()
        try:
            review = self.teacher.run(question, analyses, comparison, gaps, evidence_ok)
        except (LLMError, AgentError, ValueError) as exc:
            yield self._ev("stage_error", "literature_review", self.teacher.name, _short(exc), prompt="P7")
            res["sources"] = self._sources(res)
            yield finish("failed", "The literature review could not be generated. Per-paper analysis, comparison and gaps are still shown below.",
                         {"stage": "literature_review", "message": str(exc)})
            return
        stmts = all_statements(review)
        yield self._ev("stage_done", "literature_review", self.teacher.name, f"Review drafted with {len(stmts)} statements",
                       prompt="P7", data={"statements": len(stmts)}, duration_ms=_ms(t0))

        # -------- 10. citation verification (P8 + code)
        yield self._ev("stage_start", "citation_verification", self.verifier.name,
                       "Verifying every claim against its cited passages", prompt="P8")
        t0 = time.time()
        items = [VItem(s.sid, s.text, list(s.chunk_ids), list(s.invalid_chunk_ids)) for s in stmts if not s.meta]
        items += [VItem(g.gap_id, f"{g.title}: {g.description}", list(g.chunk_ids)) for g in gaps.gaps
                  if g.basis == "explicit" or g.chunk_ids]
        events_buf: list[dict[str, Any]] = []
        results = self.verifier.run(items, on_batch=lambda n, total: events_buf.append(
            self._ev("stage_progress", "citation_verification", self.verifier.name, f"Verifying claims, batch {n}/{total}", prompt="P8")))
        for ev in events_buf:
            yield ev
        for s in stmts:
            r = results.get(s.sid)
            if r:
                s.status, s.status_reason = r.status, r.reason  # type: ignore[assignment]
        for g in gaps.gaps:
            r = results.get(g.gap_id)
            if r:
                g.status, g.status_reason = r.status, r.reason
        counts_v = {"supported": 0, "partially_supported": 0, "unsupported": 0, "unverified": 0}
        for r in results.values():
            counts_v[r.status] += 1
        checked = sum(counts_v.values())
        res["review"] = review.model_dump()
        res["gaps"] = gaps.model_dump()
        res["verification"] = {"checked": checked, **counts_v,
                               "supported_ratio": round(counts_v["supported"] / checked, 3) if checked else None,
                               "meta_statements_not_checked": sum(1 for s in stmts if s.meta)}
        if counts_v["unsupported"] or counts_v["unverified"]:
            warnings.append(f"{counts_v['unsupported']} claim(s) unsupported and {counts_v['unverified']} unverified - see the review for flags.")
        res["sources"] = self._sources(res)
        res["references"] = self._references(review, gaps)
        yield self._ev("stage_done", "citation_verification", self.verifier.name,
                       f"{counts_v['supported']} supported, {counts_v['partially_supported']} partially supported, "
                       f"{counts_v['unsupported']} unsupported, {counts_v['unverified']} unverified",
                       prompt="P8", data=res["verification"], duration_ms=_ms(t0))
        yield finish("completed", "Literature review complete.")

    # ------------------------------------------------------------------ helpers
    def run_to_result(self, question: str, paper_ids: list[str] | None = None, max_papers: int = 4) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for ev in self.run(question, paper_ids, max_papers):
            if ev["type"] == "result":
                result = ev["data"]["result"]
        return result

    def _validate(self, question: str, paper_ids: list[str] | None) -> str:
        q = (question or "").strip()
        if not q:
            raise InvalidRequest("The research question is empty. Please enter a question.")
        if len(q) > self.settings.max_question_chars:
            raise InvalidRequest(f"The question is too long ({len(q)} characters; limit {self.settings.max_question_chars}).")
        if paper_ids is not None:
            if len(paper_ids) == 0:
                raise InvalidRequest("No papers selected. Select at least one paper or leave the selection empty to search all.")
            unknown = [p for p in paper_ids if self.corpus.paper(p) is None]
            if unknown:
                raise InvalidRequest(f"Unknown paper id(s): {', '.join(unknown)}")
        return q

    def _sources(self, res: dict[str, Any]) -> dict[str, Any]:
        ids: set[str] = set()

        def walk(o: Any) -> None:
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "chunk_ids" and isinstance(v, list):
                        ids.update(x for x in v if isinstance(x, str))
                    elif k == "chunk_id" and isinstance(v, str):
                        ids.add(v)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)

        for key in ("evidence", "paper_analyses", "comparison", "gaps", "review"):
            walk(res.get(key))
        out = {}
        for cid in sorted(ids):
            ch = self.corpus.chunk(cid)
            if ch:
                out[cid] = {"chunk_id": cid, "paper_id": ch["paper_id"], "title": ch["title"], "filename": ch["filename"],
                            "page": ch["page"], "text": ch["text"][:900]}
        return out

    def _references(self, review, gaps) -> list[dict[str, Any]]:
        order: list[str] = []
        for s in all_statements(review):
            order.extend(s.chunk_ids)
        for g in gaps.gaps:
            order.extend(g.chunk_ids)
        refs = []
        for n, cid in enumerate(dict.fromkeys(order), start=1):
            ch = self.corpus.chunk(cid)
            if ch:
                refs.append({"ref": n, "chunk_id": cid, "paper_id": ch["paper_id"], "title": ch["title"],
                             "filename": ch["filename"], "page": ch["page"], "snippet": ch["text"][:260]})
        return refs


def _ms(t0: float) -> int:
    return int((time.time() - t0) * 1000)


def _short(exc: Exception) -> str:
    return str(exc)[:220]
