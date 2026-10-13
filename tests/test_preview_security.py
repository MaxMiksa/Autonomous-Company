"""Real loopback preview requests against disposable public/private fixtures."""
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import urlsplit

ROOT = Path(os.environ.get("AUTONOMOUS_COMPANY_TEST_SOURCE", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts/core"))
from runtime_artifacts import preview_request


class PreviewSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "projects/probe"
        self.project.mkdir(parents=True)
        files = {"index.html": "<!doctype html><title>Synthetic preview</title>",
                 "style.css": "body { color: rgb(1, 2, 3) }", "app.js": "window.previewFixture = true;",
                 "image.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
                 "data.json": '{"fixture": true}', "font.woff2": "synthetic-font",
                 "nested/index.html": "Nested public entry", "listing/readme.txt": "Public resource",
                 ".env": "FAKE_SECRET=synthetic-only", ".git/config": "FAKE_GIT_CONFIG",
                 ".autonomous-company/identity.json": "FAKE_IDENTITY", "hidden/.private.json": "FAKE_PRIVATE",
                 "credentials.json": "FAKE_CREDENTIAL", "service-account.json": "FAKE_SERVICE_ACCOUNT",
                 "secret.pem": "FAKE_KEY", "id_rsa": "FAKE_KEY", "settings.py": "FAKE_SOURCE"}
        for relative, payload in files.items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        environment = dict(os.environ, AUTONOMOUS_COMPANY_CYCLE_ID="security-fixture")
        self.process = subprocess.Popen([sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"),
                                         "--root", str(self.root), "--project", "projects/probe", "preview"],
                                        env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop)
        self.record = None
        deadline = time.monotonic() + 5
        while self.process.poll() is None and time.monotonic() < deadline:
            records = list((self.root / "logs/artifacts").glob("*.json"))
            if records:
                self.record = json.loads(records[0].read_text())
                if preview_request(self.record):
                    break
            time.sleep(0.02)
        self.assertTrue(self.record and preview_request(self.record))
        self.port = urlsplit(self.record["url"]).port

    def stop(self):
        if self.record:
            preview_request(self.record, stop=True)
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
        self.process.wait(timeout=5)

    def request(self, path="/", headers=None, method="GET"):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def test_private_files_and_directory_listing_are_denied(self):
        for path in ("/.env", "/%2eenv", "/.git/config", "/.autonomous-company/identity.json",
                     "/hidden/.private.json", "/credentials.json", "/service-account.json",
                     "/secret.pem", "/id_rsa", "/settings.py", "/listing/", "/listing"):
            with self.subTest(path=path):
                status, body, _ = self.request(path)
                self.assertIn(status, {403, 404})
                self.assertNotIn(b"FAKE_", body)

    def test_normal_web_assets_and_nested_index_are_preserved(self):
        for path in ("/", "/index.html", "/style.css", "/app.js", "/image.svg", "/data.json",
                     "/font.woff2", "/nested/", "/listing/readme.txt", "/app.js?version=1"):
            with self.subTest(path=path):
                status, body, headers = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertNotIn("X-Autonomous-Company-Preview", headers)
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(self.request("/index.html", method="HEAD")[0], 200)

    def test_host_origin_and_cross_site_guards_apply_to_get_head_and_control(self):
        for headers in ({"Host": "attacker.invalid"}, {"Host": "127.0.0.1:1"},
                        {"Origin": "https://attacker.invalid"}, {"Origin": "null"},
                        {"Sec-Fetch-Site": "cross-site"}):
            for method, path in (("GET", "/"), ("HEAD", "/index.html"),
                                 ("GET", "/.autonomous-company-health")):
                with self.subTest(headers=headers, method=method, path=path):
                    supplied = {"X-Autonomous-Company-Preview": self.record["token"], **headers}
                    self.assertEqual(self.request(path, supplied, method)[0], 403)
        self.assertTrue(preview_request(self.record))
        for host in (f"localhost:{self.port}", f"127.0.0.1:{self.port}"):
            self.assertEqual(self.request(headers={"Host": host, "Origin": f"http://{host}", "Sec-Fetch-Site": "same-origin"})[0], 200)
        # Last so the vulnerable implementation cannot stop the server before
        # the independent read-boundary assertions have executed.
        self.assertEqual(self.request("/.autonomous-company-stop", {"Host": "attacker.invalid",
                                     "X-Autonomous-Company-Preview": self.record["token"]}, "POST")[0], 403)

    def test_encoded_traversal_and_linked_files_or_indexes_are_denied(self):
        for path in ("/../index.html", "/%2e%2e/index.html", "/hidden%2f.private.json", "/index.html:stream",
                     "/hidden%5c.private.json", "http://attacker.invalid/index.html"):
            with self.subTest(path=path):
                self.assertIn(self.request(path)[0], {403, 404})
        try:
            (self.project / "linked.json").symlink_to(self.project / "credentials.json")
            (self.project / "linked-index").mkdir()
            (self.project / "linked-index/index.html").symlink_to(self.project / ".env")
        except OSError:
            self.skipTest("Symlink creation unavailable; traversal controls executed")
        self.assertIn(self.request("/linked.json")[0], {403, 404})
        self.assertIn(self.request("/linked-index/")[0], {403, 404})

    def test_health_and_stop_require_token_and_stop_exits_cleanly(self):
        for path, method in (("/.autonomous-company-health", "GET"), ("/.autonomous-company-stop", "POST")):
            for token in (None, "b" * 32):
                headers = {"X-Autonomous-Company-Preview": token} if token else {}
                status, _, returned = self.request(path, headers, method)
                self.assertEqual(status, 403)
                self.assertNotIn("X-Autonomous-Company-Preview", returned)
        self.assertTrue(preview_request(self.record))
        self.assertTrue(preview_request(self.record, stop=True))
        self.assertEqual(self.process.wait(timeout=5), 0)
        self.assertFalse(preview_request(self.record))
        record = json.loads(next((self.root / "logs/artifacts").glob("*.json")).read_text())
        self.assertEqual(record["state"], "stopped")
        self.assertTrue(record["endedAt"])


if __name__ == "__main__":
    unittest.main()
