"""Guardrails for filesystem access. Every tool goes through here."""


def safe_path(root, rel):
    """Resolve a model-supplied path and refuse anything outside the workspace."""
    root = root.resolve()
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise ValueError("path is outside the project folder")
    return p


def relative(root, p):
    """Workspace-relative path with forward slashes, e.g. shop/inventory.py."""
    return p.resolve().relative_to(root.resolve()).as_posix()


def iter_py_files(root):
    """All Python files in the workspace, sorted, ignoring caches."""
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" not in p.parts:
            yield p

def source_files(root):
    """Workspace-relative paths of the project's real source code: no tests, no empty files.
    Computed from the workspace itself, never from the answer key."""
    out = []
    for p in iter_py_files(root):
        rel = relative(root, p)
        if "tests" in rel.split("/")[:-1] or not p.read_text(encoding="utf-8").strip():
            continue
        out.append(rel)
    return out