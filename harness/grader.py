import json

from .config import FIXTURES_DIR


def load_key(fixture):
    return json.loads((FIXTURES_DIR / fixture / "answer_key.json").read_text(encoding="utf-8"))


def _norm(path):
    return path.replace("\\", "/").removeprefix("./")


def grade(findings, key):
    """Compare submitted findings with the answer key.
    A finding hits a bug if it names the same file and a line inside the buggy function.
    Each bug counts once; a finding that hits nothing is a false positive."""
    found = set()
    false_positives = 0
    duplicates = 0
    for f in findings:
        hit = None
        for bug in key["bugs"]:
            lo, hi = bug["lines"]
            if _norm(f["file"]) == bug["file"] and lo <= f["line"] <= hi:
                hit = bug["id"]
                break
        if hit is None:
            false_positives += 1
        elif hit in found:
            duplicates += 1
        else:
            found.add(hit)
    all_ids = [b["id"] for b in key["bugs"]]
    return {
        "found": sorted(found),
        "missed": sorted(set(all_ids) - found),
        "false_positives": false_positives,
        "duplicates": duplicates,
    }