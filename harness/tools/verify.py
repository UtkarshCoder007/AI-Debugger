import subprocess
import sys

from .base import Tool


def run_tests(ctx):
    ctx.tests_run += 1
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
        cwd=ctx.root, capture_output=True, text=True, timeout=60,
    )
    return r.stdout + r.stderr


RUN_TESTS = Tool(
    name="run_tests",
    description="Run the test suite and return its output.",
    parameters={"type": "object", "properties": {}},
    func=run_tests,
)