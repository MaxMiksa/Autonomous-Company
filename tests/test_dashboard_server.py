import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
import unittest
from pathlib import Path
from unittest import mock


SERVER_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "server.py"
# server.py imports its sibling `sentry_client`. Loading it by file path does NOT
# put dashboard/ on sys.path (production gets that for free from `python
# dashboard/server.py`), so without this the whole module fails to import and all
# of these tests are skipped as a single collection error — silently, since a
# missing module reads like an environment problem rather than a dead suite.
sys.path.insert(0, str(SERVER_PATH.parent))
SPEC = importlib.util.spec_from_file_location("dashboard_server", SERVER_PATH)
assert SPEC is not None
assert SPEC.loader is not None
dashboard_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard_server)


class DashboardServerTests(unittest.TestCase):
    def test_windows_not_running_maps_to_stopped(self) -> None:
        raw = """=== Windows Guardian ===
Awake guardian: STOPPED

=== Windows Autostart Task ===
Autostart: NOT CONFIGURED

=== WSL Daemon (systemd --user) ===
active
MainPID=321
ActiveState=active
SubState=running

=== Auto Company Status ===
Loop: NOT RUNNING
Daemon: ACTIVE (systemd --user auto-company.service)
ENGINE=claude
MODEL=sonnet
"""
        parsed = dashboard_server.parse_status_output(raw, system_name="Windows")
        self.assertEqual(parsed["guardian"]["state"], "stopped")
        self.assertEqual(parsed["autostart"]["state"], "not_configured")
        self.assertEqual(parsed["daemon"]["state"], "active")
        self.assertEqual(parsed["loop"]["state"], "stopped")
        self.assertIsNone(parsed["loop"]["pid"])

    def test_windows_not_installed_daemon_maps_correctly(self) -> None:
        raw = """=== Windows Guardian ===
Awake guardian: RUNNING (PID 45)

=== Windows Autostart Task ===
Autostart: CONFIGURED (AutoCompany-WSL-Start)

=== WSL Daemon (systemd --user) ===
auto-company.service: not installed

=== Auto Company Status ===
Loop: RUNNING (PID 77)
Daemon: NOT INSTALLED (systemd --user auto-company.service)
"""
        parsed = dashboard_server.parse_status_output(raw, system_name="Windows")
        self.assertEqual(parsed["guardian"]["state"], "running")
        self.assertEqual(parsed["guardian"]["pid"], 45)
        self.assertEqual(parsed["autostart"]["state"], "configured")
        self.assertEqual(parsed["daemon"]["state"], "not_installed")
        self.assertEqual(parsed["loop"]["state"], "running")
        self.assertEqual(parsed["loop"]["pid"], 77)

    def test_macos_active_configured_running_maps_correctly(self) -> None:
        raw = """=== Guardian ===
State=running
Pid=111
Raw=caffeinate -w 456

=== Daemon ===
State=active
MainPID=222
Raw=launchd agent loaded

=== Autostart ===
State=configured
Raw=LaunchAgent plist present

=== Loop ===
State=running
Pid=456
Raw=Loop running

=== State File ===
ENGINE=claude
MODEL=sonnet
LOOP_COUNT=9
ERROR_COUNT=0
LAST_RUN=2026-03-14 12:00:00
"""
        parsed = dashboard_server.parse_status_output(raw, system_name="Darwin")
        self.assertEqual(parsed["guardian"]["state"], "running")
        self.assertEqual(parsed["guardian"]["pid"], 111)
        self.assertEqual(parsed["daemon"]["state"], "active")
        self.assertEqual(parsed["daemon"]["mainPid"], 222)
        self.assertEqual(parsed["autostart"]["state"], "configured")
        self.assertEqual(parsed["loop"]["state"], "running")
        self.assertEqual(parsed["loop"]["pid"], 456)
        self.assertEqual(parsed["loop"]["engine"], "claude")
        self.assertEqual(parsed["loop"]["loopCount"], "9")

    def test_macos_inactive_configured_stopped_and_guardian_without_caffeinate(self) -> None:
        raw = """=== Guardian ===
State=stopped
Raw=Sleep guard: loop running without caffeinate

=== Daemon ===
State=inactive
Raw=LaunchAgent paused (.auto-loop-paused present)

=== Autostart ===
State=configured
Raw=LaunchAgent plist present

=== Loop ===
State=stopped
Raw=Loop stopped (stale PID 456)
"""
        parsed = dashboard_server.parse_status_output(raw, system_name="Darwin")
        self.assertEqual(parsed["guardian"]["state"], "stopped")
        self.assertEqual(parsed["daemon"]["state"], "inactive")
        self.assertEqual(parsed["autostart"]["state"], "configured")
        self.assertEqual(parsed["loop"]["state"], "stopped")

    def test_macos_not_installed_maps_correctly(self) -> None:
        raw = """=== Guardian ===
State=stopped
Raw=Sleep guard: not active

=== Daemon ===
State=not_installed
Raw=LaunchAgent plist not installed

=== Autostart ===
State=not_configured
Raw=LaunchAgent plist absent

=== Loop ===
State=stopped
Raw=Loop not running
"""
        parsed = dashboard_server.parse_status_output(raw, system_name="Darwin")
        self.assertEqual(parsed["daemon"]["state"], "not_installed")
        self.assertEqual(parsed["autostart"]["state"], "not_configured")
        self.assertEqual(parsed["loop"]["state"], "stopped")

    def test_windows_start_uses_powershell_runner(self) -> None:
        with mock.patch.object(
            dashboard_server,
            "run_powershell_script",
            return_value={"ok": True, "exitCode": 0, "elapsedMs": 1, "output": ""},
        ) as runner:
            result = dashboard_server.run_dashboard_action("start", system_name="Windows")
        self.assertTrue(result["ok"])
        runner.assert_called_once_with(
            dashboard_server.WINDOWS_START_SCRIPT, args=None, timeout=120
        )

    def test_macos_stop_uses_shell_runner_with_pause_daemon(self) -> None:
        with mock.patch.object(
            dashboard_server,
            "run_shell_script",
            return_value={"ok": True, "exitCode": 0, "elapsedMs": 1, "output": ""},
        ) as runner:
            result = dashboard_server.run_dashboard_action("stop", system_name="Darwin")
        self.assertTrue(result["ok"])
        runner.assert_called_once_with(
            dashboard_server.MACOS_STOP_SCRIPT,
            args=["--pause-daemon"],
            timeout=120,
        )

    def test_refresh_uses_status_script(self) -> None:
        with mock.patch.object(
            dashboard_server,
            "run_shell_script",
            return_value={"ok": True, "exitCode": 0, "elapsedMs": 1, "output": ""},
        ) as runner:
            dashboard_server.run_dashboard_action("refresh", system_name="Darwin")
        runner.assert_called_once_with(
            dashboard_server.MACOS_STATUS_SCRIPT, timeout=90
        )

    def test_invalid_log_tail_lines_fall_back_to_default(self) -> None:
        self.assertEqual(dashboard_server.parse_positive_int("abc", default=180), 180)
        self.assertEqual(dashboard_server.parse_positive_int("-5", default=180), 180)
        self.assertEqual(dashboard_server.parse_positive_int("12", default=180), 12)

    def test_unsupported_host_raises(self) -> None:
        # Was asserting that "Linux" raises. Linux/container support was added to
        # detect_host_kind() (the company itself runs in a Linux container) but
        # this test was never updated, so it had been failing independently of
        # the change it now sits beside. Assert the real contract instead:
        # Windows/Darwin/Linux resolve, anything else raises.
        self.assertEqual(dashboard_server.detect_host_kind("Linux"),
                         dashboard_server.LINUX_HOST)
        with self.assertRaisesRegex(RuntimeError, "only supports Windows"):
            dashboard_server.detect_host_kind("Plan9")


# auto-loop.log is persistent across redeploys, so the Runtime State panel is
# parsing a file that contains every historical boot. These cover the 2026-07-28
# regressions where three fields were pinned to a 2026-07-21 boot line.
STALE_THEN_CURRENT_LOG = """\
[2026-07-21 19:02:10] Interval: 60s | Timeout: 1800s | Breaker: 5 errors
[2026-07-21 19:02:10] Window budget: $8 per 18000s (pause 1800s when reached)
[2026-07-21 19:02:10] Tier ladder: ON (round-robin) | \
Claude [claude-haiku-4-5-20251001,claude-sonnet-5] | Codex effort [low,medium]
[2026-07-21 19:02:11] [ROUTER] Alternate -> Claude (old)
[2026-07-21 19:02:11] [TIER] round-robin -> Claude=claude-haiku-4-5-20251001 \
[claude $0.10/8], Codex effort=medium [codex 0/5]
[2026-07-28 08:59:17] Interval: 900s | Timeout: 1800s | Breaker: 5 errors
[2026-07-28 08:59:17] Window budget: $40 per 18000s (pause 1800s when reached)
[2026-07-28 08:59:17] Tier ladder: ON (round-robin) | \
Claude [claude-sonnet-5:low,claude-sonnet-5:high,claude-opus-5:high] | \
Codex effort [low,medium,high]
[2026-07-28 08:59:17] [ROUTER] Alternate -> Claude (both have headroom)
[2026-07-28 08:59:17] [TIER] fill-weighted -> Claude=claude-opus-5 effort=high \
[claude $3.1630/40.00], Codex effort=low [codex 1/inf]
"""


class EngineRuntimeParsingTests(unittest.TestCase):
    """read_engine_runtime() must reflect the LATEST boot, not the first one."""

    def _run(self, log_text: str, router_state: str) -> dict:
        def fake_read(path, default=""):
            return router_state if path.name == "router-state" else log_text

        with mock.patch.object(dashboard_server, "read_text_file", fake_read):
            return dashboard_server.read_engine_runtime()

    def test_claude_cycle_reports_its_effort(self) -> None:
        # Regression: routedEffort was hardcoded "" on the Claude branch, so the
        # panel could never show which rung ran — and the live ladder's rungs
        # differ only by effort.
        out = self._run(STALE_THEN_CURRENT_LOG, "claude")
        self.assertEqual(out["routedEngine"], "claude")
        self.assertEqual(out["routedModel"], "claude-opus-5")
        self.assertEqual(out["routedEffort"], "high")
        self.assertEqual(out["claudeEffort"], "high")

    def test_codex_cycle_still_reports_codex_effort(self) -> None:
        out = self._run(STALE_THEN_CURRENT_LOG, "codex")
        self.assertEqual(out["routedEffort"], "low")
        # The Claude-ladder pick is still surfaced separately on a Codex cycle.
        self.assertEqual(out["claudePick"], "claude-opus-5")

    def test_window_budget_and_ladders_take_the_latest_boot(self) -> None:
        # Regression: re.search() returned the FIRST match, so the panel showed
        # a $8 cap and a haiku/sonnet ladder days after both had changed.
        out = self._run(STALE_THEN_CURRENT_LOG, "claude")
        self.assertEqual(out["windowBudget"], "40")
        self.assertEqual(out["interval"], "900")
        self.assertEqual(
            out["claudeLadder"],
            ["claude-sonnet-5:low", "claude-sonnet-5:high", "claude-opus-5:high"],
        )
        self.assertEqual(out["codexLadder"], ["low", "medium", "high"])

    def test_legacy_tier_line_without_claude_effort_still_parses(self) -> None:
        # Pre-APP-241 lines carry no `effort=` after the model. Requiring it
        # would silently fall back to an even older line.
        legacy_only = (
            "[2026-07-21 19:02:10] Window budget: $8 per 18000s (pause 1800s when reached)\n"
            "[2026-07-21 19:02:11] [TIER] round-robin -> Claude=claude-sonnet-5 "
            "[claude $0.10/8], Codex effort=medium [codex 0/5]\n"
        )
        out = self._run(legacy_only, "claude")
        self.assertEqual(out["routedModel"], "claude-sonnet-5")
        self.assertEqual(out["routedEffort"], "")
        self.assertEqual(out["codexEffort"], "medium")

    # --- read_settings: distinguish "nothing set it" from "Coolify set it" ------
    #
    # A blank runtime.env entry is not the same as an unconfigured knob. MODEL and
    # CLAUDE_EFFORT live in Coolify and not in runtime.env, so the panel rendered
    # them as empty and an operator would reasonably read that as "unset".

    def _settings(self, file_text: str, environ: dict):
        with mock.patch.object(
            dashboard_server, "read_text_file", lambda *a, **k: file_text
        ), mock.patch.dict(dashboard_server.os.environ, environ, clear=True):
            return dashboard_server.read_settings()

    def test_settings_source_runtime_env_wins(self) -> None:
        out = self._settings(
            "LOOP_INTERVAL=900\n", {"LOOP_INTERVAL": "3600"}
        )
        self.assertEqual(out["effective"]["LOOP_INTERVAL"], "900")
        self.assertEqual(out["source"]["LOOP_INTERVAL"], "runtime.env")

    def test_settings_source_container_when_absent_from_file(self) -> None:
        out = self._settings("", {"MODEL": "claude-haiku-4-5-20251001"})
        self.assertEqual(out["effective"]["MODEL"], "claude-haiku-4-5-20251001")
        self.assertEqual(out["source"]["MODEL"], "container")
        # The raw runtime.env view stays empty — that is what the editor writes to.
        self.assertEqual(out["values"]["MODEL"], "")

    def test_settings_source_default_when_nowhere(self) -> None:
        out = self._settings("", {})
        self.assertEqual(out["source"]["MODEL"], "default")
        self.assertEqual(out["effective"]["MODEL"], "")

    # --- an escalated cycle must report what RAN, not what the ladder picked ----
    #
    # [TIER] is written before apply_cycle_escalation() overrides the model, so
    # reading only [TIER] made Runtime State claim claude-sonnet-5 for a cycle
    # that executed claude-opus-5:high (observed live 2026-07-28 14:07:56).

    ESCALATED_LOG = (
        "Tier ladder: ON | Claude [claude-sonnet-5:low] | Codex effort [low]\n"
        "Window budget: $40 per 18000s\n"
        "[TIER] fill-weighted \u2192 Claude=claude-sonnet-5 effort=high [claude $7/40], "
        "Codex effort=low [codex 4/\u221e]\n"
        "[ESCALATE] one-shot 'claude-opus-5:high' CONSUMED \u2014 "
        "model=claude-opus-5 effort=high timeout=1800s\n"
    )

    def _runtime(self, log_text: str, engine: str = "claude"):
        def fake_read(path, default="", *a, **k):
            return engine if str(path).endswith("router-state") else log_text

        with mock.patch.object(dashboard_server, "read_text_file", fake_read), \
             mock.patch.object(
                 dashboard_server, "read_text_file_tail",
                 lambda *a, **k: log_text):
            return dashboard_server.read_engine_runtime()

    def test_escalated_cycle_reports_the_escalated_model(self) -> None:
        out = self._runtime(self.ESCALATED_LOG)
        self.assertEqual(out["routedModel"], "claude-opus-5")
        self.assertEqual(out["routedEffort"], "high")
        self.assertTrue(out.get("escalated"))
        # The ladder's own pick is still reported separately, unchanged.
        self.assertEqual(out["claudePick"], "claude-sonnet-5")

    def test_escalation_before_the_tier_line_is_ignored(self) -> None:
        # A consumed escalation from an EARLIER cycle must not leak into this one.
        stale = (
            "[ESCALATE] one-shot 'claude-opus-5:high' CONSUMED \u2014 "
            "model=claude-opus-5 effort=high timeout=1800s\n"
            "Tier ladder: ON | Claude [claude-sonnet-5:low] | Codex effort [low]\n"
            "Window budget: $40 per 18000s\n"
            "[TIER] fill-weighted \u2192 Claude=claude-sonnet-5 effort=low [claude $9/40], "
            "Codex effort=low [codex 4/\u221e]\n"
        )
        out = self._runtime(stale)
        self.assertEqual(out["routedModel"], "claude-sonnet-5")
        self.assertEqual(out["routedEffort"], "low")
        self.assertNotIn("escalated", out)

    def test_codex_cycle_ignores_escalation_entirely(self) -> None:
        out = self._runtime(self.ESCALATED_LOG, engine="codex")
        self.assertNotEqual(out["routedModel"], "claude-opus-5")
        self.assertNotIn("escalated", out)


class WindowCutoffTests(unittest.TestCase):
    """The dashboard must measure spend over the SAME window the loop enforces.

    auto-loop.sh anchors on ccusage's blockStart (the current Claude billing
    block) and only falls back to rolling now-5h. The dashboard used the rolling
    bound unconditionally and then printed the result against the loop's cap.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logdir = Path(self._tmp.name)
        self.usage = self.logdir / "operator-usage.json"
        self.patch = mock.patch.object(
            dashboard_server, "LOG_FILE", self.logdir / "auto-loop.log"
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self._tmp.cleanup()

    def _write(self, payload: str, age_secs: float = 0.0):
        self.usage.write_text(payload, encoding="utf-8")
        if age_secs:
            old = time.time() - age_secs
            os.utime(self.usage, (old, old))

    def test_fresh_blockstart_anchors_the_window(self):
        start = datetime.now(timezone.utc) - timedelta(seconds=1200)
        self._write(json.dumps({"blockStart": start.isoformat().replace("+00:00", "Z")}))
        rolling = time.time() - 18000
        cutoff = dashboard_server._window_cutoff_epoch()
        self.assertAlmostEqual(cutoff, start.timestamp(), delta=2)
        self.assertGreater(cutoff, rolling)

    def test_stale_usage_file_falls_back_to_rolling(self):
        start = datetime.now(timezone.utc) - timedelta(seconds=1200)
        self._write(
            json.dumps({"blockStart": start.isoformat().replace("+00:00", "Z")}),
            age_secs=1800,  # older than OPERATOR_USAGE_STALE_SECS (900)
        )
        self.assertAlmostEqual(
            dashboard_server._window_cutoff_epoch(), time.time() - 18000, delta=2
        )

    def test_blockstart_older_than_rolling_never_widens_the_window(self):
        start = datetime.now(timezone.utc) - timedelta(seconds=40000)
        self._write(json.dumps({"blockStart": start.isoformat().replace("+00:00", "Z")}))
        self.assertAlmostEqual(
            dashboard_server._window_cutoff_epoch(), time.time() - 18000, delta=2
        )

    def test_missing_or_unparseable_file_falls_back(self):
        for payload in (None, "not json", json.dumps({}), json.dumps({"blockStart": "?"})):
            with self.subTest(payload=payload):
                if payload is None:
                    self.usage.unlink(missing_ok=True)
                else:
                    self._write(payload)
                self.assertAlmostEqual(
                    dashboard_server._window_cutoff_epoch(), time.time() - 18000, delta=2
                )


class DirectorPanelAppendTests(unittest.TestCase):
    """Director panel writes by APPEND (2026-10-13), never by whole-body replace.

    Real directive_writer.py against a temp AC_APP_DIR, so the panel is tested
    through the same gates (PENDING, size brake, backup, audit) as production.
    """

    MAIN = ("## Kaynak belgeler\n\nTablo.\n\n# ANA DİREKTİF\n## WOWCAR 2.0 ŞİRKET\n\n"
            "### 1. Görev\nAna metin satırı.\n\n## Operatör açıklaması\n\nNot.\n\n")
    BODY = MAIN + ("## ARŞİV 4 — eski tur\n\nÖzet.\n\n"
                   "## KAYIT DÜZENLEME GÜVENLİĞİ — kural\n\nKalıcı kural.\n")

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.app = Path(self.td.name)
        (self.app / "memories").mkdir(parents=True)
        self.env = {**os.environ, "AC_APP_DIR": str(self.app), "AC_ACTOR": "test"}
        body = self.app / "b.md"
        body.write_text(self.BODY, encoding="utf-8")
        self._w("write", "--body-file", str(body))
        sha = self._show()["body_sha256"]
        self._w("status", "--expect-status", "PENDING", "--to", "DONE", "--expect-body-sha256", sha)
        self.patches = [
            mock.patch.object(dashboard_server, "DIRECTIVE_APP_DIR", self.app),
            mock.patch.object(dashboard_server, "DIRECTIVE_FILE", self.app / "memories" / "human-directive.md"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.td.cleanup()

    def _w(self, *argv: str) -> None:
        r = subprocess.run([sys.executable, str(dashboard_server.DIRECTIVE_WRITER), *argv],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def _show(self) -> dict:
        r = subprocess.run([sys.executable, str(dashboard_server.DIRECTIVE_WRITER), "show"],
                           capture_output=True, text=True, env=self.env)
        return dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)

    def _live(self) -> str:
        return (self.app / "memories" / "human-directive.md").read_text(encoding="utf-8")

    def test_send_on_done_appends_and_keeps_body(self) -> None:
        out = dashboard_server.write_directive("İki satırlık operatör notu.\nİkinci satır.")
        live = self._live()
        self.assertEqual(out["status"], "PENDING")
        self.assertIn("Ana metin satırı.", live)            # ANA DİREKTİF intact
        self.assertIn("## KAYIT DÜZENLEME GÜVENLİĞİ", live)  # earlier section intact
        self.assertIn("## OPERATÖR DİREKTİFİ — cockpit ", live)
        self.assertTrue(live.rstrip().endswith("İkinci satır."))

    def test_inner_headings_are_demoted_to_one_section(self) -> None:
        before = len(dashboard_server.read_directive()["sections"])
        dashboard_server.write_directive("Şablon başlangıcı\n\n## Decision\nKarar.\n# Büyük başlık\nSon.")
        live = self._live()
        self.assertIn("### Decision", live)
        self.assertIn("### Büyük başlık", live)
        self.assertNotIn("\n## Decision", live)
        self.assertEqual(len(dashboard_server.read_directive()["sections"]), before + 1)

    def test_own_heading_is_kept(self) -> None:
        dashboard_server.write_directive("## YENİ İŞ — test\n\nMadde 1.\n## alt\nMadde 2.")
        live = self._live()
        self.assertIn("\n## YENİ İŞ — test\n", live)
        self.assertNotIn("OPERATÖR DİREKTİFİ — cockpit", live)
        self.assertIn("### alt", live)

    def test_pending_gate_then_allow_pending_appends(self) -> None:
        dashboard_server.write_directive("Birinci ek.")
        with self.assertRaises(dashboard_server.DirectiveRefused) as cm:
            dashboard_server.write_directive("İkinci ek.")
        self.assertIn("PENDING", str(cm.exception))
        dashboard_server.write_directive("İkinci ek.", allow_pending=True)
        live = self._live()
        self.assertIn("Birinci ek.", live)
        self.assertIn("İkinci ek.", live)
        self.assertIn("Ana metin satırı.", live)

    def test_sections_summary_partitions_body(self) -> None:
        d = dashboard_server.read_directive()
        kinds = [s["kind"] for s in d["sections"]]
        self.assertEqual(kinds, ["main", "archive", "active"])
        self.assertEqual(sum(s["bytes"] for s in d["sections"]), d["bodyBytes"])
        self.assertEqual(d["sections"][2]["heading"], "KAYIT DÜZENLEME GÜVENLİĞİ — kural")
        self.assertEqual(d["warnBytes"], dashboard_server.DIRECTIVE_WARN_BYTES)

    def test_english_body_kinds(self) -> None:
        # K-2 (2026-10-16): the live directive is English; ARCHIVE counts as archive and the
        # English protected headings stay inside the main chunk.
        en = ("## Source documents and locations\n\nTable.\n\n# MAIN DIRECTIVE\n## WOWCAR 2.0 COMPANY\n\n"
              "### 15. Authority limits\nText.\n\n## Operator note (given together with the directive)\n\nNote.\n\n"
              "## ARCHIVE 4 — old round\n\nSummary.\n\n## RECORD EDIT SAFETY — rule\n\nStanding rule.\n")
        body = self.app / "en.md"
        body.write_text(en, encoding="utf-8")
        self._w("write", "--body-file", str(body), "--allow-pending")
        d = dashboard_server.read_directive()
        self.assertEqual([s["kind"] for s in d["sections"]], ["main", "archive", "active"])
        self.assertEqual(sum(s["bytes"] for s in d["sections"]), d["bodyBytes"])

    def test_sections_empty_when_writer_unloadable(self) -> None:
        with mock.patch.object(dashboard_server, "_directive_writer_mod", None), \
             mock.patch.object(dashboard_server, "DIRECTIVE_WRITER", self.app / "missing.py"):
            d = dashboard_server.read_directive()
        self.assertEqual(d["sections"], [])
        self.assertEqual(d["status"], "DONE")
        self.assertIn("Ana metin satırı.", d["directive"])


if __name__ == "__main__":
    unittest.main()


class ReadTextFileTailTests(unittest.TestCase):
    """auto-loop.log is persistent and ever-growing; the status poll must not
    re-parse all of it. Correctness rule: everything read from it takes the LAST
    match, so a tail is fine — but the once-per-boot banner must still be found."""

    def _tmp(self, content: bytes):
        import tempfile
        d = tempfile.mkdtemp()
        p = Path(d) / "auto-loop.log"
        p.write_bytes(content)
        return p

    def test_returns_whole_file_when_smaller_than_window(self) -> None:
        p = self._tmp(b"line one\nline two\n")
        self.assertEqual(
            dashboard_server.read_text_file_tail(p, 1_000_000), "line one\nline two\n"
        )

    def test_truncates_to_the_tail_and_drops_the_partial_first_line(self) -> None:
        body = ("".join(f"line {i}\n" for i in range(1000))).encode()
        p = self._tmp(body)
        out = dashboard_server.read_text_file_tail(p, 200)
        self.assertLessEqual(len(out.encode()), 200)
        self.assertTrue(out.endswith("line 999\n"))
        # never starts mid-line
        self.assertTrue(out.startswith("line "))

    def test_multibyte_seek_does_not_produce_replacement_junk(self) -> None:
        body = ("".join(f"satır-{i} ölçüm\n" for i in range(500))).encode("utf-8")
        p = self._tmp(body)
        out = dashboard_server.read_text_file_tail(p, 201)
        self.assertNotIn("�", out)

    def test_missing_file_returns_fallback(self) -> None:
        self.assertEqual(
            dashboard_server.read_text_file_tail(Path("/nope/none.log"), 100, "fb"), "fb"
        )

    def test_engine_runtime_falls_back_to_full_file_when_banner_is_out_of_window(self) -> None:
        # Banner at the very top, then more than the window's worth of churn after it.
        banner = (
            "Tier ladder: ON (round-robin) | Claude [claude-sonnet-5:low] | "
            "Codex effort [low,medium]\n"
            "Window budget: $40 per 18000s (pause 1800s when reached)\n"
        )
        churn = "".join(f"[TIER] fill-weighted -> Claude=m{i} effort=low [claude $1/40], "
                        f"Codex effort=low [codex 1/2]\n" for i in range(3000))
        p = self._tmp((banner + churn).encode())

        def fake_read(path, default=""):
            return "claude" if path.name == "router-state" else p.read_text()

        with mock.patch.object(dashboard_server, "LOG_FILE", p), \
             mock.patch.object(dashboard_server, "ENGINE_RUNTIME_TAIL_BYTES", 2000), \
             mock.patch.object(dashboard_server, "read_text_file", fake_read):
            out = dashboard_server.read_engine_runtime()
        # Recovered from the full file rather than silently losing the fields.
        self.assertEqual(out["windowBudget"], "40")
        self.assertEqual(out["claudeLadder"], ["claude-sonnet-5:low"])


class WeeklyCostWindowTests(unittest.TestCase):
    """Haftalık görüntü sıfırlaması (operatör kararı 2026-08-24): manşet sayaçlar
    Pazartesi 00:00 UTC'den başlar; all-time toplamlar aynen korunur; damgasız
    satır haftalığa asla sayılmaz (fail-safe)."""

    def _summary_for(self, log_text: str):
        with mock.patch.object(dashboard_server, "read_text_file",
                               lambda p, d="": log_text if p == dashboard_server.LOG_FILE else ""), \
             mock.patch.object(dashboard_server, "read_ccusage", lambda: {"available": False}):
            return dashboard_server.read_cost_summary()

    @staticmethod
    def _stamp(dt):
        return dt.strftime("[%Y-%m-%d %H:%M:%S]")

    def test_week_window_splits_old_and_new_costs(self):
        now = datetime.now(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        old = monday - timedelta(days=3)     # geçen hafta
        new = monday + timedelta(hours=1)    # bu hafta
        log = "\n".join([
            f"{self._stamp(old)} Cycle #1 [OK] Completed (cost: 5.0, subtype: success)",
            f"{self._stamp(old)} [LIMIT] hit",
            f"{self._stamp(new)} Cycle #2 [OK] Completed (cost: 2.5, subtype: success)",
            f"{self._stamp(new)} [GATE] Daily TOTAL exceeded — pausing BOTH engines",
            f"{self._stamp(new)} [BUDGET] Claude 5h $0/$∞",
        ])
        out = self._summary_for(log)
        self.assertEqual(out["totalUsd"], 7.5)          # all-time: her iki hafta
        self.assertEqual(out["weekUsd"], 2.5)           # yalnız bu hafta
        self.assertEqual(out["weekCycles"], 1)
        self.assertEqual(out["weekLimitHits"], 0)       # LIMIT geçen haftadaydı
        self.assertEqual(out["weekGatePauses"], 1)      # gerçek pause sayılır
        # [BUDGET] durum satırı pause DEĞİLDİR — eski 487'lik yanılgının testi:
        self.assertEqual(out["weekStart"], monday.strftime("%Y-%m-%d"))

    def test_unstamped_cost_line_counts_all_time_only(self):
        now = datetime.now(timezone.utc)
        log = "\n".join([
            "Cycle #9 [OK] Completed (cost: 3.0, subtype: success)",  # damgasız (eski biçim)
            f"{self._stamp(now)} Cycle #10 [OK] Completed (cost: 1.0, subtype: success)",
        ])
        out = self._summary_for(log)
        self.assertEqual(out["totalUsd"], 4.0)
        self.assertEqual(out["weekUsd"], 1.0)


class LiveBudgetGateDisplayTests(unittest.TestCase):
    """'Budget / interval: $40 cap' fosili (operatör buldu, 2026-08-24): eski
    'Window budget' satırı 07-30'da emekli oldu ama kalıcı logdaki Temmuz satırı
    paneli besliyordu. Canlı 'Budget gates' bannerı ve [BUDGET] gate satırı
    parse edilmeli; fosil yalnız fallback."""

    def test_engine_runtime_parses_live_gate_banner_last_match(self):
        log = (
            "[2026-07-22 10:00:00] Window budget: $40 per 18000s\n"
            "[2026-08-24 09:46:36] Interval: 3600s | Timeout: 1200s\n"
            "[2026-08-24 09:46:36] Budget gates (all notional): Claude 5h $∞ | "
            "Codex 5h $∞ | Daily TOTAL $500 (UTC day) | Weekly TOTAL $2500 (rolling)\n"
        )
        with mock.patch.object(dashboard_server, "read_text_file",
                               lambda p, d="": log if p == dashboard_server.LOG_FILE else ""):
            out = dashboard_server.read_engine_runtime()
        self.assertEqual(out["dailyBudget"], "500")
        self.assertEqual(out["weeklyBudget"], "2500")
        self.assertEqual(out["windowBudget"], "40")  # fosil yalnız fallback alanı

    def test_cost_summary_carries_last_budget_gate_line(self):
        now = datetime.now(timezone.utc)
        stamp = now.strftime("[%Y-%m-%d %H:%M:%S]")
        log = (
            f"{stamp} [BUDGET] Claude 5h $0/$∞ | Codex 5h $1/$∞ | "
            "Daily TOTAL $10.6360/$500 | Weekly TOTAL $28.4601/$2500\n"
            f"{stamp} Cycle #1 [OK] Completed (cost: 1.0, subtype: success)\n"
        )
        with mock.patch.object(dashboard_server, "read_text_file",
                               lambda p, d="": log if p == dashboard_server.LOG_FILE else ""), \
             mock.patch.object(dashboard_server, "read_ccusage", lambda: {"available": False}):
            out = dashboard_server.read_cost_summary()
        self.assertEqual(out["gateDailyUsd"], 10.636)
        self.assertEqual(out["gateDailyCap"], 500.0)
        self.assertEqual(out["gateWeeklyCap"], 2500.0)


class GraftFreshnessTests(unittest.TestCase):
    """read_graft_freshness fails open — the container cockpit has no local
    graft-freshness.json (no .git, no local hook) and must show n/a, never crash."""

    def test_absent_file_reports_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(dashboard_server, "REPO_ROOT", Path(td)):
                self.assertEqual(dashboard_server.read_graft_freshness(),
                                 {"available": False})

    def test_valid_status_passthrough(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"
            logs.mkdir()
            (logs / "graft-freshness.json").write_text(
                json.dumps({"available": True, "behind": 3, "age_h": 5.0,
                            "refreshing": False}))
            with mock.patch.object(dashboard_server, "REPO_ROOT", Path(td)):
                out = dashboard_server.read_graft_freshness()
        self.assertTrue(out["available"])
        self.assertEqual(out["behind"], 3)

    def test_malformed_json_reports_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"
            logs.mkdir()
            (logs / "graft-freshness.json").write_text("{ not valid json")
            with mock.patch.object(dashboard_server, "REPO_ROOT", Path(td)):
                self.assertEqual(dashboard_server.read_graft_freshness(),
                                 {"available": False})
