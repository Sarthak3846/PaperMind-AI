---
id: P4
name: Cross-Paper Comparison
version: v1
step: 7
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You compare research papers.

## USER
Compare the papers below with respect to the question. Output JSON with this shape:
{"comparable": true | false,
 "comparability_notes": "...",
 "table": [{"dimension": "methodology | datasets | evaluation_metrics | findings",
            "entries": [{"paper_id": "...", "value": "...", "chunk_ids": ["..."]}]}],
 "similarities": [{"text": "...", "paper_ids": ["..."], "chunk_ids": ["..."]}],
 "differences": [{"text": "...", "paper_ids": ["..."], "chunk_ids": ["..."]}],
 "contradictions": [{"topic": "...", "positions": [{"paper_id": "...", "statement": "...", "chunk_ids": ["..."]}],
                     "conditions_comparable": true | false, "explanation": "..."}],
 "incompatibilities": [{"paper_ids": ["..."], "reason": "..."}]}

Question: {question}

Paper analyses:
{analyses_json}
