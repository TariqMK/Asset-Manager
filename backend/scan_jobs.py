"""
Background scans with a live log.

Scanning a big folder (thumbnails for every image) can take a while, so
scans run on a worker thread instead of inside the HTTP request. The UI
polls status() to show a small scan log while it works.

Only one scan runs at a time -- start() refuses while one is running --
so two scans can never write the same index shard at once.
"""
import threading
import time

_lock = threading.Lock()
_job = None  # the current / most recent scan, see start()

_MAX_LINES = 200


class ScanBusy(Exception):
    pass


def start(label, fn):
    """Runs fn(progress) on a worker thread. fn does the actual scan and
    returns its summary (or list of summaries); progress is the callback
    library.scan_root() and friends report to. Raises ScanBusy if a scan
    is already running."""
    global _job
    with _lock:
        if _job and _job["running"]:
            raise ScanBusy("A scan is already running")
        job = {
            "id": (_job["id"] + 1) if _job else 1,
            "label": label,
            "running": True,
            "lines": [],
            "progress": None,
            "summaries": None,
            "error": None,
        }
        _job = job

    def progress(message, done=None, total=None, current=None):
        with _lock:
            if message is not None:
                job["lines"].append(message)
                del job["lines"][:-_MAX_LINES]
            if total is not None:
                job["progress"] = {"done": done, "total": total, "current": current}

    def run():
        started = time.monotonic()
        try:
            result = fn(progress)
            summaries = result if isinstance(result, list) else [result]
            added = sum(s.get("added", 0) for s in summaries)
            missing = sum(s.get("newly_missing", 0) for s in summaries)
            progress(
                f"Done in {time.monotonic() - started:.1f}s -- "
                f"{added} new, {missing} newly missing"
            )
            with _lock:
                job["summaries"] = summaries
        except Exception as e:  # surface it in the log instead of a silent dead thread
            progress(f"Scan failed: {e}")
            with _lock:
                job["error"] = str(e)
        finally:
            with _lock:
                job["running"] = False
                job["progress"] = None

    threading.Thread(target=run, daemon=True).start()
    return job["id"]


def status():
    with _lock:
        if _job is None:
            return {"id": None, "running": False, "lines": []}
        return {
            "id": _job["id"],
            "label": _job["label"],
            "running": _job["running"],
            "lines": list(_job["lines"]),
            "progress": dict(_job["progress"]) if _job["progress"] else None,
            "summaries": _job["summaries"],
            "error": _job["error"],
        }
