import glob, json
from pathlib import Path

for path in sorted(glob.glob("runs/*/log.jsonl")):
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        if e["event"] == "tool" and e["name"] == "submit_findings" and "not read" in e["output"]:
            print(Path(path).parent.name, "->", e["output"][:110])