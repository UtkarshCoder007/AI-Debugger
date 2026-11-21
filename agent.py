from harness.grader import grade, load_key
from harness.loop import run_agent

if __name__ == "__main__":
    result = run_agent("shop_v1")
    key = load_key("shop_v1")
    n = len(key["bugs"])
    g = grade(result["findings"], key)
    fix = result["fix"]
    print(f"\nstatus: {result['status']} | steps: {result['steps']} | tokens: {result['tokens']} of {result['token_budget']}")
    if result["budget_message"]:
        print(result["budget_message"])
    print(f"edits: {result['edits_made']} | changed files: {', '.join(result['changed_files']) or 'none'}")
    print(f"\nfindings: found {len(g['found'])}/{n} | false positives: {g['false_positives']}")
    print(f"fixes:    fixed {len(fix['bugs_fixed'])}/{n}: {', '.join(fix['bugs_fixed']) or '-'}")
    print(f"not fixed: {', '.join(fix['bugs_not_fixed']) or '-'}")
    print(f"regressions: {', '.join(fix['regressions']) or 'none'} | tampered: {fix['tampered']}")
    if "grading_error" in fix:
        print(f"GRADING ERROR: {fix['grading_error']}")
    print(f"details: runs/{result['run_id']}/  (log.jsonl, result.json, changes/fix.diff)")