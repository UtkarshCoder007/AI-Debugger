"""What did the agent actually do, step by step? Reads an experiment's run logs; no API calls.
Usage: python trace.py v3-notes-pruning"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def short(path):
    return Path(path).stem[:5]


def describe(event):
    name, args, out = event["name"], event["args"], event["output"]
    if name == "list_files":
        return "LIST"
    if name == "read_file":
        return f"READ:{short(args.get('path', '?'))}"
    if name == "search":
        return "SEARCH"
    if name == "run_tests":
        return "TESTS"
    if name == "add_note":
        return "NOTE" if not out.startswith("error") else "NOTE-REJECTED"
    if name == "submit_findings":
        return "SUBMIT-OK" if out.startswith("Findings recorded") else "SUBMIT-REFUSED"
    if name in ("apply_edits", "replace_in_file"):
        return "EDIT-REJECTED" if out.startswith("error") else "EDIT-OK"
    return name


def main():
    label = sys.argv[1]
    data = json.loads((ROOT / "results" / f"{label}.json").read_text(encoding="utf-8"))
    for i, row in enumerate(data["runs"], 1):
        events = [json.loads(l) for l in (ROOT / "runs" / row["run_id"] / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        tools = [e for e in events if e["event"] == "tool"]
        calls = [e for e in events if e["event"] == "model_call"]
        reads = Counter(e["args"].get("path", "?") for e in tools if e["name"] == "read_file")
        rereads = sum(c - 1 for c in reads.values())
        nudges = sum(1 for e in events if e["event"] == "nudge")
        print(f"run {i}: {row['status']} | {row['steps']} steps | {row['tokens']} tokens | re-reads: {rereads} | plain-text nudges: {nudges}")
        print("   file reads:", ", ".join(f"{short(p)} x{c}" for p, c in reads.items()) or "none")
        print("   sequence:  ", " > ".join(describe(e) for e in tools))
        for e in tools:
            if e["name"] in ("apply_edits", "replace_in_file") and e["output"].startswith("error"):
                print("   rejected:", e["output"][:200].replace("\n", " "))
        print("   prompt tokens per call:", " ".join(str(c["prompt_tokens"]) for c in calls))
        print("   stubs shown per call:  ", " ".join(str(c.get("pruned_results", 0)) for c in calls))
        for n in row.get("notes", []):
            print("   note:", n[:140])
        print()


if __name__ == "__main__":
    main()