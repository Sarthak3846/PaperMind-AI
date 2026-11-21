import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.llm import LLMService  # noqa: E402
from app.prompts import get_library  # noqa: E402
from retrieval.index import get_corpus  # noqa: E402
from tests.fakes import FakeBackend, noop_sleep  # noqa: E402


@pytest.fixture(scope="session")
def corpus():
    return get_corpus()


@pytest.fixture()
def prompts():
    return get_library("final")


@pytest.fixture()
def make_service():
    def _make(backend=None):
        backend = backend or FakeBackend()
        return backend, LLMService(backend, get_settings(), sleep=noop_sleep)
    return _make
