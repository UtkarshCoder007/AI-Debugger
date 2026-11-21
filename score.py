import argparse
import json
import time
from collections import Counter
from datetime import datetime
from statistics import mean

from harness import config
from harness.grader import grade, load_key
from harness.loop import run_agent


def main():
    ap = argparse.ArgumentParser(description="Run the agent N times and grade every run.")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--label", default=None, help="name for this experiment, e.g. v5-fixing")
    ap.add_argument("--fixture", default="shop_v1")
    ap.add_argument("--pause", type=int, default=15, help="seconds between runs (rate limits)")
    ap.add_argument("--budget", type=int, default=None, help="token budget per run (default: TOKEN_BUDGET from .env)")
    ap.add_argument("--batch-budget", type=int, default=None, help="stop the batch once this many tokens are used in total")
    args = ap.parse_args()
    if args.budget:
        config.TOKEN_BUDGET = args.budget

    label = args.label or datetime.now().strftime("%Y%m%d-%H%M%S")
    key = load_key(args.fixture)
    source_files = set(key["source_files"])
    n_bugs = len(key["bugs"])

    rows = []
    total_tokens = 0
    print(f"{'run':<4}{'status':<16}{'found':<8}{'fixed':<8}{'reg':<5}{'fp':<4}{'tokens':<8}{'steps':<7}{'edits':<7}gate")
    for i in range(1, args.runs + 1):
        result = run_agent(args.fixture, verbose=False)
        total_tokens += result["tokens"]
        g = grade(result["findings"], key)
        fix = result["fix"]
        fixed_n = 0 if fix["tampered"] else len(fix["bugs_fixed"])  # tampering scores zero
        row = {
            **result, **g,
            "fixed_count": fixed_n,
            "all_files_read": source_files <= set(result["files_read"]),
        }
        rows.append(row)
        found = f"{len(g['found'])}/{n_bugs}"
        fixed = f"{fixed_n}/{n_bugs}"
        print(f"{i:<4}{row['status']:<16}{found:<8}{fixed:<8}{len(fix['regressions']):<5}{g['false_positives']:<4}"
              f"{row['tokens']:<8}{row['steps']:<7}{row['edits_made']:<7}{row['gate_rejections']}")
        if fix["tampered"]:
            print("     ^ tampered: the run changed files it should not have; its fixes count as zero")
        if "grading_error" in fix:
            print(f"     ^ grading error: {fix['grading_error']}")
        if args.batch_budget and total_tokens >= args.batch_budget and i < args.runs:
            print(f"Batch token cap reached ({total_tokens} of {args.batch_budget}); stopping after {i} run(s).")
            break
        if i < args.runs:
            time.sleep(args.pause)

    ok = [r for r in rows if r["status"] != "error"]  # API/infrastructure failures are not agent failures
    if not ok:
        print("\nEvery run errored; nothing to average. Check the run logs.")
        return

    summary = {
        "label": label,
        "fixture": args.fixture,
        "model": config.MODEL,
        "rules": {"require_full_coverage": config.REQUIRE_FULL_COVERAGE, "token_budget": config.TOKEN_BUDGET, "reasoning_effort": config.REASONING_EFFORT},
        "runs": len(rows),
        "errored_runs": len(rows) - len(ok),
        "statuses": dict(Counter(r["status"] for r in ok)),
        "mean_bugs_found": round(mean(len(r["found"]) for r in ok), 2),
        "mean_bugs_fixed": round(mean(r["fixed_count"] for r in ok), 2),
        "runs_fully_fixed": sum(r["fixed_count"] == n_bugs and not r["fix"]["regressions"] for r in ok),
        "total_regressions": sum(len(r["fix"]["regressions"]) for r in ok),
        "tampered_runs": sum(bool(r["fix"]["tampered"]) for r in ok),
        "mean_false_positives": round(mean(r["false_positives"] for r in ok), 2),
        "mean_tokens": round(mean(r["tokens"] for r in ok)),
        "mean_steps": round(mean(r["steps"] for r in ok), 1),
        "mean_edits": round(mean(r["edits_made"] for r in ok), 1),
        "pct_all_files_read": round(100 * mean(r["all_files_read"] for r in ok)),
        "mean_gate_rejections": round(mean(r["gate_rejections"] for r in ok), 2),
        "per_bug_found": {b["id"]: sum(b["id"] in r["found"] for r in ok) for b in key["bugs"]},
        "per_bug_fixed": {
            b["id"]: sum(b["id"] in r["fix"]["bugs_fixed"] and not r["fix"]["tampered"] for r in ok)
            for b in key["bugs"]
        },
    }

    print(f"\n=== {label} | {summary['model']} | {len(ok)} scored runs | budget {config.TOKEN_BUDGET} tokens/run ===")
    print(f"run statuses:         {summary['statuses']}")
    print(f"mean bugs found:      {summary['mean_bugs_found']}/{n_bugs}   (review)")
    print(f"mean bugs fixed:      {summary['mean_bugs_fixed']}/{n_bugs}   (hidden tests)")
    print(f"fully fixed runs:     {summary['runs_fully_fixed']}/{len(ok)} | regressions: {summary['total_regressions']} | tampered: {summary['tampered_runs']}")
    print(f"mean false positives: {summary['mean_false_positives']}")
    print(f"mean tokens / steps / edits: {summary['mean_tokens']} / {summary['mean_steps']} / {summary['mean_edits']}")
    print(f"read every source file: {summary['pct_all_files_read']}% | gate rejections per run: {summary['mean_gate_rejections']}")
    print("per bug (found / fixed):")
    for bug_id in summary["per_bug_found"]:
        print(f"  {bug_id:<24}{summary['per_bug_found'][bug_id]}/{len(ok)}   {summary['per_bug_fixed'][bug_id]}/{len(ok)}")
    if summary["errored_runs"]:
        print(f"({summary['errored_runs']} run(s) errored and were excluded)")

    config.RESULTS_DIR.mkdir(exist_ok=True)
    out = config.RESULTS_DIR / f"{label}.json"
    out.write_text(json.dumps({"summary": summary, "runs": rows}, indent=2), encoding="utf-8")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()