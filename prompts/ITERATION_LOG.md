# Prompt iteration log

Three saved versions of every prompt (P1-P8) exist in `prompts/v1`, `prompts/v2`, `prompts/v3`.
`prompts/final` is a frozen copy of v3 and is what the application loads by default (`PROMPT_VERSION=final`).
**Prompt versions recorded: 3** (v1, v2, v3 = final).

All versions use the same variables and the same output schemas, so any version can be run through the
full pipeline: `python test-data/run_eval.py --prompt-version v1` (then v2, v3/final), and
`python test-data/run_eval.py --compare` prints the metrics table used below.

| Version | What changed | Why it was changed (design rationale) | Result after the change |
|---|---|---|---|
| v1 | Baseline. One-line system prompt, short user prompt that names the JSON fields. Temperature 1.0, no rules, no examples. | Starting point: the simplest instruction that can produce the required JSON. | **TO FILL** from `results/v1/metrics.json` and `summary.md` |
| v2 | Full role definition per component; explicit grounding rules (use only the passages, copy chunk IDs exactly, verbatim quotes, null instead of guessing); exact JSON schema in the system prompt; temperature 0.5. | v1 gives the model no definition of "supported", "explicit vs inferred" or "comparable", and no instruction to leave fields empty. Expected failure modes: invented chunk IDs, paraphrased "quotes", guessed fields. | **TO FILL** |
| v3 | Stricter wording about downstream machine checks (the model is told that IDs and quotes are verified in code); caps on list lengths; extra rules per prompt (contradiction vs difference, no global novelty, numbers must be in the text); few-shot examples for P1, P2, P6, P8; per-prompt temperature (0.0-0.3). | To reduce schema repairs and unsupported claims left after v2, and to make behaviour repeatable between runs. | **TO FILL** |

## How to fill the Result column honestly

1. Run all 15 cases for each version (`--prompt-version v1`, `v2`, `v3`). Runs are non-deterministic, so run each version at least twice (copy `results/<v>` to `results/<v>_run1` between runs, or note the numbers per run).
2. Run `python test-data/run_eval.py --compare` and copy the numbers: first-pass JSON validity, repairs, invalid-after-repair, mean supported ratio, cases passed.
3. Open the saved JSON for failing cases and write what you actually saw (e.g. "v1: 14 of 90 evidence quotes rejected as not found in source; v2: 3 of 88").
4. Edit the **Why** column to match what the results showed. The "why" column above is the design rationale written before testing; if v1 turns out not to fail in the way predicted, say so.

The Milestone 2 guidelines require observed results with numbers ("It got better" is not accepted), and warn that a log with no observed results loses marks.
