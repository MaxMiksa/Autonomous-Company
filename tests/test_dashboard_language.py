"""Exercise language HTTP routes against an isolated checkout; never run services."""

import http.client
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock


SERVER_PATH = Path(__file__).resolve().parents[1] / "dashboard/server.py"
SPEC = importlib.util.spec_from_file_location("dashboard_language_server", SERVER_PATH)
server_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server_module)


class DashboardLanguageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        root_patch = mock.patch.object(server_module, "REPO_ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        env_patch = mock.patch.dict(os.environ, {}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        system_patch = mock.patch.object(server_module.localization, "system_language", return_value="en")
        system_patch.start()
        self.addCleanup(system_patch.stop)
        self.server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.DashboardHandler)
        thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        def close():
            self.server.shutdown()
            self.server.server_close()
            thread.join(5)
        self.addCleanup(close)
        self.port = self.server.server_address[1]

    def request(self, path="/api/language", method="GET", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def select(self, language):
        code, body = self.request(method="POST", body=json.dumps({"language": language}),
                                  headers={"Content-Type": "application/json"})
        return code, json.loads(body)

    def test_get_uses_computer_default_and_post_saves_shared_configuration(self):
        code, body = self.request()
        state = json.loads(body)
        self.assertEqual((code, state["language"], state["source"]), (200, "en", "system"))
        code, state = self.select("zh-CN")
        self.assertEqual((code, state["language"], state["nextLanguage"], state["source"]),
                         (200, "zh-CN", "zh-CN", "saved"))
        self.assertEqual((self.root / ".autonomous-company.local").read_text(), "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n")
        self.assertEqual(json.loads(self.request()[1])["language"], "zh-CN")

    def test_mid_product_save_changes_only_next_product_and_survives_reload(self):
        initial = server_module.localization.start_product(self.root, {})
        code, state = self.select("zh-CN")
        self.assertEqual(code, 200)
        self.assertEqual(state["language"], "en")
        self.assertEqual(state["nextLanguage"], "zh-CN")
        self.assertTrue(state["pending"])
        self.assertTrue(state["locked"])
        self.assertEqual(state["productId"], initial["productId"])
        self.assertEqual(json.loads(self.request()[1]), state)
        server_module.localization.next_product(self.root, "NEXT")
        state = json.loads(self.request()[1])
        self.assertEqual(state["language"], "zh-CN")
        self.assertFalse(state["pending"])

    def test_mutations_require_local_origin_json_and_a_valid_small_body(self):
        valid = '{"language":"zh-CN"}'
        cases = [
            ({"Host": "attacker.example", "Content-Type": "application/json"}, valid, 403),
            ({"Origin": "https://attacker.example", "Content-Type": "application/json"}, valid, 403),
            ({"Origin": f"http://localhost:{self.port + 1}", "Content-Type": "application/json"}, valid, 403),
            ({"Sec-Fetch-Site": "cross-site", "Content-Type": "application/json"}, valid, 403),
            ({"Content-Type": "text/plain"}, valid, 415),
        ]
        cases += [({"Content-Type": "application/json"}, body, 400) for body in (
            "", "{", "null", "[]", "{}", '{"language":"fr"}', '{"language":null}',
            '{"language":["en"]}', '{"language":"en","path":".env"}', " " * 1025,
        )]
        with mock.patch.object(server_module.localization, "set_language") as setter:
            for headers, body, expected in cases:
                with self.subTest(headers=headers, body=body[:80]):
                    self.assertEqual(self.request(method="POST", body=body, headers=headers)[0], expected)
            setter.assert_not_called()
        self.assertFalse((self.root / ".autonomous-company.local").exists())
        headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"}
        self.assertEqual(self.request(method="POST", body=valid, headers=headers)[0], 200)
        for path in ("/api/language", "/docs/readme"):
            self.assertEqual(self.request(path, headers={"Origin": "https://attacker.example"})[0], 403)

    def test_invalid_configuration_returns_safe_error_without_rewriting_it(self):
        config = self.root / ".autonomous-company.local"
        original = "AUTONOMOUS_COMPANY_LANGUAGE=secret-invalid-value\n"
        config.write_text(original, encoding="utf-8")
        code, body = self.request()
        self.assertEqual(code, 400)
        self.assertEqual(json.loads(body)["errorCode"], "language_invalid")
        self.assertNotIn("secret-invalid-value", body)
        code, _ = self.select("fr")
        self.assertEqual(code, 400)
        self.assertEqual(config.read_text(), original)

    def test_save_io_failure_has_clear_error_and_no_private_details(self):
        with mock.patch.object(server_module.localization, "set_language", side_effect=OSError("private/file")):
            code, body = self.select("zh-CN")
        self.assertEqual(code, 500)
        self.assertEqual(body, {"ok": False, "errorCode": "language_save_failed"})

    def test_document_routes_are_allowlisted_and_content_is_escaped(self):
        (self.root / "README.md").write_text('# English <script>alert("secret")</script>', encoding="utf-8")
        (self.root / "README-ZH.md").write_text("# 中文使用指南", encoding="utf-8")
        (self.root / "i18n/en").mkdir(parents=True)
        (self.root / "i18n/README.md").write_text("# 中文语言说明", encoding="utf-8")
        (self.root / "i18n/en/README.md").write_text("# English language guide", encoding="utf-8")
        (self.root / ".env").write_text("PRIVATE_SENTINEL", encoding="utf-8")
        code, body = self.request("/docs/readme")
        self.assertEqual(code, 200)
        self.assertIn("# English &lt;script&gt;", body)
        self.assertNotIn("<script>", body)
        self.assertIn('<a href="/docs/language">Language settings</a>', body)
        self.assertIn("# English language guide", self.request("/docs/language")[1])
        self.select("zh-CN")
        self.assertIn("# 中文使用指南", self.request("/docs/readme")[1])
        code, body = self.request("/docs/language")
        self.assertEqual(code, 200)
        self.assertIn("# 中文语言说明", body)
        self.assertIn('<a href="/docs/troubleshooting">故障排查</a>', body)
        for path in ("/.env", "/docs/.env", "/docs/../.env", "/docs/%2e%2e/.env", "/docs/readme/.env"):
            code, body = self.request(path)
            self.assertEqual(code, 404, path)
            self.assertNotIn("PRIVATE_SENTINEL", body)
        self.assertNotIn("PRIVATE_SENTINEL", self.request("/docs/readme?path=.env")[1])

    def test_document_translation_preserves_custom_source_and_rejects_symlinks(self):
        source = self.root / "docs/troubleshooting.md"
        source.parent.mkdir()
        source.write_text("原始排查", encoding="utf-8")
        translation = self.root / "i18n/en/docs/troubleshooting.md"
        translation.parent.mkdir(parents=True)
        translation.write_text("English troubleshooting", encoding="utf-8")
        (self.root / "i18n/source-hashes.json").write_text(json.dumps({
            "docs/troubleshooting.md": server_module.localization.source_digest(source)
        }), encoding="utf-8")
        self.assertIn("English troubleshooting", self.request("/docs/troubleshooting")[1])
        source.write_text("CUSTOMIZED_SOURCE", encoding="utf-8")
        self.assertIn("CUSTOMIZED_SOURCE", self.request("/docs/troubleshooting")[1])
        original = Path.is_symlink
        with mock.patch.object(Path, "is_symlink", lambda path: path == source or original(path)):
            self.assertEqual(self.request("/docs/troubleshooting")[0], 404)
        with mock.patch.object(server_module.localization, "resource_map", return_value={"docs/troubleshooting.md": ".env"}):
            self.assertEqual(self.request("/docs/troubleshooting")[0], 404)


if __name__ == "__main__":
    unittest.main()
