"""
Atomic JSON storage helpers.

Every write goes to a temp file in the same directory, then gets renamed
over the target. os.replace() is atomic on both Windows and POSIX, so a
crash or power loss mid-write can never leave a half-written, corrupted
JSON file behind -- worst case you lose the write, never the file.

On Windows, sync clients (OneDrive, Dropbox) and antivirus scanners
briefly open files they've just seen change. While they hold the file,
os.replace() and open() fail with PermissionError (WinError 5 / 32)
even though nothing is actually wrong. Both are retried with a short
backoff (~2s total) before giving up, so a sync pass over library_data/
doesn't turn into a failed tag edit.
"""
import json
import os
import tempfile
import time

_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.3, 0.5, 0.8)


def _with_retry(fn):
    """Runs fn(), retrying on PermissionError (a transient lock held by
    another process). The final failure is re-raised as-is."""
    for delay in _RETRY_DELAYS:
        try:
            return fn()
        except PermissionError:
            time.sleep(delay)
    return fn()


def read_json(path, default=None):
    """Read a JSON file, returning `default` if it doesn't exist yet."""
    if not os.path.exists(path):
        return default

    def _read():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return _with_retry(_read)


def write_json(path, data):
    """Atomically write `data` as pretty JSON to `path`."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        _with_retry(lambda: os.replace(tmp_path, path))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
