"""Where do the tokens go? Reads an existing experiment's run logs; makes no API calls.
Usage: python profile.py v2-coverage-gate"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_calls(run_id):
    log = ROOT / "runs" / run_id / "log.jsonl"
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    return [e for e in events if e["event"] == "model_call"]


def main():
    label = sys.argv[1]
    data = json.loads((ROOT / "results" / f"{label}.json").read_text(encoding="utf-8"))
    total = {"fixed": 0, "history": 0, "completion": 0}

    print(f"{label}: token profile\n")
    for i, row in enumerate(data["runs"], 1):
        calls = load_calls(row["run_id"])
        if not calls:
            continue
        base = calls[0]["prompt_tokens"]  # system prompt + tool schemas + task, resent every call
        prompt = sum(c["prompt_tokens"] for c in calls)
        completion = sum(c["completion_tokens"] for c in calls)
        fixed = base * len(calls)
        history = prompt - fixed          # everything the conversation has added on top
        total["fixed"] += fixed
        total["history"] += history
        total["completion"] += completion
        print(f"run {i}: {len(calls)} calls | prompt {prompt} (fixed {fixed} + history {history}) | completion {completion}")
        print("   prompt tokens per call:", " ".join(str(c["prompt_tokens"]) for c in calls))

    grand = sum(total.values())
    print("\nWhere all the tokens went:")
    for name, label_text in [("fixed", "fixed overhead (system prompt + tool schemas, resent each call)"),
                             ("history", "conversation history (files, tool output, nudges, resent each call)"),
                             ("completion", "model output (includes hidden reasoning)")]:
        print(f"  {100 * total[name] / grand:5.1f}%  {label_text}")


if __name__ == "__main__":
    main()