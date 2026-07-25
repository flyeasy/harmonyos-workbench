from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    PLUGIN_ROOT
    / "skills/harmonyos-targets/scripts/harmonyos_targets.py"
)
TEST_RUNNER = PLUGIN_ROOT / "skills/harmonyos-test/scripts/run_test_command.py"
FIXTURE = PLUGIN_ROOT / "tests/fixtures/targets.json"


class TargetsCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state = root / "targets.json"
        self.project_a = root / "project-a"
        self.project_b = root / "project-b"
        self.project_a.mkdir()
        self.project_b.mkdir()
        (self.project_a / "oh-package.json5").write_text("{}\n", encoding="utf-8")
        (self.project_b / "oh-package.json5").write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *arguments: str, expected: int = 0) -> dict[str, object]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--state-file",
            str(self.state),
            "--inventory-file",
            str(FIXTURE),
            *arguments,
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(
            completed.returncode,
            expected,
            msg=f"{completed.stdout}\n{completed.stderr}",
        )
        return json.loads(completed.stdout)

    def test_two_projects_allocate_different_fixed_phones(self) -> None:
        first = self.run_cli(
            "allocate",
            "--project",
            str(self.project_a),
            "--device-type",
            "phone",
            "--api-version",
            "20",
        )
        second = self.run_cli(
            "allocate",
            "--project",
            str(self.project_b),
            "--device-type",
            "phone",
            "--api-version",
            "20",
        )
        self.assertEqual(first["binding"]["name"], "phone-a")
        self.assertEqual(second["binding"]["name"], "phone-b")
        self.assertNotEqual(
            first["binding"]["hdcPort"],
            second["binding"]["hdcPort"],
        )
        repeated = self.run_cli("status", "--project", str(self.project_a))
        self.assertEqual(
            repeated["binding"]["targetKey"],
            first["binding"]["targetKey"],
        )
        reallocated = self.run_cli(
            "allocate",
            "--project",
            str(self.project_a),
            "--device-type",
            "phone",
            "--api-version",
            "20",
        )
        self.assertEqual(reallocated["selection"]["mode"], "existing_binding")
        self.assertEqual(
            reallocated["binding"]["targetKey"],
            first["binding"]["targetKey"],
        )
        self.assertEqual(
            reallocated["binding"]["hdcPort"],
            first["binding"]["hdcPort"],
        )

    def test_preflight_requires_lease_and_writes_matching_evidence(self) -> None:
        self.run_cli(
            "bind",
            "--project",
            str(self.project_a),
            "--emulator-id",
            "phone-a",
        )
        self.run_cli(
            "preflight",
            "--project",
            str(self.project_a),
            expected=2,
        )
        self.run_cli("acquire", "--project", str(self.project_a))
        evidence = Path(self.temp.name) / "target-preflight.json"
        result = self.run_cli(
            "preflight",
            "--project",
            str(self.project_a),
            "--evidence",
            str(evidence),
        )
        self.assertEqual(result["geometry"]["status"], "passed")
        record = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(record["schema"], "harmonyos.workbench.evidence/v2")
        self.assertEqual(record["projectId"], result["projectId"])
        self.assertNotIn(str(self.project_a), evidence.read_text(encoding="utf-8"))
        self.assertNotIn(
            "emulator:11111111-1111-1111-1111-111111111111",
            evidence.read_text(encoding="utf-8"),
        )
        self.assertNotIn("targetKey", record["target"])
        self.assertTrue(record["target"]["targetKeyHash"])
        evidence_dir = Path(self.temp.name) / "test-evidence"
        completed = subprocess.run(
            [
                sys.executable,
                str(TEST_RUNNER),
                "--project",
                str(self.project_a),
                "--state-file",
                str(self.state),
                "--target",
                "emulator",
                "--ui",
                "--target-preflight-evidence",
                str(evidence),
                "--evidence-dir",
                str(evidence_dir),
                "--",
                sys.executable,
                "-c",
                "print('ui-target-ok')",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)
        test_records = list(evidence_dir.glob("*.json"))
        self.assertEqual(len(test_records), 1)
        test_record = json.loads(test_records[0].read_text(encoding="utf-8"))
        rendered_test_record = test_records[0].read_text(encoding="utf-8")
        self.assertNotIn(str(self.project_a), rendered_test_record)
        self.assertNotIn(
            "emulator:11111111-1111-1111-1111-111111111111",
            rendered_test_record,
        )
        self.assertEqual(
            test_record["target"]["targetKeyHash"],
            record["target"]["targetKeyHash"],
        )

    def test_different_specifications_require_narrowing(self) -> None:
        result = self.run_cli(
            "allocate",
            "--project",
            str(self.project_a),
            "--api-version",
            "20",
            expected=2,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("different specifications", str(result["reason"]))


if __name__ == "__main__":
    unittest.main()
