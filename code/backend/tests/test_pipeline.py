"""End-to-end pipeline tests (fake model, real corpus, real retrieval, real validators)."""
import json

from agents.root_agent import RootAgent
from app.config import get_settings
from app.llm import BackendError
from tests.fakes import FakeBackend

Q = "Compare how REALM and retrieval-augmented generation integrate retrieval into language models"


def run(corpus, prompts, make_service, backend=None, question=Q, paper_ids=None, max_papers=3):
    backend, svc = make_service(backend)
    root = RootAgent(svc, corpus, prompts, get_settings())
    events = list(root.run(question, paper_ids, max_papers))
    return backend, events, events[-1]["data"]["result"]


def test_happy_path_completes_with_real_events(corpus, prompts, make_service):
    backend, events, res = run(corpus, prompts, make_service)
    assert res["status"] == "completed", res.get("message")
    stages = [e["stage"] for e in events if e["type"] == "stage_done"]
    assert stages[:4] == ["validate_input", "query_understanding", "retrieval", "evidence_extraction"]
    assert "citation_verification" in stages and events[-1]["type"] == "result"
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert len(res["paper_analyses"]) >= 2 and not res["comparison"]["skipped"]
    assert res["gaps"]["gaps"] and "novelty" in res["gaps"]["scope_disclaimer"]
    v = res["verification"]
    assert v["checked"] > 0 and v["unsupported"] == 0
    assert res["references"] and all(r["page"] >= 1 for r in res["references"])
    assert set(res["sources"]) >= {r["chunk_id"] for r in res["references"]}
    assert set(backend.calls) == {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"}
    assert res["metrics"]["llm_calls"] == len(backend.calls)


def test_out_of_corpus_question_stops_before_any_evidence_call(corpus, prompts, make_service):
    backend, events, res = run(corpus, prompts, make_service, question="How do I bake sourdough bread at home")
    assert res["status"] == "insufficient_evidence"
    assert backend.calls == ["P1"]                          # nothing after retrieval was called
    assert res["paper_analyses"] == [] and res["review"] is None


def test_failed_reader_stops_pipeline_and_passes_nothing_on(corpus, prompts, make_service):
    def boom(system, user):
        raise BackendError("quota exceeded", 401)
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P2": boom}))
    assert res["status"] == "failed" and res["error"]["stage"] == "evidence_extraction"
    assert "P3" not in backend.calls and "P7" not in backend.calls
    assert res["review"] is None and res["evidence"] == []
    assert any(e["type"] == "stage_error" for e in events)


def test_invalid_json_from_model_is_reported_not_passed_on(corpus, prompts, make_service):
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P2": lambda s, u: "I think the answer is 42"}))
    assert res["status"] == "failed" and "invalid output" in res["error"]["message"]
    assert res["metrics"]["invalid_after_repair"] == 1 and "P5" not in backend.calls


def test_query_understanding_failure_falls_back_with_warning(corpus, prompts, make_service):
    def boom(system, user):
        raise BackendError("overloaded", 503)
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P1": boom}))
    assert res["status"] == "completed"
    assert any("Falling back" in w for w in res["warnings"])
    assert any(e["type"] == "stage_warning" and e["stage"] == "query_understanding" for e in events)


def test_critic_rejecting_everything_gives_insufficient_evidence(corpus, prompts, make_service):
    def reject_all(system, user):
        ev = json.loads(user.split("Evidence items (JSON):\n")[-1])
        return json.dumps({"validated_ids": [], "flagged": [{"evidence_id": e["evidence_id"], "reason": "off-topic"} for e in ev],
                           "missing_information": ["nothing relevant"]})
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P5": reject_all}))
    assert res["status"] == "insufficient_evidence" and "P3" not in backend.calls


def test_single_paper_skips_comparison(corpus, prompts, make_service):
    backend, events, res = run(corpus, prompts, make_service, question="What does REALM do with retrieval", paper_ids=["realm2020"])
    assert res["status"] == "completed" and res["comparison"]["skipped"] and "P4" not in backend.calls
    assert any("at least two" in w for w in res["warnings"])


def test_fabricated_review_citation_is_flagged_unsupported(corpus, prompts, make_service):
    def p7(system, user):
        return json.dumps({"research_overview": [{"text": "Invented claim.", "chunk_ids": ["ghost:p9:c9"]}],
                           "conclusion": [{"text": "Scope note.", "chunk_ids": [], "meta": True}]})
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P7": p7}))
    st = res["review"]["research_overview"][0]
    assert st["status"] == "unsupported" and "Fabricated" in st["status_reason"]
    assert res["review"]["conclusion"][0]["status"] is None          # meta statements are not claims
    assert res["verification"]["unsupported"] == 1 and any("unsupported" in w for w in res["warnings"])


def test_verifier_outage_marks_unverified_not_verified(corpus, prompts, make_service):
    def boom(system, user):
        raise BackendError("down", 503)
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P8": boom}))
    assert res["status"] == "completed"
    assert res["verification"]["supported"] == 0 and res["verification"]["unverified"] > 0


def test_gap_and_comparison_failures_do_not_kill_the_review(corpus, prompts, make_service):
    def boom(system, user):
        raise BackendError("bad", 400)
    backend, events, res = run(corpus, prompts, make_service, FakeBackend({"P4": boom, "P6": boom}))
    assert res["status"] == "completed" and res["comparison"]["skipped"] and res["gaps"]["gaps"] == []
    assert len(res["warnings"]) >= 2


def test_invalid_requests_are_rejected(corpus, prompts, make_service):
    for q, ids in [("", None), ("   ", None), ("x" * 1001, None), ("ok question here", []), ("ok question here", ["nope"])]:
        backend, events, res = run(corpus, prompts, make_service, question=q, paper_ids=ids)
        assert res["status"] == "failed" and res["error"]["stage"] == "validate_input" and backend.calls == []
