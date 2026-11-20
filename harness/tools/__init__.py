"""Tool registry. To add a tool: define it in a module, then list it in active_tools()."""
from .. import config
from .files import LIST_FILES, READ_FILE, SEARCH
from .findings import SUBMIT_FINDINGS
from .notes import ADD_NOTE
from .verify import RUN_TESTS


def active_tools():
    tools = [LIST_FILES, READ_FILE, SEARCH, RUN_TESTS, SUBMIT_FINDINGS]
    if config.USE_NOTES:
        tools.append(ADD_NOTE)
    return {t.name: t for t in tools}


def schemas():
    return [t.schema() for t in active_tools().values()]


def execute(name, args, ctx):
    """Run a tool the model asked for. Never raises: errors go back to the model as text."""
    tool = active_tools().get(name)
    if tool is None:
        return f"error: unknown tool '{name}'"
    try:
        result = tool.func(ctx, **args)
    except TypeError as e:
        return f"error: bad arguments: {e}"
    except Exception as e:
        return f"error: {e}"
    if len(result) > config.MAX_OUTPUT_CHARS:
        result = result[:config.MAX_OUTPUT_CHARS] + "\n[output truncated]"
    return result