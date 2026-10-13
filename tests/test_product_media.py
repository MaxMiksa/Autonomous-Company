"""Media boundaries plus opt-in real Chromium/static/Node preview acceptance."""
import json
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
from product_identity import get_identity, reserve_cycle
from product_media import (MediaError, VIEWPORTS, atomic_json, capture_lock, capture_product,
                           content_version, digest, load_profile, media_folder, media_projection,
                           now, read_resource, validate_icon)
from runtime_artifacts import finalize
from product_media_process import ProcessScope, proc_identity
from product_icon_html import inspect_reference

HEAD_REVIEW_CASES = {
    "title_pseudo_link": '<!doctype html><html><head><title>Example <link rel="icon" href="/autonomous-company-icon.svg"></title></head><body><main>Business</main></body></html>',
    "self_closing_title": '<!doctype html><html><head><title/>Product</head><body><main>Business</main></body></html>',
    "leading_business_text": '<!doctype html>Business prefix<html><head><title>Product</title></head><body><main>Business</main></body></html>',
    "stray_end_br": '<!doctype html><html><head><title>Product</title></br></head><body><main>Business</main></body></html>',
    "script_double_escaped": '<!doctype html><html><head><script>const example = "<!--<script>";</script></head><body><main>Business</main></body></html>',
    "script_fake_close": '<!doctype html><html><head><script>// </ script>\n</head><body><main>Business</main></body></html>',
    "spaced_head_close": '<!doctype html><html><head><title>Product</title></ head><body><main>Business</main></body></html>',
}


class MediaFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "projects/example"
        self.project.mkdir(parents=True)
        self.name = "projects/example"
        self.product_id = get_identity(self.root, self.name, create=True)["id"]
        self.folder = media_folder(self.root, self.product_id)
        (self.project / "index.html").write_text("<!doctype html><title>Example</title><main><h1>Real product page</h1></main>", encoding="utf-8")

    def write_profile(self, profile):
        atomic_json(self.project / ".autonomous-company/media.json", {"version": 1, **profile})

    def unit_worker(self, project, profile, version, staging):
        # Unit-only solid PNG fixtures exercise storage transactions. Real
        # browser cases below assert actual rendered product output separately.
        def chunk(kind, body):
            value = kind + body
            return len(body).to_bytes(4, "big") + value + zlib.crc32(value).to_bytes(4, "big")
        for viewport in VIEWPORTS:
            header = viewport["width"].to_bytes(4, "big") + viewport["height"].to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
            pixels = (b"\0" + bytes.fromhex(version[:6]) * viewport["width"]) * viewport["height"]
            raw = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
            (staging / (viewport["name"] + ".png")).write_bytes(raw)
        return {"state": "success"}

    def capture(self, **kwargs):
        with patch("product_media.run_worker", side_effect=self.unit_worker):
            return capture_product(self.root, self.name, "cycle-1", **kwargs)


class MediaTests(MediaFixture):
    def test_reads_are_side_effect_free_and_archives_cannot_capture(self):
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        value = media_projection(self.root, self.name, readonly=True)
        self.assertEqual(value["screenshot"]["state"], "missing")
        self.assertFalse(self.folder.exists())
        with self.assertRaisesRegex(MediaError, "readonly"):
            capture_product(self.root, self.name, readonly=True)
        self.assertEqual(before, sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*")))

    def test_default_capture_is_idempotent_and_only_publishes_its_known_icon(self):
        before = {str(path.relative_to(self.project)): path.read_bytes() for path in self.project.rglob("*") if path.is_file()}
        with patch("product_media.run_worker", side_effect=self.unit_worker) as worker:
            first = capture_product(self.root, self.name, "cycle-1")
            second = capture_product(self.root, self.name, "cycle-2")
            self.assertEqual(worker.call_count, 1)
        self.assertEqual(first["latestSuccess"], second["latestSuccess"])
        after = {str(path.relative_to(self.project)): path.read_bytes() for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(set(after) - set(before), {"autonomous-company-icon.svg"})
        self.assertEqual(before, {name: raw for name, raw in after.items() if name in before})
        value = media_projection(self.root, self.name)
        self.assertEqual(value["screenshot"]["state"], "success")
        self.assertEqual(value["icon"]["source"], "default")
        self.assertEqual(value["icon"]["publicationStatus"], "published")
        self.assertEqual(digest(after["autonomous-company-icon.svg"]), value["icon"]["sha256"])

    def test_icon_publication_preserves_conflicts_and_updates_only_owned_bytes(self):
        canonical = self.project / "autonomous-company-icon.svg"
        canonical.write_text("user-owned file")
        record = self.capture()
        self.assertEqual(canonical.read_text(), "user-owned file")
        self.assertEqual(record["icon"]["publicationStatus"], "conflict")
        canonical.unlink()
        record = self.capture()
        self.assertEqual(record["icon"]["publicationStatus"], "published")
        (self.project / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="24" fill="#123456"/></svg>')
        updated = self.capture()
        self.assertEqual(updated["icon"]["publicationStatus"], "published")
        self.assertEqual(digest(canonical.read_bytes()), updated["icon"]["sha256"])
        canonical.write_text("manual change")
        self.assertEqual(media_projection(self.root, self.name)["icon"]["publicationStatus"], "stale")
        self.assertEqual(self.capture()["icon"]["publicationStatus"], "conflict")
        self.assertEqual(canonical.read_text(), "manual change")

    def test_source_change_failure_retains_original_success_and_requires_retry(self):
        original = self.capture()["latestSuccess"]
        (self.project / "index.html").write_text("<main>Changed product</main>")
        self.assertEqual(media_projection(self.root, self.name)["screenshot"]["state"], "stale")
        with patch("product_media.run_worker", side_effect=MediaError("browser_missing")) as worker:
            failed = capture_product(self.root, self.name)
            capture_product(self.root, self.name)
            self.assertEqual(worker.call_count, 1)
        self.assertEqual(failed["latestSuccess"], original)
        self.assertEqual(failed["attempt"]["reason"], "browser_missing")
        value = media_projection(self.root, self.name)["screenshot"]
        self.assertEqual(value["state"], "failed")
        self.assertTrue(value["stale"])
        self.assertEqual(self.capture(retry=True)["attempt"]["state"], "success")

    def test_changed_during_capture_is_not_published(self):
        def mutate(project, profile, version, staging):
            result = self.unit_worker(project, profile, version, staging)
            (self.project / "index.html").write_text("<main>Different version</main>")
            return result
        with patch("product_media.run_worker", side_effect=mutate):
            record = capture_product(self.root, self.name)
        self.assertEqual(record["attempt"]["reason"], "version_changed")
        self.assertNotIn("latestSuccess", record)
        self.assertFalse(list(self.folder.glob(".capture-*")))

    def test_svg_injection_external_content_and_complexity_are_rejected(self):
        wrapper = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{}</svg>'
        for content in ['<script>alert(1)</script>', '<image href="https://example.com/a"/>',
                        '<path d="M0 0" onclick="alert(1)"/>', '<style>path {fill:red}</style>',
                        '<foreignObject/>', '<animate attributeName="x"/>', '<path fill="url(#evil)"/>',
                        '<g>' + '<circle r="1"/>' * 64 + '</g>']:
            with self.subTest(content=content[:30]):
                with self.assertRaises(MediaError):
                    validate_icon(wrapper.format(content).encode())
        with self.assertRaises(MediaError):
            validate_icon(b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///secret">]><svg viewBox="0 0 64 64">&x;</svg>')
        self.assertEqual(validate_icon(wrapper.format('<circle cx="32" cy="32" r="24" fill="#456"/>').encode()), wrapper.format('<circle cx="32" cy="32" r="24" fill="#456"/>').encode())

    def test_existing_icon_is_used_and_invalid_icon_gets_marked_default(self):
        icon = self.project / "icon.svg"
        icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#123456"/></svg>')
        self.capture()
        self.assertEqual(media_projection(self.root, self.name)["icon"]["source"], "product")
        icon.write_text('<svg onload="alert(1)" viewBox="0 0 64 64"/>')
        self.capture()
        result = media_projection(self.root, self.name)["icon"]
        self.assertEqual(result["source"], "default")
        self.assertEqual(result["reason"], "icon_rejected")

    def test_resources_are_registered_and_hash_checked(self):
        record = self.capture()
        variant = record["latestSuccess"]["variants"][0]
        self.assertEqual(read_resource(self.root, self.product_id, variant["name"])[1], "image/png")
        self.assertIsNone(read_resource(self.root, self.product_id, "../media.json"))
        unregistered = "f" * 64 + ".png"
        (self.folder / unregistered).write_bytes(b"unregistered")
        self.assertIsNone(read_resource(self.root, self.product_id, unregistered))
        (self.folder / variant["name"]).write_bytes(b"modified")
        self.assertIsNone(read_resource(self.root, self.product_id, variant["name"]))
        self.assertEqual(media_projection(self.root, self.name)["screenshot"]["reason"], "artifact_missing_or_modified")

    def test_malformed_manifest_is_not_an_image_or_server_exception(self):
        self.folder.mkdir(parents=True)
        for extra in [{"attempt": []}, {"icon": "bad"}, {"deliveries": {}}, {"latestSuccess": {"version": "a" * 64, "variants": ["bad", "bad"]}}]:
            atomic_json(self.folder / "media.json", {"version": 1, "productId": self.product_id, **extra})
            self.assertIsNone(media_projection(self.root, self.name)["screenshot"]["latestSuccess"])
            self.assertIsNone(read_resource(self.root, self.product_id, "a" * 64 + ".png"))

    def test_missing_node_is_recorded_without_affecting_the_default_icon(self):
        with patch("product_media.shutil.which", return_value=None):
            record = capture_product(self.root, self.name)
        self.assertEqual(record["attempt"]["reason"], "node_missing")
        self.assertEqual(record["icon"]["publicationStatus"], "published")
        self.assertNotIn("latestSuccess", record)

    def test_crashed_recent_capture_waits_for_watchdog_then_recovers(self):
        self.folder.mkdir(parents=True)
        old = {"id": "a" * 32, "state": "capturing", "startedAt": now()}
        atomic_json(self.folder / "media.json", {"version": 1, "productId": self.product_id, "attempt": old})
        with self.assertRaisesRegex(MediaError, "capture_busy"):
            self.capture()
        old["startedAt"] = "2000-01-01T00:00:00+00:00"
        atomic_json(self.folder / "media.json", {"version": 1, "productId": self.product_id, "attempt": old})
        self.assertEqual(media_projection(self.root, self.name)["screenshot"]["state"], "interrupted")
        self.assertEqual(self.capture()["attempt"]["state"], "success")
        saved = json.loads((self.folder / ("attempt-" + "a" * 32 + ".json")).read_text())
        self.assertEqual(saved["state"], "interrupted")

    def test_nested_static_profile_and_missing_node_entry_are_explicit(self):
        (self.project / "public").mkdir()
        (self.project / "public/index.html").write_text("<main>Nested</main>")
        self.write_profile({"type": "static", "webRoot": "public", "entry": "/", "readySelector": "main"})
        self.assertEqual(load_profile(self.project)["webRoot"], "public")
        self.write_profile({"type": "node", "command": ["node", "missing.js", "{port}"]})
        with self.assertRaisesRegex(MediaError, "node_entry_missing"):
            load_profile(self.project)
        self.write_profile({"type": "node", "command": ["sh", "-c", "something"]})
        with self.assertRaisesRegex(MediaError, "invalid_command"):
            load_profile(self.project)

    def test_config_paths_and_steps_cannot_escape_or_evaluate(self):
        for config in [{"type": "static", "webRoot": "../"}, {"type": "static", "entry": "http://localhost/"},
                       {"type": "static", "entry": "/../secret"}, {"type": "static", "steps": [{"action": "evaluate", "value": "alert(1)"}]},
                       {"type": "static", "timeoutSeconds": 200}]:
            self.write_profile(config)
            with self.assertRaises(MediaError):
                load_profile(self.project)

    def test_concurrent_capture_returns_busy_without_worker(self):
        self.folder.mkdir(parents=True)
        with capture_lock(self.folder), patch("product_media.run_worker") as worker:
            with self.assertRaisesRegex(MediaError, "capture_busy"):
                capture_product(self.root, self.name)
            worker.assert_not_called()

    def test_other_os_writer_binding_is_rejected_before_starting_worker(self):
        self.folder.mkdir(parents=True)
        atomic_json(self.folder / "writer.json", {"version": 1, "os": "posix" if os.name == "nt" else "nt"})
        with patch("product_media.run_worker") as worker:
            with self.assertRaisesRegex(MediaError, "writer_runtime_mismatch"):
                capture_product(self.root, self.name)
            worker.assert_not_called()

    def test_cleanup_only_never_starts_media(self):
        cycle = reserve_cycle(self.root, self.name, "cleanup-only", 1)["cycleId"]
        with patch("product_media.run_worker") as worker:
            finalize(self.root, cycle, capture=False)
            worker.assert_not_called()
        self.assertFalse(self.folder.exists())

    def test_scope_reaps_child_even_after_worker_leader_exits(self):
        marker = self.root / "child-pid"
        script = self.root / "leader.py"
        script.write_text("import pathlib,subprocess,sys,time\nchild=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\npathlib.Path(sys.argv[1]).write_text(str(child.pid))\ntime.sleep(0.2)\n")
        scope = ProcessScope([sys.executable, str(script), str(marker)])
        try:
            deadline = time.monotonic() + 5
            while scope.process.poll() is None and time.monotonic() < deadline:
                scope.observe()
                time.sleep(0.02)
            self.assertEqual(scope.process.wait(timeout=3), 0)
            pid = int(marker.read_text())
        finally:
            scope.close()
        if os.name == "nt":
            result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True)
            self.assertNotIn(f'"{pid}"', result.stdout)
        elif Path("/proc").is_dir():
            proc = Path(f"/proc/{pid}/stat")
            self.assertTrue(not proc.exists() or proc.read_text().split()[2] == "Z")

    def test_cli_none_and_unknown_ui_are_explicit(self):
        self.write_profile({"type": "none"})
        with patch("product_media.run_worker") as worker:
            self.assertEqual(capture_product(self.root, self.name)["attempt"]["state"], "not_applicable")
            worker.assert_not_called()
        (self.project / ".autonomous-company/media.json").unlink()
        (self.project / "index.html").unlink()
        self.assertEqual(capture_product(self.root, self.name)["attempt"]["state"], "unsupported")

    def test_delivery_preserves_capture_and_ordinary_history_has_capacity(self):
        first = self.capture(trigger="delivery")["latestSuccess"]
        older = None
        for number in range(7):
            (self.project / "index.html").write_text(f"<main>{number}</main>")
            result = self.capture()
            if number == 0:
                older = result["latestSuccess"]
        self.assertTrue(all((self.folder / row["name"]).exists() for row in first["variants"]))
        self.assertTrue(all(not (self.folder / row["name"]).exists() for row in older["variants"]))
        self.assertEqual(len(list(self.folder.glob("attempt-*.json"))), 8)

    def test_cycle_close_captures_without_model_artifacts_or_preview(self):
        cycle = reserve_cycle(self.root, self.name, "cycle-normal", 1)["cycleId"]
        with patch("product_media.run_worker", side_effect=self.unit_worker) as worker:
            finalize(self.root, cycle)
            self.assertEqual(worker.call_count, 1)
        value = media_projection(self.root, self.name)["screenshot"]
        self.assertEqual(value["latestSuccess"]["cycleId"], cycle)

    def test_media_failure_does_not_fail_cycle_or_document_registration(self):
        cycle = reserve_cycle(self.root, self.name, "cycle-failed-media", 1)["cycleId"]
        with patch("product_media.run_worker", side_effect=MediaError("playwright_missing")):
            finalize(self.root, cycle)
        self.assertEqual(media_projection(self.root, self.name)["screenshot"]["reason"], "playwright_missing")
        (self.project / "DELIVERY.md").write_text("Delivery")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"), "--root", str(self.root), "--project", self.name, "document", "DELIVERY.md"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(os.name == "nt", "Native Windows symlink privileges are optional; covered on POSIX")
    def test_symlink_web_content_and_media_resources_are_rejected(self):
        outside = self.root / "outside.html"
        outside.write_text("Secret")
        (self.project / "leak.html").symlink_to(outside)
        with self.assertRaisesRegex(MediaError, "linked_path"):
            content_version(self.project, load_profile(self.project))
        (self.project / "leak.html").unlink()
        record = self.capture()
        target = self.folder / record["latestSuccess"]["variants"][0]["name"]
        target.unlink()
        target.symlink_to(outside)
        self.assertIsNone(read_resource(self.root, self.product_id, target.name))


class MediaIconReferenceTests(MediaFixture):
    def html(self, head="", newline="\n"):
        value = '<!doctype html>\n<html><head><title>Product</title>' + head + '</head><body><main>Unchanged business content</main><script>window.example = "real";</script></body></html>\n'
        raw = value.replace("\n", newline).encode()
        (self.project / "index.html").write_bytes(raw)
        return raw

    def test_missing_reference_inserts_only_owned_metadata_and_is_idempotent(self):
        original = self.html(newline="\r\n")
        with patch("product_media.run_worker", side_effect=self.unit_worker) as worker:
            first = capture_product(self.root, self.name, "cycle-1")
            updated = (self.project / "index.html").read_bytes()
            second = capture_product(self.root, self.name, "cycle-2")
            self.assertEqual(worker.call_count, 1)
        inserted = b'\r\n<link rel="icon" type="image/svg+xml" href="autonomous-company-icon.svg" data-autonomous-company-icon="v1">\r\n'
        self.assertEqual(updated.replace(inserted, b""), original)
        self.assertEqual(updated.count(inserted), 1)
        self.assertEqual((self.project / "index.html").read_bytes(), updated)
        self.assertEqual(first["icon"]["reference"]["state"], "inserted")
        self.assertEqual(second["icon"]["reference"]["state"], "linked")
        self.assertEqual(first["attempt"]["version"], content_version(self.project, load_profile(self.project)))
        self.assertTrue(media_projection(self.root, self.name)["icon"]["reference"]["unified"])

    def test_existing_correct_reference_is_not_reformatted_or_duplicated(self):
        original = self.html("<link type='image/svg+xml' href='./autonomous-company-icon.svg' rel='shortcut icon'>")
        record = self.capture()
        self.assertEqual((self.project / "index.html").read_bytes(), original)
        self.assertEqual(record["icon"]["reference"]["state"], "linked")
        self.assertFalse(record["icon"]["reference"]["managed"])

    def test_head_offset_preserves_non_lf_line_separators_and_rejects_self_closing_head(self):
        for original in [b'<html>\r<head><title>Product</title>\r</head><body>Business</body></html>',
                         '<html><head><title>Product\u2028name</title></head><body>Business</body></html>'.encode()]:
            (self.project / "index.html").write_bytes(original)
            record = self.capture()
            self.assertEqual(record["icon"]["reference"]["state"], "inserted")
            inserted = b'\n<link rel="icon" type="image/svg+xml" href="autonomous-company-icon.svg" data-autonomous-company-icon="v1">\n'
            self.assertEqual((self.project / "index.html").read_bytes().replace(inserted, b""), original)
        for original in [b"<html><head/><body>Business</body></html>",
                         b"<html><body>Business<head></head></body></html>",
                         b"<html><head><div>Business</div></head></html>",
                         b"<html><head>Business text</head></html>"]:
            (self.project / "index.html").write_bytes(original)
            self.assertEqual(self.capture()["icon"]["reference"]["state"], "unsupported")
            self.assertEqual((self.project / "index.html").read_bytes(), original)

    def test_existing_safe_custom_favicon_is_preserved_without_unification_claim(self):
        original = self.html('<link rel="icon" href="brand.svg">')
        (self.project / "brand.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="24" fill="#abcdef"/></svg>')
        record = self.capture()
        self.assertEqual((self.project / "index.html").read_bytes(), original)
        self.assertEqual(record["icon"]["reference"]["state"], "preserved")
        self.assertFalse(record["icon"]["reference"]["unified"])

    def test_title_script_and_style_text_never_count_as_dom_icon_references(self):
        for head in ['<title>Example <link rel="icon" href="autonomous-company-icon.svg"></title>',
                     '<script src="app.js"></script>',
                     '<style>/* <link rel="icon" href="autonomous-company-icon.svg"> */</style>']:
            original = self.html(head)
            record = self.capture()
            self.assertEqual(record["icon"]["reference"]["state"], "inserted")
            self.assertIn(head.encode(), (self.project / "index.html").read_bytes())
            self.assertNotEqual((self.project / "index.html").read_bytes(), original)
            self.assertEqual(media_projection(self.root, self.name)["icon"]["reference"]["state"], "linked")

    def test_ambiguous_browser_head_boundaries_fail_closed_without_writing(self):
        originals = [value for name, value in HEAD_REVIEW_CASES.items() if name != "title_pseudo_link"]
        originals += [f'<html><head><{tag}/>Product</head><body>Business</body></html>' for tag in ["script", "style"]]
        originals += [f'<html><head><{tag}>Unclosed</head><body>Business</body></html>' for tag in ["title", "script", "style"]]
        originals += [f'<html><head><title>Product</title></{tag}></head><body>Business</body></html>' for tag in ["body", "html"]]
        originals += ['<!doctype html>\u00a0<html><head><title>Product</title></head><body>Business</body></html>']
        originals += [f'<html><head><{tag}>Text</ {tag}></head><body>Business</body></html>' for tag in ["title", "style"]]
        originals += ['<html><head><script>const apparent = \'<link rel="icon" href="autonomous-company-icon.svg">\';</script></head><body>Business</body></html>']
        for original in originals:
            raw = original.encode()
            (self.project / "index.html").write_bytes(raw)
            record = self.capture()
            with self.subTest(html=original[:70]):
                self.assertEqual(record["icon"]["reference"]["state"], "unsupported")
                self.assertIsNone(record["icon"]["reference"]["unified"])
                self.assertEqual((self.project / "index.html").read_bytes(), raw)
                projection = media_projection(self.root, self.name, readonly=True)
                self.assertEqual(projection["icon"]["reference"]["state"], "unsupported")
                self.assertIsNone(projection["icon"]["reference"]["unified"])

    def test_canonical_conflict_does_not_insert_an_invalid_favicon(self):
        original = self.html()
        (self.project / "autonomous-company-icon.svg").write_text("user-owned conflicting bytes")
        record = self.capture()
        self.assertEqual(record["icon"]["publicationStatus"], "conflict")
        self.assertEqual(record["icon"]["reference"]["state"], "conflict")
        self.assertEqual((self.project / "index.html").read_bytes(), original)

    def test_pure_read_reports_missing_reference_without_repairing_it(self):
        self.html()
        self.capture()
        missing = self.html()
        before = (self.folder / "media.json").read_bytes()
        projection = media_projection(self.root, self.name, readonly=True)
        self.assertEqual(projection["icon"]["reference"]["state"], "missing")
        self.assertEqual(projection["icon"]["reference"]["reason"], "icon_reference_missing")
        with self.assertRaisesRegex(MediaError, "readonly"):
            capture_product(self.root, self.name, readonly=True)
        self.assertEqual((self.project / "index.html").read_bytes(), missing)
        self.assertEqual((self.folder / "media.json").read_bytes(), before)

    def test_html_write_failure_is_diagnostic_and_does_not_fail_the_capture(self):
        from product_media import atomic_bytes
        original = self.html()

        def fail_html(path, value):
            if path == self.project / "index.html":
                raise PermissionError("HTML is read-only")
            return atomic_bytes(path, value)

        with patch("product_media.atomic_bytes", side_effect=fail_html):
            record = self.capture()
        self.assertEqual(record["icon"]["reference"]["state"], "failed")
        self.assertEqual(record["attempt"]["state"], "success")
        self.assertEqual((self.project / "index.html").read_bytes(), original)

    def test_external_base_dynamic_and_implicit_heads_are_not_rewritten(self):
        (self.project / "user-icon.png").write_bytes(b"Raster favicon is deliberately outside the SVG validator")
        for head, expected in [('<base href="/elsewhere/">', "unconfirmed"),
                               ('<link rel="icon" href="https://example.invalid/icon.svg">', "unconfirmed"),
                               ('<link rel="icon" href="user-icon.png">', "unconfirmed")]:
            original = self.html(head)
            self.assertEqual(self.capture()["icon"]["reference"]["state"], expected)
            self.assertEqual((self.project / "index.html").read_bytes(), original)
        implicit = b"<title>Product</title><main>Business content</main>"
        (self.project / "index.html").write_bytes(implicit)
        self.assertEqual(self.capture()["icon"]["reference"]["state"], "unsupported")
        self.assertEqual((self.project / "index.html").read_bytes(), implicit)
        self.assertEqual(inspect_reference(self.project, {"type": "node"}, {}, write=True)["state"], "unconfirmed")
        self.assertEqual(inspect_reference(self.project, {"type": "none"}, {}, write=True)["state"], "not_applicable")

    def test_modified_owned_reference_is_preserved_and_flagged(self):
        original = self.html('<link rel="stylesheet" href="custom.css" data-autonomous-company-icon="v1">')
        record = self.capture()
        self.assertEqual(record["icon"]["reference"]["state"], "conflict")
        self.assertEqual(record["icon"]["reference"]["reason"], "owned_reference_modified")
        self.assertEqual((self.project / "index.html").read_bytes(), original)

    def test_broken_existing_reference_is_retained_beside_the_new_metadata(self):
        self.html('<link rel="icon" href="missing.svg">')
        record = self.capture()
        updated = (self.project / "index.html").read_text()
        self.assertIn('<link rel="icon" href="missing.svg">', updated)
        self.assertIn('data-autonomous-company-icon="v1"', updated)
        self.assertEqual(record["icon"]["reference"]["state"], "inserted")

    def test_nested_entry_uses_the_web_root_canonical_icon(self):
        nested = self.project / "public/nested"
        nested.mkdir(parents=True)
        (nested / "index.html").write_text("<!doctype html><html><head><title>Nested</title></head><body><main>Real entry</main></body></html>")
        self.write_profile({"type": "static", "webRoot": "public", "entry": "/nested/index.html"})
        record = self.capture()
        self.assertEqual(record["icon"]["reference"]["entryPath"], "public/nested/index.html")
        self.assertTrue((self.project / "public/autonomous-company-icon.svg").is_file())
        self.assertIn('href="../autonomous-company-icon.svg"', (nested / "index.html").read_text())
        self.assertEqual(record["icon"]["reference"]["href"], "../autonomous-company-icon.svg")


@unittest.skipUnless(os.environ.get("AUTONOMOUS_COMPANY_TEST_PRODUCT_MEDIA_BROWSER") == "1", "Set AUTONOMOUS_COMPANY_TEST_PRODUCT_MEDIA_BROWSER=1 for real Chromium acceptance")
class BrowserMediaTests(MediaFixture):
    def test_supported_head_boundaries_match_chromium_and_relative_icons_are_portable(self):
        rows = []
        for name, before in HEAD_REVIEW_CASES.items():
            project_name = "projects/" + name.replace("_", "-")
            project = self.root / project_name
            project.mkdir(parents=True)
            (project / "index.html").write_text(before, encoding="utf-8")
            get_identity(self.root, project_name, create=True)
            with patch("product_media.run_worker", side_effect=self.unit_worker):
                record = capture_product(self.root, project_name)
            rows.append({"name": name, "before": before, "after": (project / "index.html").read_text(encoding="utf-8"),
                         "reference": record["icon"]["reference"], "fileUrl": (project / "index.html").as_uri(),
                         "canonicalUrl": (project / "autonomous-company-icon.svg").as_uri(), "deploymentUrl": "https://example.invalid/products/demo/index.html"})
        nested = self.project / "public/nested"
        nested.mkdir(parents=True)
        before = "<!doctype html><html><head><title>Nested</title></head><body><main>Business</main></body></html>"
        (nested / "index.html").write_text(before)
        self.write_profile({"type": "static", "webRoot": "public", "entry": "/nested/index.html"})
        record = self.capture()
        rows.append({"name": "nested_relative", "before": before, "after": (nested / "index.html").read_text(),
                     "reference": record["icon"]["reference"], "fileUrl": (nested / "index.html").as_uri(),
                     "canonicalUrl": (self.project / "public/autonomous-company-icon.svg").as_uri(), "deploymentUrl": "https://example.invalid/products/demo/nested/index.html"})
        request = self.root / "head-browser-cases.json"
        request.write_text(json.dumps(rows), encoding="utf-8")
        result = subprocess.run(["node", str(ROOT / "tests/browser/media-reference-probe.cjs"), str(request)], capture_output=True,
                                text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        observations = json.loads(result.stdout)
        for row in observations:
            with self.subTest(case=row["name"]):
                self.assertEqual(row["before"]["body"], row["after"]["body"])
                self.assertEqual(row["before"]["title"], row["after"]["title"])
                if row["name"] in {"title_pseudo_link", "nested_relative"}:
                    self.assertEqual(row["reference"]["state"], "inserted")
                    self.assertEqual(row["after"]["headIcons"], 1)
                    self.assertEqual(row["after"]["bodyIcons"], 0)
                    self.assertEqual(row["resolvedFile"], row["canonicalUrl"])
                    self.assertEqual(row["after"]["absoluteHref"], row["canonicalUrl"])
                    self.assertEqual(row["resolvedDeployment"], "https://example.invalid/products/demo/autonomous-company-icon.svg")
                else:
                    self.assertEqual(row["reference"]["state"], "unsupported")
                    self.assertEqual(row["before"], row["after"])

    def test_real_static_capture_default_icon_idempotence_and_cleanup(self):
        (self.project / "index.html").write_text('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:24px sans-serif;margin:48px}main{max-width:700px}button{padding:12px}</style></head><body><main><h1>Product media verification</h1><p>Actual responsive page rendered by Chromium.</p><button onclick="this.textContent=\'Example selected\'">Load built-in example</button></main></body></html>')
        self.write_profile({"type": "static", "readySelector": "main", "steps": [{"action": "click", "selector": "button"}]})
        record = capture_product(self.root, self.name, "real-static")
        self.assertEqual(record["attempt"]["state"], "success", record["attempt"])
        self.assertEqual(record["icon"]["reference"]["state"], "inserted")
        self.assertTrue(media_projection(self.root, self.name)["icon"]["reference"]["unified"])
        for variant in record["latestSuccess"]["variants"]:
            self.assertGreater((self.folder / variant["name"]).stat().st_size, 3000)
        repeated = capture_product(self.root, self.name, "real-static-again")
        self.assertEqual(record["attempt"]["id"], repeated["attempt"]["id"])
        self.assertFalse(list(self.folder.glob(".capture-*")))

    def node_server(self, headers=True, spawn_descendant=False):
        header_source = '"X-Autonomous-Company-Media": process.env.AUTONOMOUS_COMPANY_MEDIA_TOKEN, "X-Autonomous-Company-Version": process.env.AUTONOMOUS_COMPANY_MEDIA_VERSION' if headers else '"X-Autonomous-Company-Media": "another-product"'
        script = 'const http=require("node:http"),fs=require("node:fs");'
        if spawn_descendant:
            script += 'const child=require("node:child_process").spawn(process.execPath,["-e","setInterval(()=>{},1000)"],{stdio:"ignore"}); fs.writeFileSync(".child-pid",String(child.pid));'
        script += f'const server=http.createServer((req,res)=>{{res.writeHead(200,{{{header_source},"Content-Type":"text/html"}});res.end(fs.readFileSync("index.html"));}}); server.listen(Number(process.argv[2]),"127.0.0.1",()=>fs.writeFileSync(".preview-port",String(server.address().port)));'
        (self.project / "preview.cjs").write_text(script)
        self.write_profile({"type": "node", "command": ["node", "preview.cjs", "{port}"], "healthPath": "/", "readySelector": "main", "timeoutSeconds": 2})

    def test_real_node_development_server_and_descendants_are_reaped(self):
        self.node_server(spawn_descendant=True)
        record = capture_product(self.root, self.name, "real-node")
        self.assertEqual(record["attempt"]["state"], "success", record["attempt"])
        port = int((self.project / ".preview-port").read_text())
        with socket.socket() as client:
            client.settimeout(1)
            self.assertNotEqual(client.connect_ex(("127.0.0.1", port)), 0)
        pid = int((self.project / ".child-pid").read_text())
        if os.name == "nt":
            result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True)
            self.assertNotIn(f'"{pid}"', result.stdout)
        else:
            proc = Path(f"/proc/{pid}/stat")
            self.assertTrue(not proc.exists() or proc.read_text().split()[2] == "Z")

    def test_wrong_product_at_port_never_publishes_image(self):
        self.node_server(headers=False)
        record = capture_product(self.root, self.name, "wrong-port")
        self.assertEqual(record["attempt"]["reason"], "preview_identity_or_readiness_failed")
        self.assertNotIn("latestSuccess", record)
        port = int((self.project / ".preview-port").read_text())
        with socket.socket() as client:
            client.settimeout(1)
            self.assertNotEqual(client.connect_ex(("127.0.0.1", port)), 0)

    def test_reused_port_preserves_the_unrelated_server(self):
        (self.project / "preview.cjs").write_text('const fs=require("node:fs"),http=require("node:http");fs.writeFileSync(".requested-port",process.argv[2]);const timer=setInterval(()=>{if(fs.existsSync(".contended")){clearInterval(timer);const s=http.createServer();s.on("error",()=>process.exit(2));s.listen(Number(process.argv[2]),"127.0.0.1");}},10);')
        self.write_profile({"type": "node", "command": ["node", "preview.cjs", "{port}"], "timeoutSeconds": 3})

        class OtherProduct(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(204)
                self.send_header("X-Autonomous-Company-Media", "another-product")
                self.end_headers()

            def log_message(self, *args):
                pass

        servers = []

        def contend():
            deadline = time.monotonic() + 10
            requested = self.project / ".requested-port"
            while not requested.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            if requested.exists():
                other = HTTPServer(("127.0.0.1", int(requested.read_text())), OtherProduct)
                servers.append(other)
                (self.project / ".contended").touch()
                other.serve_forever(poll_interval=0.05)

        competitor = threading.Thread(target=contend, daemon=True)
        competitor.start()
        try:
            record = capture_product(self.root, self.name, "contended-port")
            self.assertEqual(record["attempt"]["state"], "failed")
            self.assertNotIn("latestSuccess", record)
            self.assertTrue(servers)
            self.assertTrue(competitor.is_alive())
            connection = http.client.HTTPConnection("127.0.0.1", servers[0].server_port, timeout=1)
            try:
                connection.request("GET", "/")
                response = connection.getresponse()
                self.assertEqual(response.status, 204)
                self.assertEqual(response.getheader("X-Autonomous-Company-Media"), "another-product")
            finally:
                connection.close()
        finally:
            for other in servers:
                other.shutdown()
                other.server_close()
            competitor.join(timeout=2)

    def test_readiness_timeout_cleans_preview_and_does_not_publish_success(self):
        self.node_server(spawn_descendant=True)
        profile = load_profile(self.project)
        profile.update(readySelector="#never-present", timeoutSeconds=1)
        self.write_profile(profile)
        record = capture_product(self.root, self.name, "timeout")
        self.assertEqual(record["attempt"]["state"], "failed")
        self.assertNotIn("latestSuccess", record)
        port = int((self.project / ".preview-port").read_text())
        with socket.socket() as client:
            client.settimeout(1)
            self.assertNotEqual(client.connect_ex(("127.0.0.1", port)), 0)

    @unittest.skipIf(os.name == "nt", "POSIX SIGTERM cleanup is verified on Linux")
    def test_interrupted_capture_reaps_preview_without_waiting_for_watchdog(self):
        self.assert_interrupted_capture_reaps_scope()

    @unittest.skipUnless(Path("/proc").is_dir(), "Deterministic process-scan interruption requires Linux procfs")
    def test_sigterm_during_process_scan_is_not_swallowed(self):
        self.assert_interrupted_capture_reaps_scope(interrupt_scan=True)

    def assert_interrupted_capture_reaps_scope(self, interrupt_scan=False):
        self.node_server(spawn_descendant=True)
        profile = load_profile(self.project)
        profile.update(readySelector="#never-present", timeoutSeconds=15)
        self.write_profile(profile)
        command = [sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"), "--root", str(self.root), "--project", self.name, "media"]
        if interrupt_scan:
            # Deliver a real SIGTERM inside proc_identity's guarded stat read.
            # A ValueError raised by the handler used to disappear there.
            launcher = self.root / "interrupt-scan.py"
            launcher.write_text("""import os, runpy, signal, sys, time
from pathlib import Path
original = Path.read_text
root = Path(sys.argv[1])
injected = False
def read_stat(path, *args, **kwargs):
    global injected
    if not injected and path.name == 'stat' and path.parent.parent == Path('/proc') and (root / 'projects/example/.preview-port').exists():
        injected = True
        (root / 'scan-ready').touch()
        deadline = time.monotonic() + 10
        while not (root / 'interrupt-now').exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        os.kill(os.getpid(), signal.SIGTERM)
    return original(path, *args, **kwargs)
Path.read_text = read_stat
sys.argv = sys.argv[2:]
sys.path.insert(0, str(Path(sys.argv[0]).parent))
from product_media_process import ProcessScope
close_scope = ProcessScope.close
def interrupt_cleanup(scope):
    os.kill(os.getpid(), signal.SIGTERM)
    (root / 'cleanup-interrupted').touch()
    return close_scope(scope)
ProcessScope.close = interrupt_cleanup
runpy.run_path(sys.argv[0], run_name='__main__')
""", encoding="utf-8")
            command = [sys.executable, str(launcher), str(self.root), *command[1:]]
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        scope = ProcessScope(command)
        process = scope.process
        try:
            deadline = time.monotonic() + 10
            ready = self.root / "scan-ready" if interrupt_scan else self.project / ".preview-port"
            while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
                scope.observe()
                time.sleep(0.05)
            self.assertTrue(ready.exists())
            scope.observe()
            owned = dict(scope.members)
            browser_pids = [pid for pid in owned if (path := Path(f"/proc/{pid}/cmdline")).exists()
                            and any(name in path.read_bytes() for name in (b"chromium", b"chrome"))]
            if Path("/proc").is_dir():
                self.assertTrue(browser_pids, "The owned scope must include the real Chromium processes")
            started = time.monotonic()
            if interrupt_scan:
                (self.root / "interrupt-now").touch()
            else:
                process.terminate()
            process.wait(timeout=8)
            self.assertLess(time.monotonic() - started, 8)
            if interrupt_scan:
                self.assertTrue((self.root / "cleanup-interrupted").exists(), "Repeated SIGTERM must not abort cleanup")
            self.assertEqual(media_projection(self.root, self.name)["screenshot"]["state"], "interrupted")
            port = int((self.project / ".preview-port").read_text())
            with socket.socket() as client:
                client.settimeout(1)
                self.assertNotEqual(client.connect_ex(("127.0.0.1", port)), 0)
            pid = int((self.project / ".child-pid").read_text())
            proc = Path(f"/proc/{pid}/stat")
            self.assertTrue(not proc.exists() or proc.read_text().split()[2] == "Z")
            for pid, (birth, _) in owned.items():
                current = proc_identity(pid)
                self.assertTrue(not current or current["start"] != birth or current["state"] == "Z", f"Owned process {pid} survived capture interruption")
            self.assertIsNone(sentinel.poll(), "Unrelated process was stopped")
        finally:
            try:
                scope.close()
            finally:
                sentinel.terminate()
                sentinel.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
