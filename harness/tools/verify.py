import subprocess
import sys

from ..sandbox import scrubbed_env
from .base import Tool


def run_pytest(ctx):
    """Run the visible tests in the workspace. Returns (compact output, all_passed)."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=line", "-rf", "-p", "no:cacheprovider"],
            cwd=ctx.root, capture_output=True, text=True, timeout=60, env=scrubbed_env(),
        )
    except subprocess.TimeoutExpired:
        return "error: the test run timed out after 60 seconds", False
    return r.stdout + r.stderr, r.returncode == 0


def run_tests(ctx):
    ctx.tests_run += 1
    output, _ = run_pytest(ctx)
    return output


RUN_TESTS = Tool(
    name="run_tests",
    description="Run the test suite and return its output.",
    parameters={"type": "object", "properties": {}},
    func=run_tests,
)