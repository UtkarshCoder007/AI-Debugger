import json
import time
from pathlib import Path


class RunLog:
    """Append-only JSON-lines log of everything that happens in one run."""

    def __init__(self, path):
        self.path = Path(path)
        self._start = time.time()

    def event(self, kind, **data):
        record = {"t": round(time.time() - self._start, 2), "event": kind, **data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")