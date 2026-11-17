# PaperMind AI 
**A Multi-Agent Research Assistant using Retrieval-Augmented Generation (RAG)**

PaperMind AI is a multi-agent research assistant that explores how **explicit multi-agent coordination** can improve reasoning over academic literature. Instead of relying on a single, monolithic RAG pipeline, the system decomposes retrieval, verification, critique, and synthesis into clearly defined agent roles.

The goal of this project is not to “know everything,” but to reason **accurately, transparently, and inspectably** over a bounded corpus of research papers.

---

## Motivation

Traditional RAG pipelines typically follow a fixed retrieve-then-generate pattern. While effective for simple queries, this approach can break down for complex, multi-faceted research questions where evidence must be compared, validated, and synthesized carefully.

This project is inspired by the **MA-RAG** paper, which proposes using multiple agents with specialized responsibilities to coordinate retrieval and reasoning. 	PaperMind AI implements this idea end-to-end in a practical research assistant setting.

---

## What PaperMind AI Does

- Answers research questions over a **curated academic corpus**
- Enforces **evidence-first reasoning**
- Makes intermediate agent decisions **fully observable**
- Separates retrieval, extraction, critique, and synthesis into explicit stages
- Avoids hallucination by design rather than post-hoc filtering

---

## System Overview

	PaperMind AI operates as a bounded research assistant over a fixed set of papers.

### High-level workflow

1. A user submits a research query
2. The query is decomposed and routed through specialized agents
3. Relevant evidence is retrieved from the corpus
4. Extracted facts are validated and critiqued
5. A final, grounded answer is synthesized

All intermediate steps are logged and exposed to the user.

---

## Agent Architecture

The system uses multiple role-specialized agents, each with a single responsibility:

- **Search Agent**  
  Reformulates user queries into optimized keyword representations for retrieval.

- **Reader Agent**  
  Processes retrieved text and extracts verifiable facts, definitions, and metrics without interpretation.

- **Critic Agent**  
  Evaluates extracted information for completeness, redundancy, contradictions, and relevance before generation.

- **Teacher Agent**  
  Synthesizes a structured, high-density response strictly grounded in validated evidence.

- **Root Agent**  
  Orchestrates the full pipeline and controls how information flows between agents.

This explicit separation of concerns makes the system easier to debug, reason about, and extend.

---

## Retrieval Layer

- **Sparse retrieval:** BM25  
- **Corpus:** Chunked academic papers stored in a structured JSON format  
- **Design choice:** Sparse retrieval was chosen initially for transparency and debuggability

Dense retrieval (e.g., FAISS + embeddings) is planned as a future extension.

---

## Observability

One of the core design goals of PaperMind AI is **interpretability**.

The system exposes:
- Agent-by-agent execution logs
- Retrieval steps and evidence selection
- Critic validation before final synthesis

Nothing happens behind a single opaque generation call.

---

## Tech Stack

**Backend**
- Python
- FastAPI
- BM25 (rank-bm25)
- Gemini API (LLM)

**Frontend**
- React
- Deployed on Vercel

**Deployment**
- Backend: Render  
- Frontend: Vercel

---

## Running the Project Locally

### Backend

```bash
pip install -r requirements.txt
uvicorn api:app --reload
