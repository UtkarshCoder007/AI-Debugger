import re

from ..config import MAX_READ_LINES, PRELOAD_MAX_CHARS
from ..sandbox import iter_py_files, relative, safe_path, source_files
from .base import Tool


def list_files(ctx):
    out = []
    for p in iter_py_files(ctx.root):
        text = p.read_text(encoding="utf-8")
        names = re.findall(r"^(?:def|class) (\w+)", text, re.M)
        out.append(
            f"{relative(ctx.root, p)} ({len(text.splitlines())} lines) "
            f"defines: {', '.join(names) or '-'}"
        )
    return "\n".join(out)


def preload_sources(ctx):
    """Full text of every source file with line numbers, or None if the project is too big.
    Files included this way count as read: the agent has seen every line of them."""
    texts = {rel: (ctx.root / rel).read_text(encoding="utf-8") for rel in source_files(ctx.root)}
    if sum(len(t) for t in texts.values()) > PRELOAD_MAX_CHARS:
        return None
    parts = []
    for rel, text in texts.items():
        lines = text.splitlines()
        body = "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))
        parts.append(f"=== {rel} ({len(lines)} lines) ===\n{body}")
        ctx.files_read.add(rel)
    return "\n\n".join(parts)


def read_file(ctx, path, start_line=1, end_line=None):
    p = safe_path(ctx.root, path)
    lines = p.read_text(encoding="utf-8").splitlines()
    start = max(1, int(start_line))
    if start > len(lines):
        return f"error: file has only {len(lines)} lines"
    ctx.files_read.add(relative(ctx.root, p))  # the harness tracks what the agent has seen
    last_allowed = start + MAX_READ_LINES - 1
    end = min(len(lines), int(end_line) if end_line else last_allowed, last_allowed)
    body = "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))
    return f"{body}\n[showing lines {start}-{end} of {len(lines)}]"


READ_FILE = Tool(
    name="read_file",
    description=f"Read a file with line numbers (max {MAX_READ_LINES} lines per call).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "e.g. shop/inventory.py"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
        },
        "required": ["path"],
    },
    func=read_file,
)