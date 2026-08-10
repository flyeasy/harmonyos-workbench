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
    / "skills/harmonyos-capabilities/scripts/harmony_capability_audit.py"
)


class CapabilityAuditTest(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        (root / "oh-package.json5").write_text("{}\n", encoding="utf-8")
        (root / "hvigorfile.ts").write_text("export default {}\n", encoding="utf-8")
        module = root / "entry/src/main"
        module.mkdir(parents=True)
        (module / "module.json5").write_text(
            """
            {
              requestPermissions: [
                { name: 'ohos.permission.LOCATION' },
                { name: 'ohos.permission.CAMERA' }
              ]
            }
            """,
            encoding="utf-8",
        )
        pages = root / "entry/src/main/ets/pages"
        pages.mkdir(parents=True)
        (pages / "Index.ets").write_text(
            "const intent = insightIntent.shareIntent;\n"
            "const location = geoLocationManager;\n",
            encoding="utf-8",
        )
        generated = root / "build/generated"
        generated.mkdir(parents=True)
        (generated / "ignored.ts").write_text(
            "ohos.permission.READ_CONTACTS\n", encoding="utf-8"
        )
        return root

    def test_inventory_is_hints_only_and_project_relative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_project(Path(directory))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project", str(root), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            record = json.loads(result.stdout)
            self.assertEqual(record["phase"], "capabilities")
            self.assertEqual(record["status"], "needs_verification")
            names = {
                item["name"] for item in record["outputs"]["permissionMentions"]
            }
            self.assertEqual(
                names,
                {"ohos.permission.CAMERA", "ohos.permission.LOCATION"},
            )
            hints = {
                item["name"] for item in record["outputs"]["capabilityHints"]
            }
            self.assertIn("intents", hints)
            self.assertIn("location", hints)
            self.assertNotIn(str(root), result.stdout)

    def test_launcher_exposes_audit(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ROOT / "scripts/harmonyos_workbench.py"),
                "--help",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("capability-audit", result.stdout)


if __name__ == "__main__":
    unittest.main()
