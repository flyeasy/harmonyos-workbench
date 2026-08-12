from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import re
import struct
import tempfile
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
        self.assertEqual(len(names), 11)
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
            "capability-audit",
            "profile",
            "targets",
            "test-plan",
            "test-run",
            "testing-inventory",
            "integration-plan",
            "release",
            "signing-audit",
            "listing-audit",
        ):
            self.assertIn(f'"{command}"', text)

    def test_manifest_declares_skill_root(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "harmonyos-workbench")
        self.assertEqual(manifest["skills"], "./skills/")

    def test_signing_audit_separates_debug_and_release_profile_rules(self) -> None:
        script = PLUGIN_ROOT / "skills/harmonyos-release/scripts/harmony_signing_audit.py"
        spec = importlib.util.spec_from_file_location("harmony_signing_audit", script)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        base = {
            "verified": True,
            "type": "release",
            "bundle": "com.example.app",
            "app_id": "123456789",
            "distribution": "app_gallery",
            "debug_info_present": False,
            "distribution_certificate": "",
        }
        release_errors = module.profile_findings(
            base,
            kind="release",
            expected_bundle="com.example.app",
            expected_app_id="123456789",
            expected_distribution="app_gallery",
            identity_key_hash="identity",
        )
        self.assertEqual(release_errors, ["Profile does not contain one readable distribution certificate"])
        debug_errors = module.profile_findings(
            base,
            kind="debug",
            expected_bundle="com.example.app",
            expected_app_id="",
            expected_distribution="",
            identity_key_hash="identity",
        )
        self.assertIn("Profile type does not match the requested signing kind", debug_errors)
        self.assertIn("debug Profile has no debug device information", debug_errors)

    def test_listing_audit_enforces_opaque_icon_baseline(self) -> None:
        script = PLUGIN_ROOT / "skills/harmonyos-release/scripts/harmony_listing_audit.py"
        spec = importlib.util.spec_from_file_location("harmony_listing_audit", script)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            icon = Path(directory) / "icon.png"
            ihdr = struct.pack(">IIBBBBB", 1024, 1024, 8, 2, 0, 0, 0)
            icon.write_bytes(
                module.PNG_SIGNATURE
                + struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + b"\0\0\0\0"
                + struct.pack(">I", 0) + b"IEND" + b"\0\0\0\0"
            )
            self.assertEqual(module.icon_findings(module.icon_facts(icon)), [])
            alpha_ihdr = struct.pack(">IIBBBBB", 1024, 1024, 8, 6, 0, 0, 0)
            alpha_icon = Path(directory) / "alpha.png"
            alpha_icon.write_bytes(
                module.PNG_SIGNATURE
                + struct.pack(">I", len(alpha_ihdr)) + b"IHDR" + alpha_ihdr + b"\0\0\0\0"
                + struct.pack(">I", 0) + b"IEND" + b"\0\0\0\0"
            )
            self.assertIn(
                "icon must not contain an alpha channel or transparency",
                module.icon_findings(module.icon_facts(alpha_icon)),
            )
        listing, listing_errors = module.listing_facts(
            {
                "locales": {
                    "zh-CN": {
                        "appName": "示例",
                        "oneLineIntroduction": "解决一个真实问题",
                        "introduction": "只描述已验证的功能。",
                        "privacyStatementUrl": "https://example.com/privacy",
                        "privacyStatementVersion": "1.0",
                        "privacyStatementReviewedAt": "2026-08-12",
                        "screenshots": ["store/zh-CN/01.png"],
                    }
                }
            }
        )
        self.assertEqual(listing_errors, [])
        self.assertEqual(listing["locales"]["zh-CN"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
