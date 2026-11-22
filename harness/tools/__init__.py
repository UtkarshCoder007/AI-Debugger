"""Tool registry. To add a tool: define it in a module, then list it here."""
import inspect

from ..config import MAX_OUTPUT_CHARS
from .edit import REPLACE_IN_FILE
from .files import READ_FILE
from .findings import SUBMIT_FINDINGS
from .verify import RUN_TESTS

TOOLS = {t.name: t for t in (READ_FILE, RUN_TESTS, REPLACE_IN_FILE, SUBMIT_FINDINGS)}


def schemas():
    return [t.schema() for t in TOOLS.values()]


def execute(name, args, ctx):
    """Run a tool the model asked for. Never raises: errors go back to the model as text."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"error: unknown tool '{name}'"
    if not isinstance(args, dict):
        return "error: arguments must be a JSON object"
    # Models sometimes add fields the schema does not have (a "comment", say). Dropping
    # them is harmless and saves a whole call that would otherwise end in a crash.
    accepted = set(inspect.signature(tool.func).parameters) - {"ctx"}
    args = {k: v for k, v in args.items() if k in accepted}
    try:
        result = tool.func(ctx, **args)
    except TypeError as e:
        return f"error: bad arguments: {e}"
    except Exception as e:
        return f"error: {e}"
    if len(result) > MAX_OUTPUT_CHARS:
        result = result[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
    return result