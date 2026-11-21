import hashlib

from .config import FIXTURES_DIR, ROOT


def _hash_tree(folder):
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(p.relative_to(folder).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def snapshot():
    """Fingerprint of everything outside a run's workspace that must never change: the
    pristine fixtures and your .env file. Model-written code runs as you, so comparing
    this before and after a run is how we notice if it reached outside the workspace."""
    env_file = ROOT / ".env"
    return {
        "fixtures": _hash_tree(FIXTURES_DIR),
        "env_file": hashlib.sha256(env_file.read_bytes()).hexdigest() if env_file.exists() else None,
    }