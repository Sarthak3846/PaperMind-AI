"""PaperMind AI - FastAPI application.

Endpoints
  GET  /api/health           status, model, prompt version, corpus size
  GET  /api/papers           the papers that can be searched
  POST /api/research         run the whole pipeline, return the final result (JSON)
  POST /api/research/stream  same pipeline, streamed as Server-Sent Events (real stage events)
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from agents.root_agent import RootAgent
from app.config import get_settings
from app.llm import GeminiBackend, LLMBackend, LLMNotConfigured, LLMService
from app.prompts import PromptError, get_library
from app.schemas import ResearchRequest
from retrieval.index import Corpus, get_corpus

settings = get_settings()
app = FastAPI(title="PaperMind AI", version="2.0.0",
              description="Multi-agent RAG for research intelligence")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins) or ["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ dependencies (overridable in tests)
@lru_cache(maxsize=1)
def _backend_singleton() -> LLMBackend:
    return GeminiBackend(get_settings())


def get_backend() -> LLMBackend:
    try:
        return _backend_singleton()
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def get_corpus_dep() -> Corpus:
    return get_corpus()


def _make_root(backend: LLMBackend, corpus: Corpus) -> RootAgent:
    s = get_settings()
    try:
        prompts = get_library(s.prompt_version)
    except PromptError as exc:
        raise HTTPException(status_code=500, detail=f"Prompt configuration error: {exc}")
    return RootAgent(LLMService(backend, s), corpus, prompts, s)  # fresh stats + no shared chat state per request


def _validated(req: ResearchRequest, corpus: Corpus) -> ResearchRequest:
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="The research question must not be empty.")
    if req.paper_ids is not None:
        if not req.paper_ids:
            raise HTTPException(status_code=422, detail="paper_ids must contain at least one id, or be omitted to search all papers.")
        unknown = [p for p in req.paper_ids if corpus.paper(p) is None]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown paper id(s): {', '.join(unknown)}")
    return req


# ------------------------------------------------------------------ routes
@app.get("/api/health")
def health(corpus: Corpus = Depends(get_corpus_dep)):
    s = get_settings()
    return {"status": "ok", "model": s.gemini_model, "prompt_version": s.prompt_version,
            "gemini_configured": bool(s.gemini_api_key), "papers": len(corpus.papers), "chunks": len(corpus.chunks)}


@app.get("/api/papers")
def papers(corpus: Corpus = Depends(get_corpus_dep)):
    return {"papers": [{k: p.get(k) for k in ("paper_id", "title", "authors", "year", "url", "filename", "pages", "chunks")}
                       for p in corpus.papers.values()]}


@app.post("/api/research")
def research(req: ResearchRequest, backend: LLMBackend = Depends(get_backend), corpus: Corpus = Depends(get_corpus_dep)):
    req = _validated(req, corpus)
    root = _make_root(backend, corpus)
    return root.run_to_result(req.question, req.paper_ids, req.max_papers)


@app.post("/api/research/stream")
def research_stream(req: ResearchRequest, backend: LLMBackend = Depends(get_backend), corpus: Corpus = Depends(get_corpus_dep)):
    req = _validated(req, corpus)
    root = _make_root(backend, corpus)

    def gen() -> Iterator[str]:
        try:
            for ev in root.run(req.question, req.paper_ids, req.max_papers):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as exc:  # last-resort guard: always end the stream with a clear event
            err = {"seq": -1, "type": "stage_error", "stage": "internal", "agent": "RootAgent", "prompt": None,
                   "message": f"Unexpected server error: {type(exc).__name__}", "data": {}, "duration_ms": None}
            yield f"data: {json.dumps(err)}\n\n"
            final = {"seq": -1, "type": "result", "stage": "complete", "agent": "RootAgent", "prompt": None,
                     "message": "Unexpected server error", "data": {"result": {"status": "failed", "message": "Unexpected server error",
                     "error": {"stage": "internal", "message": type(exc).__name__}}}, "duration_ms": None}
            yield f"data: {json.dumps(final)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
