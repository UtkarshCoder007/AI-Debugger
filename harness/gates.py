"""Rules the harness enforces before it accepts that the agent is finished.
Each gate returns an error message for the model, or None if the agent may proceed."""
from . import config
from .sandbox import source_files


def coverage_problem(ctx):
    """The agent may not submit until it has opened every source file."""
    if not config.REQUIRE_FULL_COVERAGE:
        return None
    unread = [f for f in source_files(ctx.root) if f not in ctx.files_read]
    if not unread:
        return None
    return (
        f"error: you have not read these source files yet: {', '.join(unread)}. "
        "Read them with read_file, then call submit_findings again."
    )