---
id: P8
name: Citation Verification
version: v1
step: 10
temperature: 1.0
examples: 0
output: JSON
---
## SYSTEM
You check claims.

## USER
For each claim, say whether the cited passages support it. JSON shape:
{"verdicts": [{"sid": "S1", "verdict": "supported | partially_supported | unsupported", "reason": "..."}]}

Claims with their cited passages:
{claims_json}
