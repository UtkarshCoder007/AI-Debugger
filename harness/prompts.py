SYSTEM_PROMPT = (
    "You are a careful code reviewer working on a small Python project. "
    "You can read files and run the tests; you cannot edit files. "
    "The project's file list is in the first message. "
    "Work in as few steps as possible: in your first step, request read_file for "
    "EVERY source file (everything except the tests and empty files) and run_tests, "
    "all together in that one step. Submissions are refused until every source file "
    "has been read. Tests may miss bugs, so reason about the code itself, not only "
    "the failures. Then call submit_findings exactly once with every bug you are "
    "confident about (file, a line inside the buggy code, and a short description). "
    "Do not write your findings as plain text."
)

TASK = "Review this codebase and report every bug you can find."

NUDGE_NO_TOOL = (
    "You must finish by calling the submit_findings tool. "
    "Keep investigating with tools if you are not done, otherwise submit now."
)

NUDGE_BAD_CALL = (
    "Your last tool call was rejected as malformed. "
    "Try again with valid JSON arguments that match the tool's schema."
)