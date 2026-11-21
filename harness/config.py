"""All settings in one place. Nothing else in the project reads environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures"  # pristine projects, hidden tests, answer keys: never edited
RUNS_DIR = ROOT / "runs"          # one folder per run: workspace, log, result, changes
RESULTS_DIR = ROOT / "results"    # scorer output, one file per labelled experiment

API_KEY = os.environ["GROQ_API_KEY"]
BASE_URL = "https://api.groq.com/openai/v1"
MODEL = os.environ.get("MODEL", "openai/gpt-oss-120b")
REASONING_EFFORT = "low"

# Harness rules. Each is a switch so any experiment can be reproduced or compared.
REQUIRE_FULL_COVERAGE = True  # submit_findings is refused until every source file was read

# Token budget per run, editable in .env. Checked between model calls, so a run can
# overshoot by one call. At the warning fraction the agent is told to wrap up.
TOKEN_BUDGET = int(os.environ.get("TOKEN_BUDGET", "25000"))
BUDGET_WARN_FRACTION = 0.8

MAX_STEPS = 20
MAX_READ_LINES = 150
MAX_OUTPUT_CHARS = 3000

# Limits on the edit tool
MAX_EDITS_PER_CALL = 10
MAX_EDITS_PER_RUN = 30
MAX_EDIT_CHARS = 2000