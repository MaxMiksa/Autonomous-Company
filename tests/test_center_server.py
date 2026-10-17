"""HTTP boundary checks; fixture data here is never used for acceptance screenshots."""

import http.client
from email.message import Message
import io
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


class CenterHttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.catalog = mock.Mock()
        self.runtime = mock.Mock()
        self.runtime.create_request.return_value = {"requestId": "one", "state": "queued"}
        self.catalog.journal.return_value = {"project": {"stableId": "selected"}, "cycles": []}
        self.catalog.resource.return_value = (b"<script>alert(1)</script>", "text/html")
        self.server = center_server.CenterServer(
            ("127.0.0.1", 0), SimpleNamespace(center_id="test-center", revision=3),
            self.catalog, self.runtime, Path(self.directory.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        status, output, response_headers = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return status, output, response_headers

    def test_cross_site_and_false_host_cannot_start_work(self):
        for headers in ({"Host": f"evil.invalid:{self.port}"},
                        {"Origin": "https://evil.invalid"},
                        {"Sec-Fetch-Site": "cross-site"},
                        {"Origin": f"http://127.0.0.1:{self.port + 1}"}):
            with self.subTest(headers=headers):
                status, _, _ = self.request("POST", "/api/center/v1/requests", "{}", headers)
                self.assertEqual(status, 403)
        self.runtime.create_request.assert_not_called()

    def test_bad_bodies_do_not_create_requests(self):
        for body, headers, expected in (
            ("{}", {"Content-Type": "text/plain"}, 415),
            ('{"kind":"continue","kind":"explore"}', {}, 400),
            ('{"value":NaN}', {}, 400),
            ('{"value":1e999}', {}, 400),
            ("[]", {}, 400),
            ("{invalid", {}, 400),
            # Reject the declared size before upload; unread large payloads can
            # turn the server's early close into a Windows TCP reset.
            ("", {"Content-Length": str(center_server.MAX_BODY + 1)}, 413),
            ("{}", {"Transfer-Encoding": "chunked"}, 400),
        ):
            with self.subTest(expected=expected, prefix=body[:40]):
                status, _, _ = self.request("POST", "/api/center/v1/requests", body, headers)
                self.assertEqual(status, expected)
        self.runtime.create_request.assert_not_called()

    def test_ambiguous_framing_and_non_ascii_lengths_are_rejected_before_parsing(self):
        for headers in ((('Transfer-Encoding', ''), ('Content-Length', '2')),
                        (('Content-Length', '2'), ('Content-Length', '2')),
                        *(tuple([('Content-Length', value)]) for value in ('+2', '2_0', '２', '2,2', '-1'))):
            with self.subTest(headers=headers):
                handler = object.__new__(center_server.CenterHandler)
                handler.headers = Message()
                handler.headers['Content-Type'] = 'application/json'
                for key, value in headers:
                    handler.headers[key] = value
                handler.rfile = io.BytesIO(b'{}')
                with self.assertRaises(center_server.CenterError):
                    handler.read_body()
                self.assertEqual(handler.rfile.tell(), 0)
        self.runtime.create_request.assert_not_called()

    def test_accepted_request_keeps_queued_state_and_envelope(self):
        body = {"entryId": "selected", "idempotencyKey": "stable", "executionMode": "enqueue"}
        status, raw, _ = self.request("POST", "/api/center/v1/requests", json.dumps(body))
        result = json.loads(raw)
        self.assertEqual(status, 202)
        self.assertEqual(result["data"]["state"], "queued")
        self.assertEqual(result["centerId"], "test-center")
        self.runtime.create_request.assert_called_once_with({**body, "_provenance": {"channel": "local_api"}})

    def test_client_cannot_claim_runner_or_authenticated_provenance(self):
        body = {"_provenance": {"channel": "runner", "authenticatedUserId": "pretend-user"}}
        status, _, _ = self.request("POST", "/api/center/v1/requests", json.dumps(body))
        self.assertEqual(status, 202)
        self.runtime.create_request.assert_called_once_with({"_provenance": {"channel": "local_api"}})

    def test_journal_uses_url_scope_not_global_selection(self):
        status, raw, _ = self.request("GET", "/api/center/v1/entries/product-b/journal?sourceId=source-b&limit=5")
        self.assertEqual(status, 200)
        self.catalog.journal.assert_called_once_with("product-b", {"sourceId": "source-b", "limit": "5"})
        self.assertEqual(json.loads(raw)["data"]["project"]["stableId"], "selected")
        self.runtime.create_request.assert_not_called()

    def test_duplicate_query_rejected_before_source_read(self):
        status, _, _ = self.request("GET", "/api/center/v1/entries/product-b/journal?sourceId=a&sourceId=b")
        self.assertEqual(status, 400)
        self.catalog.journal.assert_not_called()

    def test_preparation_operations_are_readable_without_starting_work(self):
        self.runtime.list_operations.return_value = {"items": [
            {"operationId": "operation-failed", "kind": "explore", "state": "failed", "reason": "FRAMEWORK_UNVERIFIED"}
        ]}
        status, raw, _ = self.request("GET", "/api/center/v1/operations")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["data"]["items"][0]["reason"], "FRAMEWORK_UNVERIFIED")
        self.runtime.list_operations.assert_called_once_with({})
        self.runtime.create_request.assert_not_called()
        self.runtime.create_exploration.assert_not_called()

    def test_preparation_operations_reject_cross_site_reads(self):
        status, _, _ = self.request("GET", "/api/center/v1/operations", headers={"Origin": "https://evil.invalid"})
        self.assertEqual(status, 403)
        self.runtime.list_operations.assert_not_called()

    def test_business_html_cannot_execute_under_center_origin(self):
        status, raw, headers = self.request("GET", "/api/center/v1/entries/product-b/resources/document-a")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertIn(b"<script>", raw)

    def test_scope_and_path_cannot_be_replaced_with_arbitrary_file(self):
        for path in ("/api/center/v1/entries/../resources/secret", "/api/center/v1/entries/a/resources/%2e%2e",
                     "/private.env", "/api/center/v1/entries/a/resources/C:/secret"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)
        self.catalog.resource.assert_not_called()

    def test_unexpected_exception_does_not_leak_local_secrets(self):
        self.runtime.create_request.side_effect = RuntimeError("PRIVATE-SENTINEL token=/home/private/auth.json")
        status, raw, _ = self.request("POST", "/api/center/v1/requests", "{}")
        self.assertEqual(status, 503)
        self.assertNotIn(b"PRIVATE-SENTINEL", raw)
        self.assertNotIn(b"/home/private", raw)

    def test_legacy_write_endpoint_cannot_start_global_service(self):
        status, _, _ = self.request("POST", "/api/action/start", "{}")
        self.assertEqual(status, 404)
        self.runtime.create_request.assert_not_called()

    def test_old_pages_redirect_to_center_and_global_routes_are_absent(self):
        for path in ("/index.html", "/journal", "/journal/", "/journal/index.html",
                     "/legacy", "/legacy/", "/legacy/index.html"):
            status, raw, headers = self.request("GET", path)
            self.assertEqual(status, 302, path)
            self.assertEqual(headers["Location"], "/center")
            self.assertEqual(raw, b"")
        for path in ("/api/journal", "/api/status", "/api/usage", "/api/language", "/api/log-tail",
                     "/api/journal/log?id=anything", "/api/journal/document?path=README.md",
                     "/api/product-media/" + "a" * 32 + "/preview.png", "/legacy/assets/app.js"):
            self.assertEqual(self.request("GET", path)[0], 404, path)
        for path in ("/api/action/start", "/api/action/stop", "/api/action/refresh",
                     "/api/language", "/api/product-media/capture"):
            self.assertEqual(self.request("POST", path, "{}")[0], 404, path)
        self.runtime.create_request.assert_not_called()
        self.runtime.queue_action.assert_not_called()
        self.assertFalse(hasattr(self.server, "legacy"))

    def test_shared_assets_are_explicit_and_logo_bytes_unchanged(self):
        for path, mime in (("/ui-assets/ui.css", "text/css"), ("/ui-assets/ui.js", "application/javascript"),
                           ("/brand-logo.png", "image/png")):
            status, raw, headers = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertTrue(headers["Content-Type"].startswith(mime))
            self.assertEqual(raw, (center_server.DASHBOARD_DIR / path[1:]).read_bytes())
        self.assertEqual(self.request("GET", "/ui-assets/../center_store.py")[0], 404)

    def test_catalog_revision_types_are_rejected_at_the_real_http_write_boundary(self):
        import shutil
        from test_center_catalog import CenterCatalogTests
        fixture = CenterCatalogTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.cycle()
        item, = fixture.import_root()
        moved = fixture.base / 'moved'
        shutil.copytree(fixture.root, moved)
        candidate = fixture.catalog.probe({'root': str(moved)})
        self.catalog.entry_action.side_effect = fixture.catalog.entry_action
        self.catalog.reconnect.side_effect = fixture.catalog.reconnect
        for endpoint, extra in (
            (f"/entries/{item['entryId']}/archive", {}),
            (f"/sources/{item['sourceId']}/reconnect", {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'http-reconnect'}),
        ):
            before = fixture.catalog_snapshot()
            for revision in (True, 1.0):
                status, raw, _ = self.request('POST', '/api/center/v1' + endpoint, json.dumps({**extra, 'expectedRevision': revision}))
                self.assertEqual(status, 400, raw)
                self.assertEqual(json.loads(raw)['code'], 'INVALID_REQUEST')
                self.assertEqual(fixture.catalog_snapshot(), before)
            status, raw, _ = self.request('POST', '/api/center/v1' + endpoint, json.dumps({**extra, 'expectedRevision': 1}))
            self.assertEqual(status, 200, raw)
            self.assertEqual(json.loads(raw)['data']['revision'], 2)

    def test_request_revision_types_do_not_reach_admission_or_preparation_over_http(self):
        from test_center_runtime import QueueTests
        fixture = QueueTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.runtime.create_request.side_effect = fixture.runtime.create_request
        self.runtime.create_exploration.side_effect = fixture.runtime.create_exploration
        request_body = {'entryId': fixture.a['entryId'], 'sourceId': fixture.a['sourceId'], 'runtimeId': fixture.a['runtimeId'], 'expectedSourceRevision': 1}
        before = fixture.snapshot_records()
        with mock.patch.object(fixture.runtime, '_worker') as worker, mock.patch.object(fixture.adapter, 'query', wraps=fixture.adapter.query) as query:
            for path, field, base in (('/requests', 'expectedSourceRevision', request_body),
                                      ('/requests', 'configRevision', request_body),
                                      ('/explorations', 'configRevision', {})):
                for value in (True, 1.0):
                    body = {**base, 'idempotencyKey': 'http-revision-guard', field: value}
                    status, raw, _ = self.request('POST', '/api/center/v1' + path, json.dumps(body))
                    self.assertEqual(status, 400, raw)
                    self.assertEqual(json.loads(raw)['code'], 'INVALID_REQUEST')
                    self.assertEqual(fixture.snapshot_records(), before)
            worker.assert_not_called()
            query.assert_not_called()
        self.assertEqual(fixture.adapter.launched, [])


    def test_import_shape_errors_are_client_errors_not_retryable_server_failures(self):
        from test_center_catalog import CenterCatalogTests
        fixture = CenterCatalogTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.cycle()
        candidate = fixture.catalog.probe({'root': str(fixture.root)})
        self.catalog.probe.side_effect = fixture.catalog.probe
        self.catalog.commit.side_effect = fixture.catalog.commit
        base = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'http-import-shape'}
        before = (fixture.store.revision, fixture.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), fixture.hashes())
        for path, body in (('/imports/probe', {'root': str(fixture.root), 'kindHint': {}}),
                           ('/imports/commit', {**base, 'mode': []}),
                           ('/imports/commit', {**base, 'itemIds': [{}]})):
            status, raw, _ = self.request('POST', '/api/center/v1' + path, json.dumps(body))
            result = json.loads(raw)
            self.assertEqual(status, 400, raw)
            self.assertEqual(result['code'], 'INVALID_INPUT')
            self.assertFalse(result['retryable'])
            self.assertEqual((fixture.store.revision, fixture.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), fixture.hashes()), before)
        self.runtime.create_request.assert_not_called()
        self.runtime.create_exploration.assert_not_called()


    def test_runtime_enum_shape_errors_are_not_retryable_server_errors(self):
        from test_center_runtime import QueueTests
        fixture = QueueTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.runtime.create_request.side_effect = fixture.runtime.create_request
        self.runtime.create_exploration.side_effect = fixture.runtime.create_exploration
        self.runtime.preferences.side_effect = fixture.runtime.preferences
        body = {'idempotencyKey': 'http-enum-request', 'entryId': fixture.a['entryId'], 'sourceId': fixture.a['sourceId'], 'expectedSourceRevision': 1}
        before = fixture.snapshot_records()
        with mock.patch.object(fixture.runtime, '_worker') as worker:
            for path, request, code in (
                ('/requests', {**body, 'kind': {}}, 'INVALID_REQUEST'),
                ('/requests', {**body, 'executionMode': []}, 'INVALID_REQUEST'),
                ('/requests', {**body, 'config': {'engine': {}}}, 'INVALID_CONFIG'),
                ('/explorations', {'idempotencyKey': 'http-enum-explore', 'executionMode': {}}, 'INVALID_REQUEST'),
                ('/explorations', {'idempotencyKey': 'http-enum-explore', 'config': {'effort': []}}, 'INVALID_CONFIG'),
                ('/preferences', {'idempotencyKey': 'http-enum-preference', 'preferences': {'language': []}}, 'INVALID_PREFERENCE'),
            ):
                status, raw, _ = self.request('POST', '/api/center/v1' + path, json.dumps(request))
                result = json.loads(raw)
                self.assertEqual(status, 400, raw); self.assertEqual(result['code'], code); self.assertFalse(result['retryable'])
                self.assertEqual(fixture.snapshot_records(), before)
            worker.assert_not_called()
        self.assertEqual(fixture.adapter.launched, [])


    def test_request_id_container_errors_never_fall_back_or_start_work_over_http(self):
        from test_center_runtime import QueueTests
        fixture = QueueTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        self.runtime.create_request.side_effect = fixture.runtime.create_request
        body = {'idempotencyKey': 'http-id-shapes', 'entryId': fixture.a['entryId'], 'sourceId': fixture.a['sourceId'], 'runtimeId': fixture.a['runtimeId'], 'expectedSourceRevision': 1}
        before = fixture.snapshot_records()
        for field, value in (('entryId', []), ('sourceId', {}), ('sourceId', ['other']), ('runtimeId', [])):
            status, raw, _ = self.request('POST', '/api/center/v1/requests', json.dumps({**body, field: value}))
            result = json.loads(raw)
            self.assertEqual(status, 400, raw); self.assertEqual(result['code'], 'INVALID_REQUEST'); self.assertFalse(result['retryable'])
            self.assertEqual(fixture.snapshot_records(), before)
        self.assertEqual(fixture.adapter.launched, [])

    def test_catalog_id_containers_are_client_errors_over_http(self):
        from test_center_catalog import CenterCatalogTests
        fixture = CenterCatalogTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.cycle(); item, = fixture.import_root()
        self.catalog.commit.side_effect = fixture.catalog.commit
        self.catalog.entry_action.side_effect = fixture.catalog.entry_action
        before = (fixture.store.revision, fixture.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall())
        for path, body in (('/imports/commit', {'candidateId': []}),
                           (f"/entries/{item['entryId']}/source-selection", {'expectedRevision': 1, 'sourceId': {}})):
            status, raw, _ = self.request('POST', '/api/center/v1' + path, json.dumps(body))
            result = json.loads(raw)
            self.assertEqual(status, 400, raw); self.assertEqual(result['code'], 'INVALID_INPUT'); self.assertFalse(result['retryable'])
            self.assertEqual((fixture.store.revision, fixture.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall()), before)


    def test_non_loopback_rejected_before_state_creation(self):
        with self.assertRaises(ValueError):
            center_server.CenterServer(("0.0.0.0", 0), None, None, None)


if __name__ == "__main__":
    unittest.main()
