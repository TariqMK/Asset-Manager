"""
Manual update check: asks GitHub for the latest published release and
compares it with this build's version. Runs only when the user selects
the version number; sends one GET and keeps nothing.
"""
import json
import re
import urllib.error
import urllib.request

APP_NAME = "Asset Manager"
REPO = "TariqMK/Asset-Manager"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
TIMEOUT_S = 10

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


class UpdateCheckError(Exception):
    """A failed check, with a message written for the user."""


def parse_version(text):
    """(1, 2, 3) for "v1.2.3" or "1.2.3"; None for anything else (e.g. "dev")."""
    match = _VERSION_RE.match((text or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def display(version_tuple):
    return "v" + ".".join(str(n) for n in version_tuple)


def safe_release_url(url):
    """Only an https:// link from the response is opened; else the releases list."""
    if isinstance(url, str) and url.startswith("https://"):
        return url
    return RELEASES_PAGE


def _fetch(current_version):
    request = urllib.request.Request(
        LATEST_URL,
        headers={
            "User-Agent": f"AssetManager/{current_version}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return response.read()


def check(current_version, fetch=_fetch):
    """Return the result for the dialog, or raise UpdateCheckError.

    Result: {"status": "newer" | "current" | "dev", "current", "latest",
    "url", "notes"}.
    """
    try:
        raw = fetch(current_version)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise UpdateCheckError(f"No {APP_NAME} releases are published yet.") from e
        if e.code in (403, 429):
            raise UpdateCheckError(
                "GitHub limits how often it can be checked. Try again in an hour."
            ) from e
        raise UpdateCheckError(f"GitHub answered with error {e.code}. Try again later.") from e
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", None) or e
        raise UpdateCheckError(
            f"Can't reach GitHub: {reason}. Check the internet connection."
        ) from e

    unreadable = UpdateCheckError(f"GitHub sent an answer {APP_NAME} can't read. Try again later.")
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as e:
        raise unreadable from e
    if not isinstance(data, dict):
        raise unreadable
    latest = parse_version(data.get("tag_name"))
    if latest is None:
        raise unreadable

    current = parse_version(current_version)
    if current is None:
        status = "dev"
    elif latest > current:
        status = "newer"
    else:
        status = "current"

    notes = data.get("body")
    return {
        "status": status,
        "current": display(current) if current else str(current_version),
        "latest": display(latest),
        "url": safe_release_url(data.get("html_url")),
        "notes": notes if isinstance(notes, str) else "",
    }
