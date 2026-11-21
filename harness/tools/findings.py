from .. import gates
from ..sandbox import relative, safe_path
from .base import Tool


def submit_findings(ctx, findings):
    """Validate the final answer. Nothing malformed is ever accepted: the model gets a
    specific error and must try again, so every finished run has a gradable result."""
    problem = gates.coverage_problem(ctx)
    if problem:
        ctx.gate_rejections += 1
        return problem
    if not isinstance(findings, list):
        return "error: findings must be a list"
    clean = []
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            return f"error: finding {i} must be an object with file, line, description"
        file, line, desc = f.get("file"), f.get("line"), f.get("description")
        if not isinstance(file, str) or not file:
            return f"error: finding {i}: 'file' must be a non-empty string"
        path = safe_path(ctx.root, file)
        if not path.is_file():
            return f"error: finding {i}: file '{file}' does not exist. Valid paths are in the first message."
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            return f"error: finding {i}: 'line' must be a positive integer"
        n_lines = len(path.read_text(encoding="utf-8").splitlines())
        if line > n_lines:
            return f"error: finding {i}: {file} has only {n_lines} lines"
        if not isinstance(desc, str) or not desc.strip():
            return f"error: finding {i}: 'description' must be a non-empty string"
        clean.append({"file": relative(ctx.root, path), "line": line, "description": desc.strip()})
    ctx.findings = clean
    return f"Findings recorded ({len(clean)}). The review is complete."


SUBMIT_FINDINGS = Tool(
    name="submit_findings",
    description="Submit the final bug list. Call exactly once, when done.",
    parameters={
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "description": {"type": "string"},
                    },
                    "required": ["file", "line", "description"],
                },
            }
        },
        "required": ["findings"],
    },
    func=submit_findings,
)