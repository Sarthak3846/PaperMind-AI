# Changelog

Dated record of changes since Milestone 1. Git commit history is the authoritative per-change record; use
`git log --date=short` to list commits with dates. Add a line here every time you commit a meaningful change.

## 2026-11-18 - Milestone 2 build (PaperMind AI 2.0.0)

### Project transition: DebateRAG.ai -> PaperMind AI
* New repository layout: `code/backend`, `code/frontend`, `prompts/`, `test-data/`, `docs/` (Milestone 2 structure).
* Research goal changed from a debate-style Q&A to evidence-grounded literature review (analysis, comparison, gaps, verification).
* Corpus reduced from 10 to **7 papers, all on retrieval-augmented generation**. Three off-topic PDFs (video classification,
  modal logic, InternVL 1.5) and a committed WinRAR installer were removed from `DATASET/`. The old repository was not modified.

### Frontend redesign (same day)
* Rebuilt the UI on the original DebateRAG design language (deep navy, indigo-purple gradients, frosted glass, pill navbar, serif-italic hero accent, terminal log) as a single-page app: Hero, How It Works, Agents, Workspace, Footer.
* Terminal-style live log and a 10-stage progress tracker, both driven only by events streamed from `/api/research/stream`.
* Hero, navbar and workspace badges read live data from `/api/health` and `/api/papers`; the original's hard-coded confidence score, agent count, sample chart and timer-based fake logs were removed.
* Responsive layout, loading skeletons, backend-offline and error states, reduced-motion support.
* Backend and API contracts unchanged.

### Added
* Structured individual paper analysis (P3), cross-paper comparison (P4), research-gap identification (P6),
  citation verification (P8), evidence critic (P5), query understanding (P1), evidence extraction (P2), literature review (P7).
* Root Agent orchestration with real execution events, streamed over Server-Sent Events (`/api/research/stream`).
* Pydantic schemas for every model output; retry, JSON repair and error propagation in `app/llm.py`.
* Prompt library `prompts/v1`, `v2`, `v3`, `final` (8 prompts each) and `prompts/ITERATION_LOG.md`.
* Evaluation harness `test-data/run_eval.py`, 15 test cases, results template; 48 automated pytest tests.
* React research workspace: question input, paper selection, live agent log, per-paper analysis, comparison table,
  research gaps, literature review with per-claim verification badges, source passages and Markdown export.

### Changed
* Preprocessing: pypdfium2 text extraction per page (pypdf fallback), page numbers kept, portable relative paths,
  citation markers kept, bibliography chunks flagged, running headers removed; chunk IDs `paper_id:pPAGE:cINDEX`.
* Fixed: the RAG survey `2410.12837v1.pdf` produced **zero** chunks under the old coordinate filter and was silently missing from the index.
* Retrieval: real tokenisation, relevance gating (out-of-corpus questions return nothing), paper filter, boost for papers named in the question.
* Gemini integration moved from the legacy `google-generativeai` SDK to `google-genai`; model name is configurable (`GEMINI_MODEL`)
  because `gemini-2.5-flash` is scheduled for re-routing on 2026-12-01 (verify on Google's changelog).

### Fixed
* Agents no longer share a global chat history across requests and users.
* Failed model calls are no longer returned as text and passed to the next agent as evidence.
* Frontend no longer shows simulated agent logs, fixed confidence numbers or "Verified/Self-RAG" badges.

### Removed
* Landing-page marketing content that claimed features that were not implemented.
* `Agents/main.py` CLI that imported a module which did not exist.
