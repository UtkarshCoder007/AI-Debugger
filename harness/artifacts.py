import difflib
import shutil

from .config import FIXTURES_DIR
from .sandbox import source_files


def write_changes(fixture, ctx):
    """Save what the agent changed: the modified files plus one readable diff.
    Written for every run, including runs that were cut short."""
    original = FIXTURES_DIR / fixture / "project"
    out = ctx.run_dir / "changes"
    diff_lines = []
    changed = []
    for rel in source_files(ctx.root):
        if not (original / rel).exists():
            continue
        before = (original / rel).read_text(encoding="utf-8").splitlines(keepends=True)
        after = (ctx.root / rel).read_text(encoding="utf-8").splitlines(keepends=True)
        if before == after:
            continue
        changed.append(rel)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ctx.root / rel, dest)
        diff_lines += difflib.unified_diff(before, after, f"original/{rel}", f"fixed/{rel}")
    if changed:
        (out / "fix.diff").write_text("".join(diff_lines), encoding="utf-8")
    return changed