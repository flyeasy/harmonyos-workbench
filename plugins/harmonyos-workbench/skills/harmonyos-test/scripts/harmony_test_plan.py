#!/usr/bin/env python3
"""Describe locally available HarmonyOS test layers and DevEco service blockers."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.discovery import connected_targets, resolve_hdc  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402
from harmony_common.target_registry import (  # noqa: E402
    RegistryError,
    StateStore,
    get_binding,
    require_active_lease,
)


SERVICES = [
    ("local_precheck", False, False, "HarmonyOS 5.0+ physical device and matching package"),
    ("performance_base", False, True, "stable physical device"),
    ("scenario_performance", False, False, "physical device and Hypium scenario"),
    ("performance_monitoring", False, True, "physical device"),
    ("stability_base", True, True, "simulator or HarmonyOS 5.0+ device"),
    ("memory_leak", False, True, "HarmonyOS 7.0+ physical device and debug-certificate package"),
    ("multi_device_layout", True, True, "configured simulator/device form factors"),
    ("ux_base", True, True, "simulator or physical device"),
    ("security_base", False, True, "physical device for applications"),
    ("power_base", False, True, "physical device"),
    ("functional_experience", True, True, "simulator or physical device"),
    ("exploration", True, True, "simulator or physical device; long run recommended"),
    ("regression", True, True, "Hypium executable test package"),
]


def count(root: Path, pattern: str) -> int:
    return sum(1 for path in root.rglob(pattern) if path.is_file() and "build" not in path.parts)


def contains_arkweb(root: Path) -> bool:
    for path in root.rglob("*.ets"):
        if "build" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Web(" in text or "WebviewController" in text or "webview.WebviewController" in text:
            return True
    return False


def command_version(command: str) -> str:
    executable = shutil.which(command)
    if not executable:
        return ""
    result = subprocess.run([executable, "--version"], text=True, capture_output=True, check=False)
    return (result.stdout or result.stderr).strip().splitlines()[0] if result.returncode == 0 else ""


def python_module(executable: str, module: str) -> bool:
    if not executable:
        return False
    result = subprocess.run(
        [executable, "-c", f"import importlib.util; raise SystemExit(0 if importlib.util.find_spec('{module}') else 1)"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def target_status() -> list[dict[str, str]]:
    hdc = resolve_hdc()
    return connected_targets(hdc) if hdc else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--target", choices=("host", "emulator", "physical", "cloud"), default="emulator")
    parser.add_argument("--app-kind", choices=("app", "atomic-service"), default="app")
    parser.add_argument("--project-id", default="")
    parser.add_argument("--role", default="primary")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        root = find_project_root(args.project)
        identity = project_identity(root, args.project_id)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    python310 = shutil.which("python3.10") or ""
    current_python = sys.executable
    is_atomic = args.app_kind == "atomic-service"
    blockers: list[str] = []
    target_binding: dict[str, object] = {}
    if args.target in {"emulator", "physical"}:
        store = StateStore(Path(args.state_file).expanduser() if args.state_file else None)
        try:
            with store.transaction(write=False) as state:
                binding = get_binding(
                    state,
                    project_id=identity,
                    project_root=str(root),
                    role=args.role,
                )
                lease = require_active_lease(
                    state,
                    project_id=identity,
                    binding=binding,
                )
                target_binding = {
                    "projectId": identity,
                    "role": args.role,
                    "targetKey": binding.get("targetKey", ""),
                    "runtimeSerial": binding.get("runtimeSerial", ""),
                    "fingerprintDigest": binding.get("fingerprintDigest", ""),
                    "leaseExpiresAt": lease.get("expiresAt", ""),
                }
        except RegistryError as error:
            blockers.append(str(error))
    service_plan = []
    for name, simulator, atomic, condition in SERVICES:
        supported = True
        reasons: list[str] = []
        if args.target == "emulator" and not simulator:
            supported = False
            reasons.append("service does not support simulator")
        if is_atomic and not atomic:
            supported = False
            reasons.append("service does not support atomic service")
        if args.target == "host":
            supported = False
            reasons.append("service requires emulator, physical device, or cloud")
        service_plan.append({
            "service": name,
            "available_for_target": supported,
            "condition": condition,
            "blockers": reasons,
        })

    payload = {
        "status": "blocked" if blockers else "passed",
        "project": str(root),
        "projectId": identity,
        "target": args.target,
        "app_kind": args.app_kind,
        "targetBinding": target_binding,
        "blockers": blockers,
        "detected": {
            "local_test_files": count(root, "*.test.ets"),
            "ohos_test_files": sum(1 for path in root.rglob("*.ets") if "ohosTest" in path.parts),
            "project_smoke_scripts": len(list((root / "scripts").glob("*smoke*"))) if (root / "scripts").exists() else 0,
            "arkweb": contains_arkweb(root),
            "python": command_version(Path(current_python).name),
            "python310": command_version("python3.10"),
            "hypium_in_python310": python_module(python310, "hypium"),
            "hypium_in_current_python": importlib.util.find_spec("hypium") is not None,
            "xdevice_in_python310": python_module(python310, "xdevice"),
            "deveco_testing_installed": Path("/Applications/DevEco_Testing_for_App.app").exists(),
            "hdc_targets": target_status(),
        },
        "recommended_order": [
            "project static/smoke gates",
            "Local Test",
            "Instrument Test on selected target",
            "Hypium deterministic UI regression",
            "DevEco Testing specialty service",
            "backend/relay end-to-end validation where applicable",
        ],
        "services": service_plan,
        "matrix_version": "DevEco Testing 26.0; last verified 2026-07-20",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
