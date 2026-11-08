"""
Offline tests for the manual update check: version parsing and comparison,
reading a GitHub response, URL safety and every user-facing error message.
The HTTP call is stubbed; nothing here touches the network.
"""
import io
import json
import os
import sys
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import update_check as uc  # noqa: E402


def response(tag="v1.4.0", url="https://github.com/TariqMK/Asset-Manager/releases/tag/v1.4.0", body="Notes"):
    return lambda _version: json.dumps({"tag_name": tag, "html_url": url, "body": body}).encode()


def failing(exc):
    def fetch(_version):
        raise exc
    return fetch


def http_error(code):
    return urllib.error.HTTPError(uc.LATEST_URL, code, "err", {}, io.BytesIO(b""))


class VersionTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(uc.parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(uc.parse_version("1.2.3"), (1, 2, 3))
        self.assertIsNone(uc.parse_version("dev"))
        self.assertIsNone(uc.parse_version("v1.2"))
        self.assertIsNone(uc.parse_version("v1.2.3-beta"))
        self.assertIsNone(uc.parse_version(None))

    def test_numeric_comparison(self):
        self.assertGreater(uc.parse_version("0.10.0"), uc.parse_version("0.9.0"))
        r = uc.check("0.9.0", fetch=response(tag="v0.10.0"))
        self.assertEqual(r["status"], "newer")


class ResultTests(unittest.TestCase):
    def test_newer(self):
        r = uc.check("1.3.9", fetch=response())
        self.assertEqual(r["status"], "newer")
        self.assertEqual((r["current"], r["latest"]), ("v1.3.9", "v1.4.0"))
        self.assertEqual(r["url"], "https://github.com/TariqMK/Asset-Manager/releases/tag/v1.4.0")
        self.assertEqual(r["notes"], "Notes")

    def test_up_to_date(self):
        self.assertEqual(uc.check("1.4.0", fetch=response())["status"], "current")

    def test_local_build_newer_than_release_is_up_to_date(self):
        self.assertEqual(uc.check("1.5.0", fetch=response())["status"], "current")

    def test_dev_build(self):
        r = uc.check("dev", fetch=response())
        self.assertEqual(r["status"], "dev")
        self.assertEqual(r["current"], "dev")

    def test_missing_url_falls_back(self):
        self.assertEqual(uc.check("1.0.0", fetch=response(url=None))["url"], uc.RELEASES_PAGE)

    def test_non_https_url_falls_back(self):
        r = uc.check("1.0.0", fetch=response(url="http://evil.example/x"))
        self.assertEqual(r["url"], uc.RELEASES_PAGE)

    def test_user_agent_and_accept_headers(self):
        captured = {}

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.header_items())
            captured["timeout"] = timeout
            return FakeResponse(json.dumps({"tag_name": "v1.0.0"}).encode())

        original = uc.urllib.request.urlopen
        uc.urllib.request.urlopen = fake_urlopen
        try:
            uc.check("1.0.0")
        finally:
            uc.urllib.request.urlopen = original
        self.assertEqual(captured["headers"]["User-agent"], "AssetManager/1.0.0")
        self.assertEqual(captured["headers"]["Accept"], "application/vnd.github+json")
        self.assertEqual(captured["timeout"], 10)


class ErrorTests(unittest.TestCase):
    def assertMessage(self, fetch, message):
        with self.assertRaises(uc.UpdateCheckError) as ctx:
            uc.check("1.0.0", fetch=fetch)
        self.assertEqual(str(ctx.exception), message)

    def test_no_release(self):
        self.assertMessage(failing(http_error(404)), "No Asset Manager releases are published yet.")

    def test_rate_limit(self):
        for code in (403, 429):
            self.assertMessage(failing(http_error(code)),
                               "GitHub limits how often it can be checked. Try again in an hour.")

    def test_other_http_error(self):
        self.assertMessage(failing(http_error(500)), "GitHub answered with error 500. Try again later.")

    def test_no_connection(self):
        self.assertMessage(failing(urllib.error.URLError("no route")),
                           "Can't reach GitHub: no route. Check the internet connection.")

    def test_timeout(self):
        self.assertMessage(failing(TimeoutError("timed out")),
                           "Can't reach GitHub: timed out. Check the internet connection.")

    def test_unreadable(self):
        msg = "GitHub sent an answer Asset Manager can't read. Try again later."
        self.assertMessage(lambda _v: b"not json", msg)
        self.assertMessage(lambda _v: b"[]", msg)
        self.assertMessage(response(tag="nightly"), msg)


if __name__ == "__main__":
    unittest.main()
