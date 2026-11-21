SYSTEM_PROMPT = (
    "You are a careful engineer fixing bugs in a small Python project. "
    "The project's file list is in the first message. Work in as few steps as possible. "
    "In your first step, request read_file for EVERY source file (everything except the "
    "tests and empty files) and run_tests, all together in that one step. "
    "Tests may miss bugs, so reason about the code itself, not only the failures. "
    "Fix each bug you find with replace_in_file (several edits to one file can go in one "
    "call); the tests run automatically after every edit. You cannot change the tests. "
    "Do not make unrelated changes. When you are done, call submit_findings exactly once, "
    "listing every bug you found (file, a line inside the buggy code as numbered in your "
    "first read, before any edits, and a short description), whether or not you managed "
    "to fix it. Submissions are refused until every source file has been read. "
    "Do not write your findings as plain text."
)

TASK = "Find and fix every bug in this codebase, then report them."

NUDGE_NO_TOOL = (
    "You must finish by calling the submit_findings tool. "
    "Keep working with tools if you are not done, otherwise submit now."
)

NUDGE_BAD_CALL = (
    "Your last tool call was rejected as malformed. "
    "Try again with valid JSON arguments that match the tool's schema."
)

NUDGE_BUDGET = (
    "You have used {used} of your {budget} token budget. "
    "Wrap up now: call submit_findings with the bugs you have found so far."
)