import json

import pytest

from app.llm import BackendError, InvalidModelOutput, LLMError, LLMService, parse_json_loose
from app.config import get_settings
from app.schemas import QueryUnderstanding
from tests.fakes import FakeBackend, noop_sleep

GOOD = json.dumps({"task_type": "factual", "keywords": ["rag"], "sub_questions": [], "ambiguities": []})


class Scripted:
    def __init__(self, outputs):
        self.outputs, self.n, self.models = list(outputs), 0, []

    def generate(self, *, system, user, temperature, json_mode, model=None):
        self.models.append(model)
        self.n += 1
        o = self.outputs.pop(0)
        if isinstance(o, Exception):
            raise o
        return o


def svc(backend):
    return LLMService(backend, get_settings(), sleep=noop_sleep)


def test_invalid_json_is_repaired_once(prompts):
    b = Scripted(["not json {{", GOOD])
    s = svc(b)
    out = s.call_json(prompts.get("P1"), QueryUnderstanding, question="q")
    assert out.keywords == ["rag"] and s.stats.repairs == 1 and b.n == 2


def test_invalid_twice_raises(prompts):
    s = svc(Scripted(["nope", '{"task_type": "banana", "keywords": []}']))
    with pytest.raises(InvalidModelOutput):
        s.call_json(prompts.get("P1"), QueryUnderstanding, question="q")
    assert s.stats.invalid_after_repair == 1


def test_markdown_fences_are_tolerated():
    assert parse_json_loose("```json\n{\"a\": 1}\n```") == {"a": 1}
    assert parse_json_loose("Sure! {\"a\": 1} done") == {"a": 1}


def test_transient_errors_are_retried(prompts):
    s = svc(Scripted([BackendError("busy", 503), BackendError("rate", 429), GOOD]))
    assert s.call_json(prompts.get("P1"), QueryUnderstanding, question="q").keywords == ["rag"]
    assert s.stats.retries == 2


def test_permanent_error_raises_llm_error(prompts):
    s = svc(Scripted([BackendError("bad key", 401)]))
    with pytest.raises(LLMError):
        s.call_json(prompts.get("P1"), QueryUnderstanding, question="q")
    assert s.stats.failures == 1


def test_retries_exhausted(prompts):
    s = svc(Scripted([BackendError("down", 503)] * 10))
    with pytest.raises(LLMError):
        s.call_json(prompts.get("P1"), QueryUnderstanding, question="q")


def test_fallback_model_on_404(prompts, monkeypatch):
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "fallback-model")
    b = Scripted([BackendError("model not found", 404), GOOD])
    s = LLMService(b, get_settings(), sleep=noop_sleep)
    s.call_json(prompts.get("P1"), QueryUnderstanding, question="q")
    assert b.models == [None, "fallback-model"]
