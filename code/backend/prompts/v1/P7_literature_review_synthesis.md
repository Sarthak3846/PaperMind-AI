---
id: P7
name: Literature Review Synthesis
version: v1
step: 9
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You write literature reviews.

## USER
Write a literature review answering the question, as JSON with these sections:
{"research_overview": [{"text": "...", "chunk_ids": ["..."]}],
 "paper_summaries": [{"paper_id": "...", "statements": [{"text": "...", "chunk_ids": ["..."]}]}],
 "cross_paper_synthesis": [{"text": "...", "chunk_ids": ["..."]}],
 "agreements_and_contradictions": [{"text": "...", "chunk_ids": ["..."]}],
 "research_gaps": [{"text": "...", "chunk_ids": ["..."]}],
 "limitations": [{"text": "...", "chunk_ids": ["..."], "meta": false}],
 "conclusion": [{"text": "...", "chunk_ids": ["..."]}]}

Question: {question}

Paper analyses:
{analyses_json}

Comparison:
{comparison_json}

Research gaps:
{gaps_json}

Evidence:
{evidence_json}
