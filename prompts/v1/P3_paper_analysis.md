---
id: P3
name: Individual Paper Analysis
version: v1
step: 6
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You summarise research papers.

## USER
Analyse the paper "{paper_title}" using the passages below. Give the research problem, objectives, methodology, datasets, findings, quantitative results, limitations and future directions as JSON with this shape:
{"research_problem": {"text": "...", "chunk_ids": ["..."]} | null,
 "objectives": [{"text": "...", "chunk_ids": ["..."]}],
 "methodology": [{"text": "...", "chunk_ids": ["..."]}],
 "datasets": [{"text": "...", "chunk_ids": ["..."]}],
 "findings": [{"text": "...", "chunk_ids": ["..."]}],
 "quantitative_results": [{"metric": "...", "value": "...", "context": "...", "chunk_ids": ["..."]}],
 "limitations": [{"text": "...", "chunk_ids": ["..."]}],
 "future_directions": [{"text": "...", "chunk_ids": ["..."]}]}

Researcher question for context: {question}

Passages:
{passages}
