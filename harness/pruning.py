"""Keeps what the model sees small by replacing old, bulky tool results with one-line stubs."""
PRUNABLE_TOOLS = {"read_file", "search"}


def prune_history(messages, keep_recent, mention_notes=False):
    """Return (view, pruned_count).
    `view` is a copy of the conversation in which every prunable tool result except the
    newest `keep_recent` is replaced by a stub. The original list is never modified, so the
    real history and the logs stay complete."""
    calls = {}  # tool_call_id -> (tool name, raw arguments)
    for m in messages:
        for tc in m.get("tool_calls") or []:
            calls[tc["id"]] = (tc["function"]["name"], tc["function"]["arguments"])

    prunable = [
        i for i, m in enumerate(messages)
        if m["role"] == "tool" and calls.get(m["tool_call_id"], ("",))[0] in PRUNABLE_TOOLS
    ]
    to_stub = set(prunable[:-keep_recent]) if keep_recent > 0 else set(prunable)

    view = []
    for i, m in enumerate(messages):
        if i in to_stub:
            name, args = calls[m["tool_call_id"]]
            kept = " Your notes are still available." if mention_notes else ""
            stub = (f"[{name}({args}) result removed to save tokens "
                    f"({len(m['content'])} chars).{kept} Call {name} again if you need it.]")
            view.append({**m, "content": stub})
        else:
            view.append(m)
    return view, len(to_stub)