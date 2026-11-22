import json

import openai

from . import config, integrity, tools
from .artifacts import write_changes
from .fixgrader import grade_fix
from .grader import load_key
from .llm import call_model
from .prompts import NUDGE_BAD_CALL, NUDGE_BUDGET, NUDGE_NO_TOOL, SYSTEM_PROMPT, TASK
from .runlog import RunLog
from .tools.files import list_files, preload_project
from .workspace import create_run


def run_agent(fixture="shop_v1", verbose=True):
    """Run one fix attempt in a fresh workspace. Returns a summary dict (also saved to result.json)."""
    run_dir, ctx = create_run(fixture)
    log = RunLog(run_dir / "log.jsonl")
    outside_before = integrity.snapshot()
    log.event("run_start", model=config.MODEL, fixture=fixture, token_budget=config.TOKEN_BUDGET)
    say = print if verbose else (lambda *a, **k: None)

    # small projects go into the first message in full, so the agent skips the reading calls
    preloaded = preload_project(ctx)
    if preloaded:
        task_message = f"{TASK}\n\nThe whole project, with line numbers:\n\n{preloaded}"
    else:
        task_message = f"{TASK}\n\nProject files (open them with read_file):\n{list_files(ctx)}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task_message},
    ]
    schemas = tools.schemas()
    tokens = steps = 0
    status = "step_limit"
    budget_message = None
    warned = False

    try:
        for step in range(1, config.MAX_STEPS + 1):
            if tokens >= config.TOKEN_BUDGET:
                status = "budget_exceeded"
                budget_message = (f"Token budget exceeded: used {tokens} of {config.TOKEN_BUDGET}. "
                                  "The run was stopped; partial results are kept.")
                log.event("budget_exceeded", used=tokens, budget=config.TOKEN_BUDGET)
                say(f"\n{budget_message}")
                break
            if not warned and tokens >= config.BUDGET_WARN_FRACTION * config.TOKEN_BUDGET:
                warned = True
                messages.append({"role": "user",
                                 "content": NUDGE_BUDGET.format(used=tokens, budget=config.TOKEN_BUDGET)})
                log.event("budget_warning", used=tokens, budget=config.TOKEN_BUDGET)
            steps = step

            try:
                resp = call_model(messages, schemas)
            except openai.BadRequestError as e:
                # the model produced a tool call the API refused: tell it and let it retry
                log.event("bad_request", step=step, message=str(e)[:500])
                say(f"\n[step {step}] malformed tool call, asking the model to retry")
                messages.append({"role": "user", "content": NUDGE_BAD_CALL})
                continue

            msg = resp.choices[0].message
            usage = resp.usage
            tokens += usage.total_tokens
            details = getattr(usage, "prompt_tokens_details", None)
            cached = getattr(details, "cached_tokens", 0) or 0  # Groq does not count these toward rate limits
            log.event("model_call", step=step, prompt_tokens=usage.prompt_tokens,
                      completion_tokens=usage.completion_tokens, total_tokens=usage.total_tokens,
                      cached_tokens=cached)
            say(f"\n[step {step}] this call: {usage.total_tokens} tokens | run total: {tokens}")

            if not msg.tool_calls:
                # the model tried to finish in plain text; the harness does not accept that
                log.event("nudge", step=step, content=msg.content)
                say("  model answered in plain text, sending it back to use submit_findings")
                messages.append({"role": "assistant", "content": msg.content or "(no content)"})
                messages.append({"role": "user", "content": NUDGE_NO_TOOL})
                continue

            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                    output = tools.execute(tc.function.name, args, ctx)
                except json.JSONDecodeError:
                    args = {}
                    output = "error: arguments were not valid JSON"
                log.event("tool", step=step, name=tc.function.name, args=args, output=output)
                say(f"  tool: {tc.function.name} -> {len(output)} chars")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

            if ctx.findings is not None:
                status = "submitted"
                break
    except Exception as e:  # keep this run's record even if something unexpected breaks
        status = "error"
        log.event("error", message=f"{type(e).__name__}: {e}")

    # everything below runs for every run, including ones cut short: partial results are kept
    changed = write_changes(fixture, ctx)
    try:
        fix = grade_fix(fixture, ctx.root, load_key(fixture))
    except Exception as e:  # a broken fixture must not lose the run's record
        log.event("grading_error", message=f"{type(e).__name__}: {e}")
        fix = {"bugs_fixed": [], "bugs_not_fixed": [], "regressions": [], "suite_ran": False,
               "tampered": False, "grading_error": f"{type(e).__name__}: {e}"}
    if integrity.snapshot() != outside_before:
        fix["tampered"] = True
        fix["outside_files_changed"] = True

    result = {
        "run_id": run_dir.name,
        "status": status,
        "budget_message": budget_message,
        "token_budget": config.TOKEN_BUDGET,
        "steps": steps,
        "tokens": tokens,
        "findings": ctx.findings or [],
        "files_read": sorted(ctx.files_read),
        "tests_run": ctx.tests_run,
        "gate_rejections": ctx.gate_rejections,
        "edits_made": ctx.edits_made,
        "changed_files": changed,
        "fix": fix,
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.event("run_end", **{k: v for k, v in result.items() if k != "findings"})
    return result