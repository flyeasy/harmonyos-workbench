#!/usr/bin/env python3
"""Stable launcher for every HarmonyOS Workbench capability."""

from __future__ import annotations

import os
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "build": PLUGIN_ROOT / "skills/harmonyos-build/scripts/harmony_build.py",
    "profile": PLUGIN_ROOT / "skills/harmonyos-build/scripts/inspect_harmony_profile.py",
    "targets": PLUGIN_ROOT / "skills/harmonyos-targets/scripts/harmonyos_targets.py",
    "test-plan": PLUGIN_ROOT / "skills/harmonyos-test/scripts/harmony_test_plan.py",
    "test-run": PLUGIN_ROOT / "skills/harmonyos-test/scripts/run_test_command.py",
    "testing-inventory": PLUGIN_ROOT
    / "skills/harmonyos-test/scripts/deveco_task_inventory.py",
    "release": PLUGIN_ROOT
    / "skills/harmonyos-release/scripts/harmony_release_preflight.py",
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: harmonyos_workbench.py <command> [arguments]")
        print("commands: " + ", ".join(sorted(COMMANDS)))
        return 0
    command = sys.argv[1]
    script = COMMANDS.get(command)
    if not script:
        print(f"unknown command: {command}", file=sys.stderr)
        return 2
    if not script.is_file():
        print(f"bundled command is missing: {script}", file=sys.stderr)
        return 2
    os.execv(sys.executable, [sys.executable, str(script), *sys.argv[2:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
