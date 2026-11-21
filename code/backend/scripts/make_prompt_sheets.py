"""Generate docs/prompt_sheets.md (one sheet per final prompt, in the Milestone 2 format) from /prompts/final.
Run from code/backend:  python scripts/make_prompt_sheets.py
The 'sample run' line is left for you to fill from a REAL run saved in test-data/results/final/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import REPO_ROOT, get_settings  # noqa: E402
from app.prompts import PROMPT_FILES, PromptLibrary  # noqa: E402

PURPOSE = {
    "P1": "Turn the researcher's question into a task type, search keywords and sub-questions.",
    "P2": "Extract verbatim, citable evidence from retrieved passages.",
    "P3": "Produce a structured analysis (problem, method, datasets, results, limits) of ONE paper.",
    "P4": "Compare analysed papers; separate real contradictions from differences caused by different settings.",
    "P5": "Act as adversarial reviewer: decide which evidence may be passed to later agents.",
    "P6": "Identify explicit vs inferred research gaps without claiming global novelty.",
    "P7": "Write the structured literature review with citations restricted to supplied material.",
    "P8": "Judge each claim as supported / partially supported / unsupported against its cited passages.",
}
VARS = {
    "question": "the researcher's question (string, max 1000 chars)",
    "passages": "retrieved passages, each with a [chunk_id | paper | page] header",
    "paper_title": "title of the paper being analysed", "paper_id": "short id of that paper, e.g. selfrag2023",
    "analyses_json": "compact JSON of the per-paper analyses (claims carry chunk_ids)",
    "comparison_json": "JSON of the cross-paper comparison, or a 'skipped' marker",
    "evidence_json": "JSON list of evidence items (evidence_id, claim, quote/chunk_id)",
    "gaps_json": "JSON list of identified research gaps",
    "claims_json": "JSON list of {sid, claim, passages[]} to verify",
}

s = get_settings()
lib = PromptLibrary(s.prompts_dir, "final")
out = ["# Prompt sheets (final prompt set)\n", f"Generated from `prompts/final/`. Model: `{s.gemini_model}` via the google-genai SDK; "
       "every call is stateless and requests JSON output (`response_mime_type=application/json`).\n"]
for pid in PROMPT_FILES:
    sp = lib.get(pid)
    meta = (s.prompts_dir / "final" / PROMPT_FILES[pid]).read_text(encoding="utf-8").split("---")[1]
    ex = next((l.split(":")[1].strip() for l in meta.splitlines() if l.startswith("examples")), "0")
    step = next((l.split(":")[1].strip() for l in meta.splitlines() if l.startswith("step")), "?")
    out += [f"\n## {pid} - {sp.name}\n", f"- **Step in workflow:** {step} of 10\n- **Purpose:** {PURPOSE[pid]}",
            f"- **Tool and model:** Gemini API, model from `GEMINI_MODEL` (default `{s.gemini_model}`)",
            f"- **Settings:** temperature {sp.temperature}, JSON output mode, max 8192 output tokens",
            f"- **Number of examples included:** {ex}", "- **Output format:** JSON, validated against a Pydantic schema (one automatic repair retry)",
            "- **Variables:**"]
    out += [f"  - `{{{v}}}`: {VARS.get(v, '')}" for v in sorted(sp.variables())]
    out += ["\n**System prompt**\n", "```text", sp.system, "```", "\n**User prompt template**\n", "```text", sp.user_template, "```",
            "\n**Sample run (real input and actual output):** _paste from `test-data/results/final/Txx.json` after you run the evaluation._\n"]
dest = REPO_ROOT / "docs" / "prompt_sheets.md"
dest.write_text("\n".join(out), encoding="utf-8")
print("wrote", dest)
