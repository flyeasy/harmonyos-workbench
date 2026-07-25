from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_skill_names_are_unique_and_prefixed(self) -> None:
        names: list[str] = []
        for skill_file in sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, msg=str(skill_file))
            name = match.group(1).strip()
            self.assertTrue(name.startswith("harmonyos-"))
            self.assertEqual(skill_file.parent.name, name)
            names.append(name)
        self.assertEqual(len(names), 9)
        self.assertEqual(len(names), len(set(names)))

    def test_every_capability_uses_the_common_contract(self) -> None:
        for skill_file in sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            self.assertRegex(text, r"(Phase|Capability) contract|统一阶段契约")
            for field in ("Input", "Preflight", "Execute", "Verify", "Evidence", "Handoff"):
                self.assertIn(field, text, msg=f"{field}: {skill_file}")

    def test_no_retired_names_or_todos_remain(self) -> None:
        retired = (
            "build-harmonyos-apps",
            "manage-harmonyos-devices",
            "test-harmonyos-apps",
            "release-harmonyos-apps",
            "review-harmonyos-design",
            "harmonyos-motion-vocabulary",
            "[TODO",
        )
        scan_roots = [PLUGIN_ROOT / "skills", PLUGIN_ROOT / "scripts"]
        for path in (
            path
            for root in scan_roots
            for path in root.rglob("*")
        ):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".md", ".py", ".json", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for value in retired:
                self.assertNotIn(value, text, msg=str(path))

    def test_launcher_targets_exist(self) -> None:
        launcher = PLUGIN_ROOT / "scripts/harmonyos_workbench.py"
        text = launcher.read_text(encoding="utf-8")
        for command in (
            "build",
            "profile",
            "targets",
            "test-plan",
            "test-run",
            "testing-inventory",
            "release",
        ):
            self.assertIn(f'"{command}"', text)

    def test_manifest_declares_skill_root(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "harmonyos-workbench")
        self.assertEqual(manifest["skills"], "./skills/")


if __name__ == "__main__":
    unittest.main()
