"""Center documentation uses its preference without mutating historical sources."""

import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))
import center_server
import documentation


class CenterDocumentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = mock.Mock()
        self.runtime.preferences.return_value = {"language": "en"}
        self.server = center_server.CenterServer(
            ("127.0.0.1", 0), SimpleNamespace(center_id="docs", revision=1),
            mock.Mock(), self.runtime, self.root)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        def close():
            self.server.shutdown()
            self.server.server_close()
            thread.join(5)
        self.addCleanup(close)
        for name, content in {
            "README.md": '# English <script>alert("secret")</script>',
            "README-ZH.md": "# 中文使用指南",
            "docs/troubleshooting.md": "# 原始排查",
            "docs/windows-setup.md": "# 原始安装",
            "i18n/en/docs/troubleshooting.md": "# English troubleshooting",
            "i18n/en/docs/windows-setup.md": "# English setup",
            "i18n/README.md": "# 中文语言说明",
            "i18n/en/README.md": "# English language guide",
            ".autonomous-company.local": "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n",
            ".env": "PRIVATE_SENTINEL",
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (self.root / "i18n/source-hashes.json").write_text(json.dumps({
            name: documentation.localization.source_digest(self.root / name)
            for name in ("docs/troubleshooting.md", "docs/windows-setup.md")
        }), encoding="utf-8")

    def request(self, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        try:
            connection.request("GET", path, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def test_all_four_documents_follow_center_preference_and_return_to_center(self):
        before = {str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        for language, texts in (
            ("en", ("English &lt;script&gt;", "English troubleshooting", "English setup", "English language guide")),
            ("zh-CN", ("中文使用指南", "原始排查", "原始安装", "中文语言说明")),
        ):
            self.runtime.preferences.return_value = {"language": language}
            for name, text in zip(documentation.DOCUMENTS, texts):
                status, body = self.request("/docs/" + name)
                self.assertEqual(status, 200)
                self.assertIn(text, body)
                self.assertIn('href="/center"', body)
                self.assertIn('lang="' + language + '"', body)
                self.assertNotIn('<script>alert(', body)
        after = {str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(after, before)
        self.runtime.create_request.assert_not_called()

    def test_arbitrary_paths_queries_and_cross_site_reads_are_rejected(self):
        for path in ("/.env", "/docs/.env", "/docs/../.env", "/docs/%2e%2e/.env", "/docs/readme/.env",
                     "/docs/readme?path=.env", "/docs/readme?language=zh-CN"):
            status, body = self.request(path)
            self.assertEqual(status, 404, path)
            self.assertNotIn("PRIVATE_SENTINEL", body)
        self.assertEqual(self.request("/docs/readme", {"Origin": "https://attacker.example"})[0], 403)

    def test_custom_sources_remain_visible_and_symlinks_cannot_expose_private_files(self):
        source = self.root / "docs/troubleshooting.md"
        source.write_text("CUSTOMIZED_SOURCE", encoding="utf-8")
        self.assertIn("CUSTOMIZED_SOURCE", self.request("/docs/troubleshooting")[1])
        original = Path.is_symlink
        with mock.patch.object(Path, "is_symlink", lambda path: path == source or original(path)):
            self.assertNotEqual(self.request("/docs/troubleshooting")[0], 200)
        with mock.patch.object(documentation.localization, "resource_map", return_value={"docs/troubleshooting.md": ".env"}):
            status, body = self.request("/docs/troubleshooting")
            self.assertNotEqual(status, 200)
            self.assertNotIn("PRIVATE_SENTINEL", body)


if __name__ == "__main__":
    unittest.main()
