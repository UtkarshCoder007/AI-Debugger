# AI Agent Debugger: a harness-engineering experiment

An LLM agent that reviews a small Python codebase, finds planted bugs, fixes them, and is graded
by hidden tests, built to learn **harness engineering**: everything around the model that makes
an agent reliable (tools, guardrails, verification, budgets, logging, and evaluation).

The model is fixed (`openai/gpt-oss-120b` on Groq's free tier). The experiments change the
**harness**, and every change is measured by a scorer against an answer key the agent can never
see. Nine versions are documented below, including the ones that failed.

## Headline results

On a 4-file project with 5 planted bugs, the final version (v9) fixes about 4 of 5 bugs per run
with no regressions and no tampering, at about 24k tokens per run.

| Version | Task | Runs | Bugs found (mean / 5) | Bugs fixed (mean / 5) | Mean tokens | Mean steps |
|---|---|---|---|---|---|---|
| v1 baseline | review | 5 | 2.4 | n/a | 5,794 | 5.6 |
| v2 coverage gate | review | 5 | 3.8 | n/a | 13,155 | 10 |
| v3 notes + pruning | review | 5 | 1.8 | n/a | 28,246 | 17 |
| v4 fewer calls | review | 5 | 4.0 | n/a | 9,336 | 7.2 |
| v5 fixing (low effort) | review + fix | 3 | 2.33 | 2.33 | 20,530 | 10.7 |
| v6 preloaded source | review + fix | 3 | 2.0 | 2.0 | 8,369 | 5 |
| v7 medium reasoning effort | review + fix | 2 | 5.0 | 4.5 | 25,634 | 10.5 |
| v8 multi-file edits | review + fix | 3 | 2.67* | 3.67 | 26,859 | 10 |
| **v9 lean tool results** | review + fix | 3 | 4.0 | 4.0 | 23,950 | 7.7 |

\* One v8 run hit the token budget before submitting, so it scored 0 found while still fixing 3 bugs.
Zero false positives in every batch. Zero regressions and zero tampered runs in every fixing batch.

Per-bug results ("found" for v1-v4, "fixed" for v5-v9):

| Bug | v1 | v2 | v3 | v4 | v5 | v6 | v7 | v8 | v9 |
|---|---|---|---|---|---|---|---|---|---|
| `remove_stock` rejects the exact remaining stock | 5/5 | 5/5 | 3/5 | 5/5 | 3/3 | 3/3 | 2/2 | 3/3 | 3/3 |
| bulk-discount tiers in the wrong order | 5/5 | 5/5 | 3/5 | 5/5 | 3/3 | 3/3 | 2/2 | 3/3 | 3/3 |
| `place_order` is not all-or-nothing | 2/5 | 0/5 | 0/5 | 1/5 | 0/3 | 0/3 | 1/2 | 1/3 | 2/3 |
| pagination off-by-one | 0/5 | 5/5 | 3/5 | 5/5 | 1/3 | 0/3 | 2/2 | 3/3 | 3/3 |
| average of an empty list | 0/5 | 4/5 | 0/5 | 4/5 | 0/3 | 0/3 | 2/2 | 1/3 | 1/3 |

**Read these numbers with care.** Samples are 2-5 runs per version on one fixture, the model is
non-deterministic, and the task changed from review-only (v1-v4) to review-and-fix (v5-v9), so
versions are only loosely comparable across that line. Differences of half a bug between versions
are within noise.

## How it works

```
task + project ─► model ─► tool call ─► harness validates and runs it ─► result ─► model ─► ...
                                              │
              guardrails · gates · token budget · run log · hidden-test grading
```

The model only ever *requests* actions. Our code decides what happens.

| Harness job | What it does here |
|---|---|
| Capabilities | Four tools: `read_file`, `run_tests`, `replace_in_file`, `submit_findings` |
| Guardrails | Path sandbox; only source files are editable (never tests or config); read-before-write; edits must match exactly once; syntax check before writing; a heuristic screen for dangerous code; edit-count and size limits |
| Verification | Tests run automatically after every edit and the result goes straight back to the model |
| Gates | `submit_findings` is refused until every source file has been read |
| Budget | A per-run token budget (default 25,000) with a warning at 80%; a run that exceeds it ends as `budget_exceeded` and its partial work is still graded |
| Context control | The whole project is preloaded into the first message when small; errors and edit results carry the file's current text so no re-read is needed |
| Isolation | Every run works in its own copy (`runs/<id>/workspace`); the fixture is never modified; `changes/fix.diff` shows what the agent changed |
| Safety checks | Secrets stripped from the test subprocess's environment; `.env` and the fixtures are hashed before and after each run to detect tampering |
| Observability | Every step is logged as JSON lines (tokens, tool calls, outputs) |
| Evaluation | A scorer runs N attempts and grades them against an answer key; fixes are graded by hidden tests the agent never sees |

## Version history

### v1: baseline and experiment rig
**Changed:** Built the measurement setup before any improvement: a pristine fixture with 5 planted
bugs, a private workspace per run, an answer key kept outside the agent's reach, a structured final
answer (`submit_findings`, validated and retried on malformed input), JSONL run logs, and a scorer.
Tools: `list_files`, `read_file`, `search`, `run_tests`, `submit_findings`.
**Why:** Two early unscored runs of the same agent on the same code found 4 of 5 bugs, then 2 of 5.
Without measurement there was no way to tell whether any change helped.
**Result:** 2.4/5 found, 5,794 tokens. Every run stopped after reading 3 files: 0% read every source
file and only 20% ran the tests, despite the prompt asking for both. Both bugs in `report.py` were
found 0 times.
**Lesson:** The prompt does not make the model thorough; the harness has to.

### v2: coverage gate
**Changed:** `submit_findings` is refused until the agent has opened every source file. The file
list is computed from the workspace at run time, never from the answer key.
**Result:** 3.8/5 found, 13,155 tokens. The gate fired once in every run and one nudge was always
enough. The two `report.py` bugs went from 0/5 to 5/5 and 4/5.
**Lesson:** The biggest early loss was the harness accepting "done" too early. The remaining
miss, `place_order`, is a reasoning miss that more reading did not fix.

### v3: notes and pruning (negative result)
**Changed:** An `add_note` tool for the agent's own memory, plus pruning that replaced all but the
2 newest file reads with one-line stubs.
**Result:** 1.8/5 found, 28,246 tokens, 17 steps. Two of five runs hit the 20-step cap and scored 0.
**Why it failed (from the run traces):**
- Thrashing: with room for 2 files in view and a 4-file project, the agent kept re-reading what it
  had just lost (re-reads per run: 6, 3, 10, 2, 0).
- The notes anchored the answer: the prompt said to build the submission from the notes, the notes
  held roughly one bug per file, and no note in any run mentioned the empty-list bug, which had been
  found 4/5 in v2.
- Per-call cost did not drop. The notes prompt and schema added about 139 tokens to every call.
- Pruning rewrites earlier messages, which breaks prefix caching (see lessons).
**Lesson:** The 4-file project is too small for context management to pay off, and a "memory"
feature can become a bottleneck.

### v4: fewer calls
**Changed:** Removed pruning and notes. Put the file list in the first message (dropping
`list_files` and `search`), shortened the tool schemas, and asked the model to request all reads
in one step.
**Result:** 4.0/5 found, 9,336 tokens, 7.2 steps: the best review result per token.
**Lesson:** Cost is roughly (number of calls) x (prompt size), so removing calls is the strongest
lever. Later, Groq's docs showed gpt-oss does not support parallel tool calls, so the "one step"
instruction could not have worked; the savings most likely came from the file map and the smaller
tool list.

### v5: fixing
**Changed:** The agent can now edit code. Added `replace_in_file(path, edits)` with exact-match-once
and read-before-write rules, an allowlist of editable files, automatic test runs after every edit,
the token budget with partial-result handling, scrubbed subprocess environment, integrity hashing,
`changes/fix.diff`, and grading by hidden tests (a bug counts as fixed only if all its hidden tests
pass; regressions are visible tests that passed originally and fail now). `check_fixture.py` proves
the grader works: the buggy code scores 0/5 and the reference solution scores 5/5.
**Result (low reasoning effort):** 2.33/5 fixed, 20,530 tokens, 10.7 steps. No regressions, no
tampering. Every bug the agent found, it fixed.
**Lesson:** The fixing machinery worked. The problem was finding bugs: asking for fixes made the
review worse (`average-empty-list` fell from 4/5 found in v4 to 0/3).

### v6: preload the source
**Changed:** When the source is small (under `PRELOAD_MAX_CHARS`), it goes into the first message in
full and counts as read.
**Result:** 2.0/5 fixed, 8,369 tokens, 5 steps. The three runs were nearly identical (8,387 /
8,297 / 8,424 tokens) and each fixed the same two bugs, the two that have failing visible tests.
**Lesson:** Much cheaper, but the agent appeared to treat the failing tests as its work list.

### v7: medium reasoning effort
**Changed:** One setting, `REASONING_EFFORT` from `low` to `medium`. This is a model setting, not a
harness change.
**Result:** 5/5 found in both runs, 4.5/5 fixed, 25,634 tokens, 10.5 steps.
**Lesson:** For recall, reasoning effort mattered more than any harness change tried before it. The
cost tripled mainly because the number of calls doubled; model output was only about 13% of tokens.
This version had just 2 runs, so treat 4.5 as indicative.

### v8: multi-file edits (negative result, reverted)
**Changed:** One `apply_edits` call taking edits across several files, applied all-or-nothing.
**Result:** 3.67/5 fixed, 26,859 tokens, 10 steps; one run exhausted its token budget (the budget
handling worked and the partial fixes were still graded).
**Why it did not help (from the traces):** The model still made 3-4 edit calls per run. It spent
1-2 calls reading the visible tests, re-read files it already had after editing, and lost calls to
rejected edits (one `'old'` text that matched nowhere, one unexpected `comment` argument that crashed
the tool).
**Lesson:** The traces pointed at wasted calls elsewhere, which led to v9.

### v9: lean tool results (final)
**Changed:** Built on v7's `replace_in_file`. The visible tests are preloaded (read-only) in the first
message. Every edit result returns the file's current numbered text, so no re-read is needed.
Mismatch errors include the current text. Unknown tool arguments are dropped instead of crashing.
**Result:** 4.0/5 found and fixed, 23,950 tokens, 7.7 steps, no regressions, no tampering.
Compared with v7: steps fell about 27% and tokens about 7%; the drop from 4.5 to 4.0 fixed is within
noise at 2-3 runs.

## What I learned

1. **The prompt does not make a model thorough; the harness does.** The coverage gate took
   "every source file read" from 0% to 100%, and recall from 2.4 to 3.8.
2. **Measure first.** Run-to-run variance (2/5 vs 4/5 on identical code) hid every early change until
   there was a scorer, an answer key, and multiple runs.
3. **A rejected design is still a result.** v3 and v8 failed for reasons the logs made clear.
4. **Cost is the number of calls, not the amount of reasoning.** Every call resends the whole
   conversation, so tokens are roughly calls x prompt size. Preloading and richer tool results won
   by removing calls.
5. **Check what the platform actually supports.** On Groq, gpt-oss-120b has no parallel tool calls and
   a forced-tool setting (`tool_choice=required`) is not reliably enforced (per Groq's docs and a
   Groq community post), so prompts and design that assumed otherwise were wasted.
6. **Prefix caching favors append-only conversations.** Groq's cache needs an exact prompt prefix, and
   pruning rewrites history. In v7 only 18% of prompt tokens were reported as cached; I did not
   investigate why.
7. **Grade fixes with hidden tests, not the visible ones.** Visible tests catch only 2 of the 5 bugs.
   The hidden tests also accept any reasonable behavior where the code never specified one (for the
   empty-list case, anything but a `ZeroDivisionError`).

## Limitations

- One fixture, 4 files and 5 planted bugs, and 2-5 runs per version. This is a learning project, not
  a benchmark. I would not read anything into half-a-bug differences.
- One model. Conclusions about the harness may not transfer to other models.
- The two reasoning-heavy bugs (`place_order` atomicity and the empty-list average) are still found
  and fixed inconsistently.
- **Model-written code runs on your machine** with your permissions. The guardrails (secret
  scrubbing, an allowlist of editable files, a heuristic code screen, integrity hashing) reduce the
  risk but are not a sandbox. For untrusted models, run it in a container.
- The free-tier limits on tokens per minute and per day shaped which experiments were practical.

## Project layout

```
agent.py              one attempt, with a graded summary
score.py              N attempts, graded, saved to results/
check_fixture.py      verifies the grader (no API calls)
profile.py            where the tokens went (from run logs, no API calls)
trace.py              step-by-step view of each run (no API calls)
cache_check.py        prompt-cache hit rate (no API calls)
harness/              config, sandbox, loop, tools/, gates, grader, fixgrader, integrity, ...
fixtures/shop_v1/     project/ (buggy code + visible tests), hidden_tests/, solution/, answer_key.json
results/              one JSON file per experiment (v1 ... v9)
runs/                 per-run workspace, log and changes (gitignored)
```

## Setup

Requires Python 3.10+ and a free [Groq](https://console.groq.com) API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env              # macOS/Linux: cp .env.example .env, then add your key
```

`.env` settings:

```
GROQ_API_KEY=your_key_here
MODEL=openai/gpt-oss-120b
REASONING_EFFORT=medium
TOKEN_BUDGET=25000
PRELOAD_MAX_CHARS=12000
```

The default in the code is `REASONING_EFFORT=low`; set `medium` to reproduce v7-v9.

## Usage

```powershell
python check_fixture.py                     # free: confirms the grader (buggy 0/5, reference 5/5)
python agent.py                             # one attempt (about 20-25k tokens)
python score.py --runs 3 --label my-test --pause 60 --batch-budget 70000
python profile.py my-test                   # token breakdown, free
python trace.py my-test                     # what each run did, free
```

An average run costs about 24k tokens, so check your own Groq limits before starting a batch. The
scorer's `--pause` spaces runs out for per-minute limits, and `--batch-budget` stops a batch early.
Each result file records the settings that produced it. Runs are non-deterministic, so expect
numbers to differ from the tables above.

## Status

Finished as a learning project. Possible next steps: a second, larger fixture to test whether the
gains generalize, a two-phase design (review, then fix), and container isolation for model-written code.