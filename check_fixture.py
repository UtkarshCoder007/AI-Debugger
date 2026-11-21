"""Checks the grader itself, with no API calls: the buggy project must score 0/5 and the
reference solution must score 5/5. Run it after changing the hidden tests or the answer key."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("GROQ_API_KEY", "unused")  # config requires the variable to exist

from harness.config import FIXTURES_DIR
from harness.fixgrader import grade_fix
from harness.grader import load_key

fixture = sys.argv[1] if len(sys.argv) > 1 else "shop_v1"
key = load_key(fixture)
project = FIXTURES_DIR / fixture / "project"
solution = FIXTURES_DIR / fixture / "solution"


def show(title, fix, expect_fixed):
    ok = (len(fix["bugs_fixed"]) == expect_fixed and not fix["regressions"]
          and not fix["tampered"] and fix["suite_ran"])
    print(f"{title}: fixed {len(fix['bugs_fixed'])}/{len(key['bugs'])} | "
          f"regressions {fix['regressions'] or 'none'} | tampered {fix['tampered']} -> {'OK' if ok else 'PROBLEM'}")
    if fix["bugs_not_fixed"] and expect_fixed:
        print("   not fixed:", ", ".join(fix["bugs_not_fixed"]))
    return ok


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    buggy = Path(tmp) / "buggy"
    fixed = Path(tmp) / "fixed"
    shutil.copytree(project, buggy)
    shutil.copytree(project, fixed)
    shutil.copytree(solution, fixed, dirs_exist_ok=True)
    results = [
        show("buggy project", grade_fix(fixture, buggy, key), 0),
        show("reference fix", grade_fix(fixture, fixed, key), len(key["bugs"])),
    ]
print("\nGrader is trustworthy." if all(results) else "\nFix the hidden tests or the solution before running experiments.")