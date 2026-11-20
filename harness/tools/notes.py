from .. import config
from .base import Tool


def add_note(ctx, text):
    """The agent's long-term memory. Notes survive pruning, so the model can write down
    what it learned from a file before that file's contents are removed from its view."""
    if not isinstance(text, str) or not text.strip():
        return "error: 'text' must be a non-empty string"
    if len(text) > config.MAX_NOTE_CHARS:
        return f"error: note is {len(text)} characters; keep it under {config.MAX_NOTE_CHARS}"
    if len(ctx.notes) >= config.MAX_NOTES:
        return f"error: you already have {config.MAX_NOTES} notes; stop noting and submit your findings"
    ctx.notes.append(text.strip())
    return f"Note {len(ctx.notes)} saved."


ADD_NOTE = Tool(
    name="add_note",
    description=(
        "Save a short note to your permanent memory. Notes are never removed from your view, "
        "unlike file contents. Use it for bugs you found (file, line, why) and for one-line "
        "summaries of what each function does and calls."
    ),
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    func=add_note,
)