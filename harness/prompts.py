from . import config

_BASE = (
    "You are a careful code reviewer working on a small Python project. "
    "You can only inspect the code and run its tests; you cannot edit files. "
    "Use list_files first, read code in small slices, and run the tests. "
    "Tests may miss bugs, so reason about the code itself, not only the failures. "
    "When you are finished, call submit_findings exactly once with every bug you "
    "are confident about (file, a line inside the buggy code, and a short "
    "description). Do not write your findings as plain text."
)

_NOTES = (
    " File contents you have already read are removed from your view as you go, but your "
    "notes are always kept. After reading each file, call add_note to record any bug you "
    "found (file, line, why) and a one-line summary of what each function does and what it "
    "calls, so you can still reason about it later. Build your final submit_findings from "
    "your notes."
)


def system_prompt():
    return _BASE + (_NOTES if config.USE_NOTES else "")


TASK = "Review this codebase and report every bug you can find."

NUDGE_NO_TOOL = (
    "You must finish by calling the submit_findings tool. "
    "Keep investigating with tools if you are not done, otherwise submit now."
)

NUDGE_BAD_CALL = (
    "Your last tool call was rejected as malformed. "
    "Try again with valid JSON arguments that match the tool's schema."
)