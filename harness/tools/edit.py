import re

from .. import config
from ..sandbox import relative, safe_path, source_files
from .base import Tool
from .files import numbered
from .verify import run_pytest

# Heuristic screen for code that reaches outside the project when the tests import it.
# It is a speed bump, not a sandbox: real isolation needs a container.
_FORBIDDEN = re.compile(
    r"\b(?:import|from)\s+(?:os|sys|subprocess|socket|shutil|pathlib|ctypes|requests|urllib|http|importlib|builtins)\b"
    r"|\b(?:open|eval|exec|compile|__import__)\s*\("
)


def replace_in_file(ctx, path, edits):
    if not isinstance(edits, list) or not edits:
        return "error: 'edits' must be a non-empty list of {old, new} objects"
    if len(edits) > config.MAX_EDITS_PER_CALL:
        return f"error: at most {config.MAX_EDITS_PER_CALL} edits per call"
    if ctx.edits_made + len(edits) > config.MAX_EDITS_PER_RUN:
        return f"error: edit limit reached ({config.MAX_EDITS_PER_RUN} per run). Submit your findings."

    target = safe_path(ctx.root, path)
    rel = relative(ctx.root, target)
    editable = source_files(ctx.root)
    if rel not in editable:
        return f"error: '{rel}' cannot be edited. Only these files can be changed: {', '.join(editable)}"
    if rel not in ctx.files_read:
        return f"error: read {rel} with read_file before editing it"

    text = target.read_text(encoding="utf-8")
    for i, e in enumerate(edits):
        if not isinstance(e, dict) or not isinstance(e.get("old"), str) or not isinstance(e.get("new"), str):
            return f"error: edit {i} must be an object with string fields 'old' and 'new'"
        old, new = e["old"], e["new"]
        if not old:
            return f"error: edit {i}: 'old' must not be empty"
        if len(old) > config.MAX_EDIT_CHARS or len(new) > config.MAX_EDIT_CHARS:
            return f"error: edit {i}: keep 'old' and 'new' under {config.MAX_EDIT_CHARS} characters"
        if _FORBIDDEN.search(new):
            return (f"error: edit {i}: that code is not allowed "
                    "(imports of os/sys/subprocess/network modules, open, eval, exec)")
        count = text.count(old)
        if count != 1:
            # include the file's current text so the retry needs no extra read
            return (f"error: edit {i}: 'old' matches {count} places in {rel}; it must match exactly once, "
                    "and must not include the line-number prefixes. Nothing was changed.\n"
                    f"Current text of {rel}:\n{numbered(target)}")
        text = text.replace(old, new, 1)

    try:
        compile(text, rel, "exec")
    except SyntaxError as err:
        return (f"error: those edits would leave {rel} with a syntax error "
                f"({err.msg}, line {err.lineno}). Nothing was changed.")

    target.write_text(text, encoding="utf-8")
    ctx.edits_made += len(edits)
    output, passed = run_pytest(ctx)  # verification loop: every edit is tested immediately
    status = "all visible tests pass" if passed else "some visible tests fail"
    return (f"Applied {len(edits)} edit(s) to {rel}. Automatic test run: {status}.\n{output}\n"
            f"Current text of {rel}:\n{numbered(target)}")


REPLACE_IN_FILE = Tool(
    name="replace_in_file",
    description=(
        "Edit a source file you have already read. Each edit replaces the text 'old' with 'new'; "
        "'old' must match exactly once. Tests run automatically afterwards, and the result shows "
        "the file's current text."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"old": {"type": "string"}, "new": {"type": "string"}},
                    "required": ["old", "new"],
                },
            },
        },
        "required": ["path", "edits"],
    },
    func=replace_in_file,
)