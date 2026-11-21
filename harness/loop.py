import json

import openai

from . import config, tools
from .llm import call_model
from .prompts import NUDGE_BAD_CALL, NUDGE_NO_TOOL, SYSTEM_PROMPT, TASK
from .runlog import RunLog
from .workspace import create_run


def run_agent(fixture="shop_v1", verbose=True):
    """Run one review in a fresh workspace. Returns a summary dict (also saved to result.json)."""
    run_dir, ctx = create_run(fixture)
    log = RunLog(run_dir / "log.jsonl")
    log.event("run_start", model=config.MODEL, fixture=fixture)
    say = print if verbose else (lambda *a, **k: None)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TASK},
    ]
    schemas = tools.schemas()
    tokens = steps = 0
    status = "step_limit"

    try:
        for step in range(1, config.MAX_STEPS + 1):
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
            log.event("model_call", step=step, prompt_tokens=usage.prompt_tokens,
                      completion_tokens=usage.completion_tokens, total_tokens=usage.total_tokens)
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
                say(f"  tool: {tc.function.name}({args}) -> {len(output)} chars")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

            if ctx.findings is not None:
                status = "submitted"
                break
    except Exception as e:  # keep this run's record even if something unexpected breaks
        status = "error"
        log.event("error", message=f"{type(e).__name__}: {e}")

    result = {
        "run_id": run_dir.name,
        "status": status,
        "steps": steps,
        "tokens": tokens,
        "findings": ctx.findings or [],
        "files_read": sorted(ctx.files_read),
        "tests_run": ctx.tests_run,
        "gate_rejections": ctx.gate_rejections,
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.event("run_end", **{k: v for k, v in result.items() if k != "findings"})
    return result