"""Tool registry. To add a tool: define it in a module, then list it here."""
from ..config import MAX_OUTPUT_CHARS
from .files import LIST_FILES, READ_FILE, SEARCH
from .findings import SUBMIT_FINDINGS
from .verify import RUN_TESTS

TOOLS = {t.name: t for t in (LIST_FILES, READ_FILE, SEARCH, RUN_TESTS, SUBMIT_FINDINGS)}


def schemas():
    return [t.schema() for t in TOOLS.values()]


def execute(name, args, ctx):
    """Run a tool the model asked for. Never raises: errors go back to the model as text."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"error: unknown tool '{name}'"
    try:
        result = tool.func(ctx, **args)
    except TypeError as e:
        return f"error: bad arguments: {e}"
    except Exception as e:
        return f"error: {e}"
    if len(result) > MAX_OUTPUT_CHARS:
        result = result[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
    return result