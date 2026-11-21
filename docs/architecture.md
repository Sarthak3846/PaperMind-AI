# PaperMind AI - architecture and diagrams

All diagrams are Mermaid and describe the code as built. To get images for the Milestone 2 PDF, paste a block into
https://mermaid.live and export PNG/SVG (the guidelines require diagrams that match what you built and are not copied from the internet).

## 1. Prompt workflow (10 stages, 8 prompts)

```mermaid
flowchart TD
    Q[Researcher question + optional paper selection] --> V[1 Validate input - code]
    V -->|invalid| E1[HTTP 422 / 400 or failed result]
    V --> P1[2 P1 Query understanding - SearchAgent]
    P1 -->|LLM failure| FB[fallback: raw question terms + warning]
    P1 --> R[3 BM25 retrieval - no LLM]
    FB --> R
    R -->|no passages| IE[status: insufficient_evidence - stop]
    R --> P2[4 P2 Evidence extraction - ReaderAgent]
    P2 --> QC{{code: chunk id exists and quote found in chunk?}}
    QC -->|rejected items dropped| P5
    P2 -->|LLM failure| FAIL[status: failed - nothing passed on]
    QC --> P5[5 P5 Evidence critic - CriticAgent]
    P5 -->|nothing validated| IE
    P5 --> P3[6 P3 Per-paper analysis - PaperAnalystAgent, one call per paper]
    P3 --> P4[7 P4 Cross-paper comparison - ComparisonAgent, needs 2+ papers]
    P4 --> P6[8 P6 Research gaps - ResearchGapAgent]
    P6 --> P7[9 P7 Literature review - TeacherAgent]
    P7 --> P8[10 P8 Citation verification - CitationVerifier + code checks]
    P8 --> OUT[Result: review + per-claim status + references]
```

## 2. Task decomposition

```mermaid
flowchart LR
    T[Evidence-grounded literature review] --> A[Understand the question]
    T --> B[Find passages]
    T --> C[Establish trustworthy evidence]
    T --> D[Analyse each paper alone]
    T --> E[Compare across papers]
    T --> F[Find gaps]
    T --> G[Write the review]
    T --> H[Verify every claim]
    A --- P1
    B --- BM25
    C --- P2 & P5
    D --- P3
    E --- P4
    F --- P6
    G --- P7
    H --- P8
```

## 3. Input-output flow

```mermaid
flowchart LR
    I1[question: text] --> RT[Retrieval]
    I2[paper_ids: optional] --> RT
    RT --> PS[passages with chunk_id, paper, page]
    PS --> EV[validated evidence: chunk_id, verbatim quote, claim]
    EV --> AN[PaperAnalysis x N: 8 structured fields, each claim with chunk_ids]
    AN --> CP[Comparison: table, similarities, differences, contradictions, incompatibilities]
    AN --> GP[Gaps: explicit or inferred, supporting papers and chunks]
    CP --> RV
    GP --> RV[Review: 7 sections of cited statements]
    EV --> RV
    RV --> VF[Verification: supported / partial / unsupported / unverified per claim]
    VF --> UI[UI tabs + Markdown export + numbered references with page numbers]
```

## 4. System architecture

```mermaid
flowchart LR
    subgraph Browser
      UI[React + Vite + Tailwind workspace]
    end
    subgraph Backend [FastAPI - code/backend]
      API[app/main.py: /api/research, /api/research/stream SSE, /api/papers, /api/health]
      ROOT[agents/root_agent.py - orchestration, events]
      AG[agents/*: Search, Reader, Critic, PaperAnalyst, Comparison, ResearchGap, Teacher, Verifier]
      LLM[app/llm.py: retries, JSON parse, schema validation, repair, stats]
      PR[app/prompts.py: loads /prompts/<version>]
      RET[retrieval/: preprocessing.py, index.py BM25]
    end
    subgraph Data
      PDF[DATASET/*.pdf]
      JSON[data/processed/chunks.json, papers.json, ingest_report.json]
      PROMPTS[prompts/v1 v2 v3 final]
    end
    G[(Gemini API)]
    UI -- POST + SSE events --> API --> ROOT --> AG --> LLM --> G
    AG --> RET --> JSON
    PDF -- python -m retrieval.preprocessing --> JSON
    PR --> PROMPTS
    AG --> PR
```

## 5. RAG pipeline

```mermaid
flowchart TD
    subgraph Offline ingestion
      A[PDF] --> B[pdfium text per page; pypdf fallback]
      B --> C[clean: soft hyphens, running headers, page numbers]
      C --> D[900-char chunks with 150 overlap, never crossing a page]
      D --> E[chunk_id = paper_id:p PAGE :c INDEX]
      E --> F[chunks.json + bibliography flag]
    end
    subgraph Online retrieval
      Q[keywords from P1] --> T[tokenise, stop-words, light stemming]
      T --> BM[BM25 scores]
      BM --> G{coverage gate: enough query terms in chunk?}
      G -->|no| NONE[no hit]
      G -->|yes| H[group by paper, boost papers named in the question, round-robin top 12]
    end
    F --> BM
```

## 6. Agent loop (sequence)

```mermaid
sequenceDiagram
    participant UI
    participant Root as RootAgent (code)
    participant A as Agent
    participant L as LLMService
    participant G as Gemini
    UI->>Root: question, paper_ids
    loop each stage
        Root-->>UI: event stage_start (SSE)
        Root->>A: run(inputs)
        A->>L: call_json(prompt, schema)
        L->>G: generate (retry on 429/5xx)
        G-->>L: JSON text
        L->>L: parse + validate (one repair attempt)
        L-->>A: typed object or LLMError
        A->>A: code checks (ids, quotes, numbers)
        alt failure
            A-->>Root: error -> stage_error, pipeline stops or stage skipped
        else ok
            A-->>Root: validated result
        end
        Root-->>UI: event stage_done (SSE)
    end
    Root-->>UI: result event
```

## Design decisions that matter for grading

* **Failures never become facts.** A failed stage raises; the Root Agent stops or skips and says so. The original DebateRAG returned `"Error in X: ..."` strings that flowed into the next agent.
* **Two layers of citation checking.** Code first (ID exists, quote is in the chunk, numbers appear in the cited text), then the P8 verifier for meaning.
* **Gaps are scoped.** `basis` is explicit (authors state it) or inferred; global-novelty wording is flagged; every gap view carries a scope disclaimer.
* **Stateless calls.** No chat history is kept between calls or users (the original agents kept one global chat per agent).
