import json

import pytest
from fastapi.testclient import TestClient

from app import main
from tests.fakes import FakeBackend


@pytest.fixture()
def client():
    main.app.dependency_overrides[main.get_backend] = lambda: FakeBackend()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_health_and_papers(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["papers"] == 7 and h["chunks"] > 500
    p = client.get("/api/papers").json()["papers"]
    assert len(p) == 7 and all(x["paper_id"] and x["title"] and x["pages"] for x in p)


def test_empty_question_is_422(client):
    for body in ({"question": ""}, {"question": "   "}, {}):
        assert client.post("/api/research", json=body).status_code == 422
        assert client.post("/api/research/stream", json=body).status_code == 422


def test_too_long_question_is_422(client):
    assert client.post("/api/research", json={"question": "a" * 1001}).status_code == 422


def test_unknown_or_empty_paper_selection(client):
    assert client.post("/api/research", json={"question": "retrieval", "paper_ids": ["nope"]}).status_code == 400
    assert client.post("/api/research", json={"question": "retrieval", "paper_ids": []}).status_code == 422


def test_blocking_endpoint_returns_result(client):
    r = client.post("/api/research", json={"question": "Compare REALM and retrieval-augmented generation retrieval", "max_papers": 3})
    assert r.status_code == 200 and r.json()["status"] == "completed"


def test_stream_emits_ordered_events_and_final_result(client):
    with client.stream("POST", "/api/research/stream", json={"question": "Compare REALM and retrieval-augmented generation retrieval"}) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        events = [json.loads(l[6:]) for l in r.iter_lines() if l.startswith("data: ")]
    assert events[0]["stage"] == "validate_input" and events[-1]["type"] == "result"
    assert events[-1]["data"]["result"]["status"] == "completed"
    assert any(e["type"] == "stage_start" and e["prompt"] == "P3" for e in events)


def test_missing_api_key_gives_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: None)
    main._backend_singleton.cache_clear()
    main.app.dependency_overrides.clear()
    c = TestClient(main.app)
    r = c.post("/api/research", json={"question": "retrieval augmented generation"})
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]
