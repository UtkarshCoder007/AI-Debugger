from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunContext:
    """Everything the tools need to know about the current run.
    Tools read the workspace location from here and record what the agent did."""

    root: Path                  # this run's private copy of the project
    run_dir: Path               # where this run's log and result are written
    findings: list | None = None            # set once submit_findings succeeds
    files_read: set = field(default_factory=set)
    tests_run: int = 0
    gate_rejections: int = 0  # how often a harness gate refused the agent's attempt to finish