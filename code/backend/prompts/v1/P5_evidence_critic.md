---
id: P5
name: Evidence Critic
version: v1
step: 5
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You review evidence.

## USER
Question: {question}

Evidence:
{evidence_json}

Say which evidence items are good and which are weak. JSON shape:
{"validated_ids": ["E1", "E3"],
 "flagged": [{"evidence_id": "E2", "reason": "..."}],
 "contradictions": ["E4 and E7 disagree about ..."],
 "missing_information": ["..."]}
