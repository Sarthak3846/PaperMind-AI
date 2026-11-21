"""Fault-injection tests: every agent must reject fabricated or unsupported model output."""
import json

import pytest

from agents.common import AgentError
from agents.comparison_agent import ComparisonAgent
from agents.gap_agent import ResearchGapAgent
from agents.paper_analyst import PaperAnalystAgent
from agents.reader_agent import ReaderAgent
from agents.teacher_agent import TeacherAgent, all_statements
from agents.verifier import CitationVerifier, VItem
from app.llm import BackendError, LLMError
from app.schemas import Comparison, GapsResult, PaperAnalysis, Claim
from tests.fakes import FakeBackend


def chunks_of(corpus, pid, n=4):
    return corpus.paper_context(pid, ["retrieval", "generation"], n_query=n)


def test_reader_rejects_fabricated_id_and_fake_quote(corpus, prompts, make_service):
    ch = chunks_of(corpus, "realm2020")
    real = ch[0]
    def p2(system, user):
        return json.dumps({"evidence": [
            {"chunk_id": real["chunk_id"], "quote": " ".join(real["text"].split()[:20]), "claim": "ok", "kind": "fact"},
            {"chunk_id": "realm2020:p99:c9", "quote": "Totally fabricated source reference text", "claim": "bad id", "kind": "fact"},
            {"chunk_id": real["chunk_id"], "quote": "This sentence was invented by the language model itself", "claim": "bad quote", "kind": "fact"}]})
    _, svc = make_service(FakeBackend({"P2": p2}))
    kept, rejected = ReaderAgent(svc, prompts, corpus).run("q", ch)
    assert [e.evidence_id for e in kept] == ["E1"]
    assert {r["reason"] for r in rejected} == {"unknown_chunk_id", "quote_not_found_in_chunk"}


def test_analyst_drops_hallucinated_ids_and_numbers(corpus, prompts, make_service):
    ch = chunks_of(corpus, "realm2020")
    ok = ch[0]["chunk_id"]
    def p3(system, user):
        return json.dumps({"research_problem": {"text": "real", "chunk_ids": [ok]},
            "findings": [{"text": "invented", "chunk_ids": ["realm2020:p77:c1"]}, {"text": "no ids", "chunk_ids": []}],
            "quantitative_results": [{"metric": "EM", "value": "99.987", "chunk_ids": [ok]}]})
    _, svc = make_service(FakeBackend({"P3": p3}))
    a = PaperAnalystAgent(svc, prompts, corpus).run("q", corpus.paper("realm2020"), ch)
    assert a.research_problem and a.findings == [] and a.quantitative_results == []
    assert a.rejected_claims == 3 and "findings" in a.missing_fields


def test_analyst_with_nothing_verifiable_raises(corpus, prompts, make_service):
    ch = chunks_of(corpus, "realm2020")
    _, svc = make_service(FakeBackend({"P3": lambda s, u: json.dumps({"findings": [{"text": "x", "chunk_ids": ["nope"]}]})}))
    with pytest.raises(ValueError):
        PaperAnalystAgent(svc, prompts, corpus).run("q", corpus.paper("realm2020"), ch)


def _analyses(corpus):
    out = []
    for pid in ("realm2020", "selfrag2023"):
        ch = chunks_of(corpus, pid)
        out.append(PaperAnalysis(paper_id=pid, title=corpus.paper(pid)["title"], filename=corpus.paper(pid)["filename"],
                                 research_problem=Claim(text="p", chunk_ids=[ch[0]["chunk_id"]]),
                                 methodology=[Claim(text="m", chunk_ids=[ch[1]["chunk_id"]])]))
    return out


def test_comparison_needs_two_papers(corpus, prompts, make_service):
    backend, svc = make_service()
    c = ComparisonAgent(svc, prompts, corpus).run("q", _analyses(corpus)[:1])
    assert c.skipped and backend.calls == []


def test_comparison_removes_uncited_items(corpus, prompts, make_service):
    an = _analyses(corpus)
    good = an[0].research_problem.chunk_ids[0]
    def p4(system, user):
        return json.dumps({"comparable": True, "similarities": [
            {"text": "fabricated cite", "paper_ids": ["realm2020"], "chunk_ids": ["x:p1:c1"]},
            {"text": "fine", "paper_ids": ["realm2020"], "chunk_ids": [good]}],
            "contradictions": [{"topic": "t", "positions": [{"paper_id": "realm2020", "statement": "s", "chunk_ids": [good]}]}]})
    _, svc = make_service(FakeBackend({"P4": p4}))
    c = ComparisonAgent(svc, prompts, corpus).run("q", an)
    assert len(c.similarities) == 1 and c.contradictions == [] and c.rejected_items == 2


def test_gap_agent_flags_global_novelty_and_downgrades(corpus, prompts, make_service):
    an = _analyses(corpus)
    def p6(system, user):
        return json.dumps({"gaps": [
            {"title": "Nobody has studied X", "description": "There is no prior work on this topic.", "why_it_exists": "w",
             "basis": "explicit", "supporting_paper_ids": ["realm2020"], "chunk_ids": ["fake:p1:c1"]},
            {"title": "No paper support", "description": "d", "why_it_exists": "w", "basis": "inferred", "supporting_paper_ids": [], "chunk_ids": []}]})
    _, svc = make_service(FakeBackend({"P6": p6}))
    g = ResearchGapAgent(svc, prompts, corpus).run("q", an, Comparison(skipped=True, skip_reason="x"))
    assert len(g.gaps) == 1 and g.rejected_items == 1
    gap = g.gaps[0]
    assert gap.global_claim_flag and gap.basis == "inferred" and "Downgraded" in gap.note
    assert "novelty" in g.scope_disclaimer


def test_teacher_strips_fabricated_citations(corpus, prompts, make_service):
    an = _analyses(corpus)
    good = an[0].research_problem.chunk_ids[0]
    def p7(system, user):
        return json.dumps({"research_overview": [{"text": "A", "chunk_ids": [good, "ghost:p1:c1"]}, {"text": "B", "chunk_ids": ["ghost:p1:c1"]}],
                           "paper_summaries": [{"paper_id": "not_analysed", "statements": [{"text": "C", "chunk_ids": [good]}]}]})
    _, svc = make_service(FakeBackend({"P7": p7}))
    r = TeacherAgent(svc, prompts, corpus).run("q", an, Comparison(skipped=True), GapsResult(), [])
    s = r.research_overview
    assert s[0].chunk_ids == [good] and s[0].invalid_chunk_ids == ["ghost:p1:c1"]
    assert s[1].chunk_ids == [] and s[1].invalid_chunk_ids == ["ghost:p1:c1"]
    assert r.paper_summaries == []


def test_teacher_empty_review_raises(corpus, prompts, make_service):
    _, svc = make_service(FakeBackend({"P7": lambda s, u: "{}"}))
    with pytest.raises(AgentError):
        TeacherAgent(svc, prompts, corpus).run("q", _analyses(corpus), Comparison(skipped=True), GapsResult(), [])


def test_verifier_code_checks_do_not_call_llm(corpus, prompts, make_service):
    backend, svc = make_service()
    res = CitationVerifier(svc, prompts, corpus).run([
        VItem("S1", "claim without citation", []),
        VItem("S2", "claim with fake citation", [], invalid_chunk_ids=["ghost:p1:c1"])])
    assert res["S1"].status == "unsupported" and "No source" in res["S1"].reason
    assert res["S2"].status == "unsupported" and "Fabricated reference" in res["S2"].reason
    assert backend.calls == []


def test_verifier_numeric_downgrade_and_failure_is_unverified(corpus, prompts, make_service):
    cid = "realm2020:p1:c0"
    _, svc = make_service()
    res = CitationVerifier(svc, prompts, corpus).run([VItem("S1", "The model gains 97.31 points.", [cid])])
    assert res["S1"].status == "partially_supported" and "97.31" in res["S1"].reason

    def boom(system, user):
        raise BackendError("down", 500)
    _, svc2 = make_service(FakeBackend({"P8": boom}))
    svc2.settings = svc2.settings
    res2 = CitationVerifier(svc2, prompts, corpus).run([VItem("S1", "claim", [cid])])
    assert res2["S1"].status == "unverified"
