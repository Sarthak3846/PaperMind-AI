#!/usr/bin/env python3
"""Run the PaperMind test cases against the REAL pipeline and save every actual output.

    python test-data/run_eval.py                         # all cases, prompt set 'final'
    python test-data/run_eval.py --prompt-version v1     # evaluate an older prompt set
    python test-data/run_eval.py --cases T01,T05         # subset
    python test-data/run_eval.py --compare               # table of metrics across prompt versions

Needs GEMINI_API_KEY (code/backend/.env). Pass/Fail is computed by code from the checks in
inputs/test_cases.json - you may override a row by hand in the Milestone 2 PDF, but write down why.
Results go to test-data/results/<prompt-version>/ (one JSON per case + summary.md + metrics.json).

--selftest runs the harness against a scripted FAKE model to check the harness itself. Those results
are written to results/_selftest and are NOT valid evidence for submission."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "code" / "backend"
CASES_FILE = HERE / "inputs" / "test_cases.json"


def short(text: str, n: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


# --------------------------------------------------------------------------- checks
def evaluate(case: dict, http_status: int, body: dict) -> tuple[bool, list[str], str]:
    """Return (passed, failed_check_descriptions, short_actual_output)."""
    checks = case["checks"]
    failures: list[str] = []
    result = body if http_status == 200 else {}
    status = result.get("status")

    if "http_status" in checks and http_status != checks["http_status"]:
        failures.append(f"HTTP {http_status}, expected {checks['http_status']}")
    if "http_status" not in checks and http_status != 200:
        failures.append(f"HTTP {http_status}: {str(body.get('detail', body))[:120]}")
    if "status" in checks and status != checks["status"]:
        failures.append(f"status={status}, expected {checks['status']}")
    if "status_in" in checks and status not in checks["status_in"]:
        failures.append(f"status={status}, expected one of {checks['status_in']}")

    if http_status == 200:
        analyses = result.get("paper_analyses") or []
        comp = result.get("comparison") or {}
        review = result.get("review") or {}
        gaps = result.get("gaps") or {}
        sources = result.get("sources") or {}
        sections = ["research_overview", "cross_paper_synthesis", "agreements_and_contradictions", "research_gaps", "limitations", "conclusion"]
        statements = [s for k in sections for s in review.get(k, [])] + [s for p in review.get("paper_summaries", []) for s in p.get("statements", [])]
        used_ids = {c for s in statements for c in s.get("chunk_ids", [])}
        v = result.get("verification") or {}

        if "min_papers_analyzed" in checks and len(analyses) < checks["min_papers_analyzed"]:
            failures.append(f"{len(analyses)} papers analysed, need {checks['min_papers_analyzed']}")
        if checks.get("comparison_present") and (not comp or comp.get("skipped")):
            failures.append("comparison missing or skipped")
        if checks.get("comparison_skipped") and not comp.get("skipped"):
            failures.append("comparison was not skipped")
        if checks.get("comparison_has_table") and not comp.get("table"):
            failures.append("comparison table empty")
        if checks.get("comparison_has_findings") and not (comp.get("differences") or comp.get("similarities") or comp.get("contradictions")):
            failures.append("comparison has no similarities, differences or contradictions")
        if checks.get("has_gaps") and not gaps.get("gaps"):
            failures.append("no research gaps returned")
        if checks.get("gaps_scoped"):
            if not gaps.get("scope_disclaimer"):
                failures.append("gap scope disclaimer missing")
            if any(g.get("basis") not in ("explicit", "inferred") for g in gaps.get("gaps", [])):
                failures.append("a gap has no explicit/inferred label")
        if "min_review_statements" in checks and len(statements) < checks["min_review_statements"]:
            failures.append(f"{len(statements)} review statements, need {checks['min_review_statements']}")
        if "min_paper_summaries" in checks and len(review.get("paper_summaries", [])) < checks["min_paper_summaries"]:
            failures.append("too few paper summaries")
        if checks.get("has_references") and not (result.get("references") and all(r.get("page", 0) >= 1 for r in result["references"])):
            failures.append("references missing or without page numbers")
        if checks.get("all_citations_exist") and any(c not in sources for c in used_ids):
            failures.append("a cited chunk id does not exist in the corpus")
        if checks.get("citations_within_selection"):
            allowed = set(case["request"].get("paper_ids") or [])
            if allowed and any(sources.get(c, {}).get("paper_id") not in allowed for c in used_ids):
                failures.append("citation from a paper outside the selection")
        if "max_unsupported_ratio" in checks and v.get("checked"):
            ratio = v["unsupported"] / v["checked"]
            if ratio > checks["max_unsupported_ratio"]:
                failures.append(f"{ratio:.0%} of claims unsupported (limit {checks['max_unsupported_ratio']:.0%})")
        if checks.get("no_review") and result.get("review"):
            failures.append("a review was generated but none was expected")
        if "max_llm_calls" in checks and (result.get("metrics") or {}).get("llm_calls", 0) > checks["max_llm_calls"]:
            failures.append(f"{result['metrics']['llm_calls']} model calls, limit {checks['max_llm_calls']}")
        if checks.get("ambiguity_noted") and not (result.get("query_understanding") or {}).get("ambiguities"):
            failures.append("no ambiguity noted by query understanding")
        if checks.get("retrieval_has_hits") and not (result.get("retrieval") or {}).get("n_hits"):
            failures.append("retrieval returned no passages")

    # ---- short human-readable actual output
    if http_status != 200:
        actual = f"HTTP {http_status}: {short(str(body.get('detail', body)), 90)}"
    else:
        m = result.get("metrics") or {}
        v = result.get("verification") or {}
        actual = (f"status={status}; {len(result.get('paper_analyses') or [])} papers; "
                  f"{v.get('supported', 0)}/{v.get('partially_supported', 0)}/{v.get('unsupported', 0)}/{v.get('unverified', 0)} "
                  f"sup/part/unsup/unver; {m.get('llm_calls', 0)} calls; {m.get('elapsed_seconds', 0)}s")
        if result.get("warnings"):
            actual += f"; {len(result['warnings'])} warning(s)"
    return not failures, failures, actual


# --------------------------------------------------------------------------- main
def load_cases(selected: set[str] | None) -> list[dict]:
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    for c in cases:
        rep = c["request"].pop("_repeat_to_chars", None)
        if rep:
            c["request"]["question"] = (c["request"]["question"] * (rep // len(c["request"]["question"]) + 1))[:rep]
    return [c for c in cases if not selected or c["id"] in selected]


def compare_versions() -> None:
    rows = []
    for d in sorted((HERE / "results").glob("*/metrics.json")):
        m = json.loads(d.read_text(encoding="utf-8"))
        rows.append((d.parent.name, m))
    if not rows:
        print("No metrics found. Run the evaluation first.")
        return
    print("| Prompt set | Cases run | Passed | Model calls | First-pass JSON valid | Repairs | Invalid after repair | Mean supported ratio | Mean seconds/run |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, m in rows:
        print(f"| {name} | {m['cases_run']} | {m['passed']} | {m['llm_calls']} | {m['first_pass_valid_rate']} | {m['repairs']} | "
              f"{m['invalid_after_repair']} | {m['mean_supported_ratio']} | {m['mean_seconds']} |")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt-version", default="final", choices=["v1", "v2", "v3", "final"])
    ap.add_argument("--cases", default="", help="comma-separated ids, e.g. T01,T05")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between cases (rate limits)")
    ap.add_argument("--compare", action="store_true", help="print a metrics table across saved prompt versions and exit")
    ap.add_argument("--selftest", action="store_true", help="use a scripted FAKE model to test the harness itself")
    args = ap.parse_args()
    if args.compare:
        compare_versions()
        return 0

    os.environ["PROMPT_VERSION"] = args.prompt_version
    sys.path.insert(0, str(BACKEND))
    from fastapi.testclient import TestClient  # noqa: E402
    from app import main as api  # noqa: E402
    from app.config import get_settings  # noqa: E402

    if args.selftest:
        from tests.fakes import FakeBackend  # noqa: E402
        api.app.dependency_overrides[api.get_backend] = lambda: FakeBackend()
        out_name = "_selftest"
        args.pause = 0
    else:
        s = get_settings()
        if not s.gemini_api_key:
            print("GEMINI_API_KEY is not set. Add it to code/backend/.env first (see .env.example).")
            return 2
        out_name = args.prompt_version

    out_dir = HERE / "results" / out_name
    out_dir.mkdir(parents=True, exist_ok=True)
    client = TestClient(api.app)
    cases = load_cases({c.strip() for c in args.cases.split(",") if c.strip()} or None)
    s = get_settings()
    print(f"Running {len(cases)} case(s) | prompt set: {args.prompt_version} | model: {'FAKE (selftest)' if args.selftest else s.gemini_model}")

    rows, metrics = [], {"calls": 0, "repairs": 0, "invalid": 0, "supported_ratios": [], "seconds": []}
    for n, case in enumerate(cases):
        t0 = time.time()
        resp = client.post("/api/research", json=case["request"])
        try:
            body = resp.json()
        except ValueError:
            body = {"detail": resp.text[:300]}
        passed, failures, actual = evaluate(case, resp.status_code, body)
        (out_dir / f"{case['id']}.json").write_text(json.dumps(
            {"case": case, "http_status": resp.status_code, "passed": passed, "failed_checks": failures,
             "actual_summary": actual, "response": body}, ensure_ascii=False, indent=2), encoding="utf-8")
        m = body.get("metrics") or {} if isinstance(body, dict) else {}
        metrics["calls"] += m.get("llm_calls", 0)
        metrics["repairs"] += m.get("repairs", 0)
        metrics["invalid"] += m.get("invalid_after_repair", 0)
        v = (body.get("verification") or {}) if isinstance(body, dict) else {}
        if v.get("supported_ratio") is not None:
            metrics["supported_ratios"].append(v["supported_ratio"])
        if m.get("elapsed_seconds"):
            metrics["seconds"].append(m["elapsed_seconds"])
        rows.append((case, actual, passed, failures))
        print(f"  {case['id']} {'PASS' if passed else 'FAIL'}  {actual}" + ("" if passed else f"\n        -> {'; '.join(failures)}"))
        if n < len(cases) - 1 and args.pause:
            time.sleep(args.pause)

    banner = "> **SELF-TEST WITH A FAKE MODEL - NOT VALID FOR SUBMISSION**\n\n" if args.selftest else ""
    lines = [f"# Test results - prompt set `{args.prompt_version}`\n", banner,
             f"Model: `{'FAKE' if args.selftest else s.gemini_model}` · generated {time.strftime('%Y-%m-%d %H:%M')}\n",
             "| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |", "|---|---|---|---|---|---|"]
    for case, actual, passed, failures in rows:
        q = case["request"]["question"]
        fail_note = "" if passed else f" — {'; '.join(failures)}"
        lines.append(f"| {case['id']} | {short(q, 60) or '(empty)'} | {case['type']} | {short(case['expected'], 110)} | {short(actual + fail_note, 140)} | {'Pass' if passed else 'Fail'} |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    calls = metrics["calls"]
    agg = {"cases_run": len(rows), "passed": sum(1 for r in rows if r[2]), "llm_calls": calls,
           "repairs": metrics["repairs"], "invalid_after_repair": metrics["invalid"],
           "first_pass_valid_rate": round((calls - metrics["repairs"] - metrics["invalid"]) / calls, 3) if calls else None,
           "mean_supported_ratio": round(sum(metrics["supported_ratios"]) / len(metrics["supported_ratios"]), 3) if metrics["supported_ratios"] else None,
           "mean_seconds": round(sum(metrics["seconds"]) / len(metrics["seconds"]), 1) if metrics["seconds"] else None,
           "model": "FAKE" if args.selftest else s.gemini_model}
    (out_dir / "metrics.json").write_text(json.dumps(agg, indent=2), encoding="utf-8")
    print(f"\n{agg['passed']}/{agg['cases_run']} passed. Saved to {out_dir.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
