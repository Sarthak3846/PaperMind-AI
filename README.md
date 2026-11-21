# PaperMind AI - Multi-Agent RAG for Research Intelligence

Team **Cognition Labs** · Prompt Engineering (SCSE4041) mini project · Bennett University

PaperMind AI helps a researcher analyse academic papers, compare findings across studies, find research gaps and
produce an **evidence-grounded literature review in which every claim is traceable to a paper, page and passage
and carries a verification status**. It grew out of our earlier DebateRAG.ai project and is a new codebase.

> **Answers come only from the PDFs in `DATASET/` (7 papers on retrieval-augmented generation).**
> The system reads *retrieved passages*, not whole papers, and its output must be checked against the sources before use.

---

## 1. What works (and what does not)

| Feature | Status | How it is verified |
|---|---|---|
| Page-aware PDF ingestion, portable paths, corrupt / scanned / duplicate PDF handling | Working | `pytest` (real PDFs + generated bad PDFs) |
| BM25 retrieval with relevance gating, paper filter, named-paper boost | Working | `pytest` on the real corpus |
| P1 Query understanding, P2 Evidence extraction, P5 Critic | Working* | pipeline tests with a scripted model; **live Gemini runs are yours to execute** |
| P3 Structured per-paper analysis (validated JSON, missing fields reported) | Working* | same |
| P4 Cross-paper comparison (tables, contradictions, incompatibility handling) | Working* | same |
| P6 Research gaps (explicit vs inferred, scope disclaimer) | Working* | same |
| P7 Literature review + references with page numbers | Working* | same |
| P8 Citation verification (code checks + LLM verdict per claim) | Working* | fault-injection tests |
| Real-time execution events (SSE) in the UI: terminal log + 10-stage tracker | Working | 29 browser checks (Playwright) against a live server |
| Redesigned responsive frontend (hero, pipeline, agents, workspace, result tabs, Markdown export) | Working | lint + build + browser checks incl. mobile and backend-offline states |
| Error handling (API failures, invalid JSON, empty / over-long query, unknown paper, no evidence) | Working | 48 `pytest` tests |
| PDF **upload** by the user | **Not implemented** | add PDFs to `DATASET/` and re-run ingestion instead |
| OCR for scanned PDFs | **Not implemented** | such PDFs are skipped and reported |
| Dense / semantic retrieval | **Not implemented** | BM25 only |

\* "Working" means the code path is implemented and tested end to end with a scripted stand-in for Gemini.
**No real Gemini output was produced while building this** (no API key was available). Run the evaluation below with
your key before you claim anything about answer quality, and put only those real results in your Milestone 2 table.

## 2. Architecture in one picture

```
Question ──> [1 validate] ──> [P1 Search Agent] ──> [BM25 retrieval] ──> [P2 Reader] ──> code check: id + quote in source
                                                                                     │
        ┌────────────────────────────────────────────────────────────────────────────┘
        └─> [P5 Critic] ─> [P3 Paper Analyst × N papers] ─> [P4 Comparison] ─> [P6 Research Gaps]
                                                                    └──────────────┬────────────┘
                                                              [P7 Teacher: literature review] ─> [P8 Citation Verifier] ─> result
```

The **Root Agent** (plain Python, no LLM call) runs these stages, emits a real event for each, and stops or skips a stage
when it fails; a failed stage's error text is never handed to the next agent. Full diagrams: `docs/architecture.md`.

**Agents:** Search (P1) · Reader (P2) · Critic (P5) · Paper Analyst (P3) · Comparison (P4) · Research Gap (P6) · Teacher (P7) · Citation Verifier (P8) · Root.
**8 final prompts**, 10 pipeline stages, roughly 8-16 model calls per run (P3 runs once per analysed paper, P8 once per 6 claims).

## 3. Dataset

`DATASET/` holds 7 PDFs (metadata in `code/backend/data/papers_manifest.json`):

| paper_id | Paper |
|---|---|
| `rag_lewis2020` | Lewis et al. 2020, Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks |
| `realm2020` | Guu et al. 2020, REALM |
| `selfrag2023` | Asai et al. 2023, Self-RAG |
| `rag_survey_gao2023` | Gao et al., RAG for LLMs: A Survey |
| `rag_survey_gupta2024` | Gupta et al., A Comprehensive Survey of RAG |
| `globalrag2025` | Luo et al., Towards Global RAG (benchmark) |
| `rag_ssrn` | RAG: The Revolution of Retrieval-Augmented Text Generation (SSRN 5252835; authors and year not recorded in the manifest) |

Ingestion produces 714 chunks (about 900 characters, never crossing a page). Chunk ID format: `paper_id:pPAGE:cINDEX`, e.g. `selfrag2023:p3:c1`.
Reference-list chunks are flagged and excluded from search (detection is heuristic; Self-RAG's bibliography is only partly caught).

**Adding papers:** copy PDFs into `DATASET/`, optionally add an entry to `papers_manifest.json` (title, authors, year), then
`cd code/backend && python -m retrieval.preprocessing` and restart the backend. Unlisted PDFs are indexed with a guessed title and a warning.
Check `code/backend/data/processed/ingest_report.json` for skipped files (corrupt, text-empty, duplicates).

## 4. Install and run (about 10 minutes)

Requirements: **Python 3.10+**, **Node.js 18+**, a free Gemini API key from https://aistudio.google.com/apikey

### Backend

Windows PowerShell:
```powershell
cd code\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then open .env and paste your GEMINI_API_KEY
python scripts\check_gemini.py  # confirms the key and model work
uvicorn app.main:app --reload --port 8000
```
macOS / Linux:
```bash
cd code/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env and add GEMINI_API_KEY
python scripts/check_gemini.py
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs for the interactive API, http://localhost:8000/api/health for status.
If PowerShell blocks the activate script: `Set-ExecutionPolicy -Scope Process Bypass`.

### Frontend (second terminal)
```bash
cd code/frontend
npm install
npm run dev
```
Open http://localhost:5173. To point at another backend, copy `.env.example` to `.env` and set `VITE_API_BASE`.

### One-command launchers (optional)
After the one-time setup above (venv + `pip install`, `npm install`, `.env`), these start each side:

| | Windows | macOS / Linux |
|---|---|---|
| Backend | `scripts\start_backend.bat` | `bash scripts/start_backend.sh` |
| Frontend | `scripts\start_frontend.bat` | `bash scripts/start_frontend.sh` |

### See the demo
1. Open http://localhost:5173. The navbar shows **Backend online** and the hero shows `7 papers · 714 passages indexed`
   (both read live from `/api/health`). A red "GEMINI_API_KEY not set" pill in the workspace means `.env` is missing the key.
2. Scroll to **Interactive Research Workspace** (or press *Open Workspace*). Click an example question, or tick REALM and Lewis et al. in
   **Paper selection** and ask *"Compare how REALM and the original RAG paper integrate retrieval"*.
3. Press **Run research pipeline**. The stage tracker and the terminal-style log fill in from events streamed by the server as each agent runs
   (1-2 minutes). **Stop** cancels the run.
4. Explore the result tabs: Literature review (verification bar and badges; click a citation chip to read the exact source passage),
   Paper analysis, Comparison, Research gaps, Evidence & retrieval. **Markdown** exports the review.
5. Try an out-of-corpus question (*"How do I bake sourdough bread?"*): the run stops with "insufficient evidence" and writes no answer.

## 5. Environment variables (`code/backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | (required) | Google AI Studio key. Never commit it. `GOOGLE_API_KEY` also works. |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Model for all calls. Check Google's changelog: `gemini-2.5-flash` is scheduled for re-routing on 1 Dec 2026. State the exact model in form Q9. |
| `GEMINI_FALLBACK_MODEL` | empty | Tried once if the main model returns 404 (retired). |
| `PROMPT_VERSION` | `final` | `v1`, `v2`, `v3` or `final` (folder under `/prompts`). |
| `CORS_ORIGINS` | localhost:5173 | Comma-separated browser origins allowed to call the API (add your Vercel URL). |
| `PAPERMIND_DATASET_DIR` | `DATASET/` | Override the PDF folder. |
| `LLM_MAX_RETRIES` / `MAX_PAPERS_PER_QUERY` | 3 / 4 | Retry count for 429/5xx; default papers analysed per run. |

Frontend: `VITE_API_BASE` (default `http://localhost:8000`).

## 6. API

| Method and path | Description |
|---|---|
| `GET /api/health` | status, model, prompt version, key configured?, corpus size |
| `GET /api/papers` | searchable papers with id, title, authors, year, pages, chunks |
| `POST /api/research` | run the pipeline, return the final JSON result |
| `POST /api/research/stream` | same, as Server-Sent Events: one `data: {json}` per event, last event `type: "result"` |

Request body: `{"question": "...", "paper_ids": ["realm2020", "rag_lewis2020"], "max_papers": 4}`
(`paper_ids` optional = search all; `max_papers` 1-6).
Errors: `422` empty / over-long question or empty `paper_ids`; `400` unknown paper id; `503` API key not configured.
Pipeline outcomes are in `status`: `completed`, `insufficient_evidence`, or `failed` (with `error.stage`).
Event fields: `seq, ts, type (stage_start|stage_progress|stage_done|stage_warning|stage_error|result), stage, agent, prompt, message, data, duration_ms`.
The result contains `query_understanding, retrieval, evidence, rejected_evidence, critic, paper_analyses, comparison, gaps, review, references, sources, verification, warnings, metrics`.

## 7. Tests and evaluation

**Automated safeguards (no API key needed):**
```bash
cd code/backend
pip install -r requirements-dev.txt
python -m pytest -q            # 48 tests
```
These use a scripted fake model plus the real corpus and cover: invalid JSON and repair, API outages and retries, fabricated chunk IDs,
quotes not in the source, hallucinated numbers, missing citations, global-novelty wording in gaps, single-paper comparison, empty / over-long
queries, out-of-corpus queries, and that failures never reach later agents. They are **not** evidence about Gemini's answer quality.

**Real evaluation against Gemini (this produces your Milestone 2 test table):**
```bash
python test-data/run_eval.py                         # 15 cases, prompt set "final"  -> test-data/results/final/
python test-data/run_eval.py --prompt-version v1     # repeat for v2, v3
python test-data/run_eval.py --compare               # metrics table across prompt versions
```
Each case's full output is saved as JSON, with `summary.md` in the exact Milestone 2 table format. Pass/Fail is computed from checks in
`test-data/inputs/test_cases.json`; failures are expected and fine to report. Fill `prompts/ITERATION_LOG.md` from the real numbers.

## 8. Repository layout

```
README.md  CHANGELOG.md  LICENSE  render.yaml
DATASET/                     7 PDFs
prompts/                     v1/ v2/ v3/ final/ (P1-P8 each) + ITERATION_LOG.md
code/backend/                FastAPI app  (app/, agents/, retrieval/, data/, tests/, scripts/)
code/frontend/               React + Vite + Tailwind app (src/components/*, src/api.js = backend client)
scripts/                     start_backend / start_frontend launchers (.bat and .sh)
test-data/                   inputs/test_cases.json, run_eval.py, results/, results_template.md
docs/                        architecture.md (Mermaid diagrams), prompt_sheets.md (generated)
```

## 9. Deployment

* **Backend (Render):** New > Blueprint from this repo (`render.yaml`), then add `GEMINI_API_KEY` in the dashboard and set `CORS_ORIGINS` to your Vercel URL.
  Free instances sleep when idle, so the first request can take about a minute.
* **Frontend (Vercel):** import the repo, set **Root Directory** to `code/frontend`, add `VITE_API_BASE` = your Render URL.
* Test both links in a private window before submitting. The old DebateRAG deployment (`debaterag-ai.onrender.com`) is no longer used by this code.

## 10. Current limitations

* Analyses are built from the ~8-12 most relevant passages per paper, not the full text; fields not covered by those passages are reported as "not reported".
* Corpus is only 7 RAG papers; "research gaps" describe these papers, not the literature (the UI and API say so).
* BM25 matches words, not meaning; questions phrased very differently from the papers can miss relevant passages. Borderline off-topic questions can still retrieve incidental matches and are then stopped by the evidence/critic stages.
* The verifier is itself an LLM; "supported" is a strong signal, not a guarantee. Always read the cited passage.
* A run takes 1-2 minutes and roughly 8-16 model calls; free-tier rate limits can slow or interrupt it (the UI then shows the failing stage).
* No user accounts, no storage of past runs, no PDF upload, no OCR.
* Scores like "supported ratio" depend on the model and are not comparable across models.

## 11. Responsible use and acknowledgements

* Outputs are drafts that need human verification; flagged claims are displayed, not hidden.
* Papers belong to their authors and are included for coursework analysis; check each licence before redistributing the repository publicly.
* Models/tools: Google Gemini API (google-genai SDK), FastAPI, Pydantic, rank-bm25, pypdfium2 / pypdf, React, Vite, Tailwind CSS, lucide-react.
* **AI-assisted development:** the code, prompts, tests and documentation of this milestone were drafted with the help of an AI assistant (Claude) and then run, reviewed and owned by the team.
  Disclose this as your course requires, and make sure each member can explain the part they claim.

## 12. Milestone 2 submission map

| Required item | Where it is |
|---|---|
| Repository structure (README, prompts/v1 v2 v3 final, code/, test-data/, docs/, CHANGELOG) | this repo |
| Prompt sheets (text, per final prompt) | `docs/prompt_sheets.md` (add one real sample run each) |
| Prompt iteration log (>= 3 versions, observed results) | `prompts/ITERATION_LOG.md` (**you must fill the results**) |
| Test table (>= 10 inputs, >= 3 edge cases) | `test-data/inputs/test_cases.json` -> `results/final/summary.md` (**run it**) |
| Diagrams | `docs/architecture.md` |
| Counts for the form | final prompts **8** · test inputs **15** · prompt versions **3** (must match your PDF) |
| Still to do by hand | Milestone 2 PDF (7 sections), supporting document, reel (90-150 s), 2-3 screenshots of real runs, contribution table, deployed prototype link |
