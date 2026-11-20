import shutil
import uuid
from datetime import datetime

from .config import FIXTURES_DIR, RUNS_DIR
from .context import RunContext


def create_run(fixture):
    """Copy the pristine fixture into a fresh workspace.
    The answer key lives next to the fixture's project folder, so it is never copied."""
    source = FIXTURES_DIR / fixture / "project"
    if not source.is_dir():
        raise FileNotFoundError(f"fixture not found: {source}")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    run_dir = RUNS_DIR / run_id
    workspace = run_dir / "workspace"
    shutil.copytree(
        source, workspace,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    return run_dir, RunContext(root=workspace.resolve(), run_dir=run_dir)