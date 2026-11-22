"""How much of the prompt was served from Groq's cache? Reads an experiment's run logs; no API calls.
Usage: python cache_check.py v7-medium-effort"""
import json
import sys
from pathlib import Path

data = json.loads(Path("results", f"{sys.argv[1]}.json").read_text(encoding="utf-8"))
total_prompt = total_cached = calls = 0
for row in data["runs"]:
    for line in Path("runs", row["run_id"], "log.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e["event"] == "model_call":
            calls += 1
            total_prompt += e["prompt_tokens"]
            total_cached += e.get("cached_tokens", 0)
print(f"{calls} model calls")
print(f"prompt tokens: {total_prompt} | cached: {total_cached} ({100 * total_cached / total_prompt:.0f}%)")
print(f"counted toward TPM (prompt - cached): {total_prompt - total_cached}")