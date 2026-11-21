# Test table (Milestone 2, Section 4)

Fill this from a REAL run: `python test-data/run_eval.py` writes `results/final/summary.md` with the same columns.
Copy that table here. Do not edit actual outputs by hand. If you override an automatic Pass/Fail, write the reason.

| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |
|---|---|---|---|---|---|
| T01 | What problem does Self-RAG address and how does it work? | Normal | (see inputs/test_cases.json) | _run the evaluation_ | _ |
| T02 | Summarize the methodology of the original RAG paper by Lewis et al. (1 paper selected) | Normal | | | |
| T03 | Compare REALM and the original RAG paper | Normal | | | |
| T04 | Compare the two RAG surveys | Normal | | | |
| T05 | What research gaps exist in evaluating RAG systems? | Normal | | | |
| T06 | Do these papers agree on when to retrieve? | Normal | | | |
| T07 | Write a literature review on RAG and hallucination | Normal | | | |
| T08 | How do I bake sourdough bread at home? | Edge | | | |
| T09 | RAG | Edge | | | |
| T10 | RAG hallucination kaise kam karta hai? | Edge | | | |
| T11 | Reflection-token question restricted to the GlobalRAG paper | Edge | | | |
| T12 | What is the finite frame property in modal logic? | Edge | | | |
| T13 | (empty question) | Invalid | | | |
| T14 | 1100-character question | Invalid | | | |
| T15 | Unknown paper id | Invalid | | | |

Number of test inputs to enter in form Q17: **15** (must equal the rows in your PDF table).

## Fault-injection tests (not model runs)

`cd code/backend && python -m pytest` executes 48 automated tests with a scripted fake model. They cover invalid
model output, fabricated chunk IDs, missing citations, API outages, unsupported numbers and error propagation.
They prove the safeguards work; they are **not** evidence about Gemini's behaviour, so keep them out of the 15-row table
or label them clearly as "unit test, fault injection".
