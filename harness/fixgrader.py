import hashlib
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

from .config import FIXTURES_DIR
from .sandbox import scrubbed_env, source_files


def _suite(project_dir, fixture):
    """Run the visible and hidden tests against a copy of project_dir.
    Returns {(classname, test name): passed}. The pristine visible tests are always used,
    so editing the tests cannot change the grade. Local pytest only: no API tokens."""
    fixture_dir = FIXTURES_DIR / fixture
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        work = Path(tmp) / "ws"
        shutil.copytree(project_dir, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        shutil.rmtree(work / "tests", ignore_errors=True)
        shutil.copytree(fixture_dir / "project" / "tests", work / "tests",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(fixture_dir / "hidden_tests", work / "hidden_tests")
        report = Path(tmp) / "report.xml"
        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "tests", "hidden_tests", "-q", "--tb=no",
                 "-p", "no:cacheprovider", f"--junitxml={report}"],
                cwd=work, capture_output=True, text=True, timeout=120, env=scrubbed_env(),
            )
        except subprocess.TimeoutExpired:
            return {}
        if not report.exists():
            return {}
        results = {}
        for tc in ET.parse(report).getroot().iter("testcase"):
            failed = tc.find("failure") is not None or tc.find("error") is not None
            results[(tc.get("classname", ""), tc.get("name", ""))] = not failed
        return results


@lru_cache(maxsize=None)
def _baseline(fixture):
    """How the untouched, buggy project does. Used to detect regressions."""
    return _suite(FIXTURES_DIR / fixture / "project", fixture)


def _files(folder):
    return {
        p.relative_to(folder).as_posix(): p
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
    }


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tampered(fixture, workspace):
    """True if anything other than an existing source file differs from the pristine project."""
    original = FIXTURES_DIR / fixture / "project"
    before, after = _files(original), _files(workspace)
    if set(before) != set(after):
        return True
    editable = set(source_files(original))
    return any(_digest(before[r]) != _digest(after[r]) for r in before if r not in editable)


def grade_fix(fixture, workspace, key):
    """Grade the code the agent left behind. A bug counts as fixed only if every hidden
    test for it passes. A regression is a visible test that passed originally but fails now."""
    now = _suite(workspace, fixture)
    before = _baseline(fixture)

    fixed, not_fixed = [], []
    for bug in key["bugs"]:
        outcomes = [ok for (classname, _), ok in now.items()
                    if classname.split(".")[-1] == bug["hidden_tests"]]
        (fixed if outcomes and all(outcomes) else not_fixed).append(bug["id"])

    regressions = sorted(
        name for (classname, name), was_ok in before.items()
        if was_ok and classname.startswith("tests.") and not now.get((classname, name), False)
    )
    return {
        "bugs_fixed": sorted(fixed),
        "bugs_not_fixed": sorted(not_fixed),
        "regressions": regressions,
        "suite_ran": bool(now),
        "tampered": _tampered(fixture, workspace),
    }