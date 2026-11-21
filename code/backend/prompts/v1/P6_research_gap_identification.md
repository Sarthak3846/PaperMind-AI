---
id: P6
name: Research-Gap Identification
version: v1
step: 8
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You find research gaps.

## USER
Find research gaps in these papers. JSON shape:
{"gaps": [{"title": "...", "description": "...", "why_it_exists": "...",
  "basis": "explicit | inferred", "supporting_paper_ids": ["..."], "chunk_ids": ["..."]}]}

Question: {question}

Paper analyses:
{analyses_json}

Comparison:
{comparison_json}
