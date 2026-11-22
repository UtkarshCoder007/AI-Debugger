"""Guardrails for filesystem access and subprocesses. Every tool goes through here."""
import os

_SECRET_WORDS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "GROQ")


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
    Computed from the workspace itself, never from the answer key. These are also the
    only files the agent is allowed to edit."""
    out = []
    for p in iter_py_files(root):
        rel = relative(root, p)
        if "tests" in rel.split("/")[:-1] or not p.read_text(encoding="utf-8").strip():
            continue
        out.append(rel)
    return out


def scrubbed_env():
    """Environment for subprocesses that run model-written code: anything that looks like
    a secret (including your Groq key) is removed."""
    env = {k: v for k, v in os.environ.items() if not any(w in k.upper() for w in _SECRET_WORDS)}
    env["COLUMNS"] = "200"  # keeps pytest's summary lines from being cut off
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env

def test_files(root):
    """Workspace-relative paths of the project's test files (read-only for the agent)."""
    out = []
    for p in iter_py_files(root):
        rel = relative(root, p)
        if "tests" in rel.split("/")[:-1] and p.read_text(encoding="utf-8").strip():
            out.append(rel)
    return out