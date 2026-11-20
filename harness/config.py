"""All settings in one place. Nothing else in the project reads environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures"  # pristine projects + answer keys, never edited
RUNS_DIR = ROOT / "runs"          # one folder per run: workspace, log, result
RESULTS_DIR = ROOT / "results"    # scorer output, one file per labelled experiment

API_KEY = os.environ["GROQ_API_KEY"]
BASE_URL = "https://api.groq.com/openai/v1"
MODEL = os.environ.get("MODEL", "openai/gpt-oss-120b")
REASONING_EFFORT = "low"

# Harness rules. Each is a switch so any experiment can be reproduced or compared.
REQUIRE_FULL_COVERAGE = True  # submit_findings is refused until every source file was read
USE_NOTES = True              # the agent gets an add_note tool and is told to use it
PRUNE_OLD_TOOL_RESULTS = True # old read_file/search results are replaced by short stubs
KEEP_RECENT_RESULTS = 2       # how many of the newest such results stay in full
MAX_NOTES = 30
MAX_NOTE_CHARS = 400
MAX_STEPS = 20
MAX_READ_LINES = 150
MAX_OUTPUT_CHARS = 3000