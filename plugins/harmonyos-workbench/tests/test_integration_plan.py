from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "skills/harmonyos-test/scripts/harmony_integration_plan.py"


class IntegrationPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        (self.root / "oh-package.json5").write_text("{}\n", encoding="utf-8")
        self.manifest = self.root / "integration.json"
        self.manifest.write_text(
            json.dumps(
                {
                    "schema": "harmonyos.workbench.integration/v1",
                    "integrations": [
                        {
                            "id": "webdav-write",
                            "kind": "external_service",
                            "requiredFor": "release",
                            "execution": "writes_isolated_data",
                            "requiredEnv": ["TEST_URL", "TEST_PASSWORD"],
                            "isolationConfirmationEnv": "TEST_ISOLATED",
                        },
                        {
                            "id": "human-device-path",
                            "kind": "companion_hardware",
                            "execution": "manual",
                            "requiredEnv": [],
                            "evidenceMode": "manual",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_plan(self, *extra: str, expected: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(self.root), "--manifest", str(self.manifest), *extra],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected, msg=completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def test_missing_configuration_blocks_without_echoing_values(self) -> None:
        result = self.run_plan(expected=2)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["items"][0]["missingEnvNames"], ["TEST_URL", "TEST_PASSWORD"])

    def test_isolated_configuration_becomes_ready_without_contacting_service(self) -> None:
        env = self.root / "private.env"
        env.write_text("TEST_URL=https://safe.test\nTEST_PASSWORD=secret-value\nTEST_ISOLATED=yes\n", encoding="utf-8")
        evidence = self.root / "artifacts/integration-plan.json"
        result = self.run_plan("--env-file", str(env), "--evidence", str(evidence))
        self.assertEqual(result["externalCalls"], False)
        self.assertEqual(result["items"][0]["status"], "ready_to_run")
        rendered = evidence.read_text(encoding="utf-8")
        self.assertNotIn("safe.test", rendered)
        self.assertNotIn("secret-value", rendered)


if __name__ == "__main__":
    unittest.main()
