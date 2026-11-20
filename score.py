import argparse
import json
import time
from datetime import datetime
from statistics import mean

from harness import config
from harness.grader import grade, load_key
from harness.loop import run_agent


def main():
    ap = argparse.ArgumentParser(description="Run the agent N times and grade every run.")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--label", default=None, help="name for this experiment, e.g. v1-baseline")
    ap.add_argument("--fixture", default="shop_v1")
    ap.add_argument("--pause", type=int, default=15, help="seconds between runs (rate limits)")
    args = ap.parse_args()

    label = args.label or datetime.now().strftime("%Y%m%d-%H%M%S")
    key = load_key(args.fixture)
    source_files = set(key["source_files"])
    n_bugs = len(key["bugs"])

    rows = []
    print(f"{'run':<4}{'status':<12}{'recall':<9}{'fp':<4}{'tokens':<8}{'steps':<7}{'all files':<11}{'tests':<7}{'gate':<6}notes")
    for i in range(1, args.runs + 1):
        result = run_agent(args.fixture, verbose=False)
        g = grade(result["findings"], key)
        row = {
            **result, **g,
            "all_files_read": source_files <= set(result["files_read"]),
            "tests_run_flag": result["tests_run"] > 0,
        }
        rows.append(row)
        print(f"{i:<4}{row['status']:<12}{len(g['found'])}/{n_bugs:<7}{g['false_positives']:<4}"
              f"{row['tokens']:<8}{row['steps']:<7}{'yes' if row['all_files_read'] else 'no':<11}"
              f"{'yes' if row['tests_run_flag'] else 'no':<7}{row['gate_rejections']:<6}{len(row['notes'])}")
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
        "rules": {
            "require_full_coverage": config.REQUIRE_FULL_COVERAGE,
            "use_notes": config.USE_NOTES,
            "prune_old_tool_results": config.PRUNE_OLD_TOOL_RESULTS,
            "keep_recent_results": config.KEEP_RECENT_RESULTS,
        },
        "runs": len(rows),
        "errored_runs": len(rows) - len(ok),
        "mean_bugs_found": round(mean(len(r["found"]) for r in ok), 2),
        "mean_false_positives": round(mean(r["false_positives"] for r in ok), 2),
        "mean_tokens": round(mean(r["tokens"] for r in ok)),
        "mean_steps": round(mean(r["steps"] for r in ok), 1),
        "pct_all_files_read": round(100 * mean(r["all_files_read"] for r in ok)),
        "pct_tests_run": round(100 * mean(r["tests_run_flag"] for r in ok)),
        "mean_gate_rejections": round(mean(r["gate_rejections"] for r in ok), 2),
        "mean_notes": round(mean(len(r["notes"]) for r in ok), 1),
        "per_bug_detection": {
            b["id"]: sum(b["id"] in r["found"] for r in ok) for b in key["bugs"]
        },
    }

    print(f"\n=== {label} | {summary['model']} | {len(ok)} scored runs ===")
    print(f"mean bugs found:      {summary['mean_bugs_found']}/{n_bugs}")
    print(f"mean false positives: {summary['mean_false_positives']}")
    print(f"mean tokens / steps:  {summary['mean_tokens']} / {summary['mean_steps']}")
    print(f"read every source file: {summary['pct_all_files_read']}% of runs | ran tests: {summary['pct_tests_run']}% of runs")
    print(f"gate rejections per run: {summary['mean_gate_rejections']} | notes per run: {summary['mean_notes']}")
    print(f"rules: {summary['rules']}")
    print("detection per bug:")
    for bug_id, count in summary["per_bug_detection"].items():
        print(f"  {bug_id:<24}{count}/{len(ok)}")
    if summary["errored_runs"]:
        print(f"({summary['errored_runs']} run(s) errored and were excluded)")

    config.RESULTS_DIR.mkdir(exist_ok=True)
    out = config.RESULTS_DIR / f"{label}.json"
    out.write_text(json.dumps({"summary": summary, "runs": rows}, indent=2), encoding="utf-8")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()