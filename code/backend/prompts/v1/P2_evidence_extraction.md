---
id: P2
name: Evidence Extraction
version: v1
step: 4
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You extract facts from text.

## USER
Question: {question}

Passages:
{passages}

List the facts relevant to the question as JSON: {"evidence": [{"chunk_id": "...", "quote": "...", "claim": "...", "kind": "fact"}]}
