---
id: P1
name: Research Query Understanding
version: v1
step: 1
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You help with research questions.

## USER
Turn this question into search keywords. Reply in JSON with the fields task_type, keywords, sub_questions, ambiguities.

Question: {question}
