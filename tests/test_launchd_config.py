import importlib.util
from pathlib import Path
import plistlib
import unittest


SPEC = importlib.util.spec_from_file_location(
    "launchd_config", Path(__file__).resolve().parents[1] / "scripts/core/launchd-config.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LaunchdConfigTests(unittest.TestCase):
    def loaded_config(self):
        project = str(Path(__file__).resolve().parents[1])
        # launchd job_export() omits WorkingDirectory and environment settings.
        config = {"Label": "com.autonomouscompany.loop", "PID": 123, "LastExitStatus": 0,
                  "ProgramArguments": ["/bin/bash", project + "/scripts/core/auto-loop.sh", "--daemon"]}
        return project, config

    def test_loaded_agent_without_working_directory_is_validated_by_command(self):
        project, config = self.loaded_config()
        MODULE.validate(project, config, loaded=True)

    def test_disk_plist_still_requires_working_directory(self):
        project, config = self.loaded_config()
        with self.assertRaisesRegex(ValueError, "WorkingDirectory"):
            MODULE.validate(project, config)

    def test_loaded_agent_with_working_directory_still_checks_it(self):
        project, config = self.loaded_config()
        config["WorkingDirectory"] = project
        MODULE.validate(project, config, loaded=True)
        for directory in (project + "/foreign", None, 123):
            with self.subTest(directory=directory):
                config["WorkingDirectory"] = directory
                with self.assertRaisesRegex(ValueError, "WorkingDirectory"):
                    MODULE.validate(project, config, loaded=True)

    def test_loaded_agent_without_working_directory_rejects_foreign_identity(self):
        project, config = self.loaded_config()
        for update in ({"Label": "com.foreign.loop"}, {"Program": "/bin/sh"},
                       {"ProgramArguments": ["/bin/bash", project + "/foreign/auto-loop.sh", "--daemon"]},
                       {"ProgramArguments": ["/bin/bash", "scripts/core/auto-loop.sh", "--daemon"]}):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    MODULE.validate(project, dict(config, **update), loaded=True)

    def test_runtime_budget_and_timeout_survive_install(self):
        env = {
            "HOME": "/Users/test", "ENGINE": "codex",
            "AUTONOMOUS_COMPANY_LANGUAGE": "en",
            "CODEX_SANDBOX_MODE": "workspace-write", "CYCLE_TIMEOUT_SECONDS": "80",
            "CYCLE_TERM_GRACE_SECONDS": "2", "USAGE_BUDGET_PERIOD": "week",
            "USAGE_HARD_LIMIT_TOKENS": "10000", "USAGE_WARNING_USD": "2",
            "OPENAI_COMPATIBLE_API_KEY": "secret-api-sentinel",
            "CURSOR_API_KEY": "secret-cursor-sentinel", "UNRELATED": "not-runtime",
        }
        raw = MODULE.render("/Users/test/repo", "/bin", env)
        actual = plistlib.loads(raw)["EnvironmentVariables"]
        for key in ("ENGINE", "AUTONOMOUS_COMPANY_LANGUAGE", "CODEX_SANDBOX_MODE", "CYCLE_TIMEOUT_SECONDS",
                    "CYCLE_TERM_GRACE_SECONDS", "USAGE_BUDGET_PERIOD",
                    "USAGE_HARD_LIMIT_TOKENS", "USAGE_WARNING_USD"):
            self.assertEqual(actual[key], env[key])
        self.assertNotIn(b"secret-", raw)
        self.assertNotIn("UNRELATED", actual)

    def test_xml_special_characters_preserve_exact_configuration(self):
        project = '/Users/test/Research & Development/"trial"'
        model = 'model<&"test>'
        payload = plistlib.loads(MODULE.render(project, "/tools & more:/bin", {
            "HOME": "/Users/test", "MODEL": model,
        }))
        self.assertEqual(payload["WorkingDirectory"], project)
        self.assertEqual(payload["ProgramArguments"][1], project + "/scripts/core/auto-loop.sh")
        self.assertEqual(payload["EnvironmentVariables"]["MODEL"], model)
        self.assertEqual(payload["KeepAlive"]["PathState"], {project + "/.auto-loop-paused": False})


if __name__ == "__main__":
    unittest.main()
