#!/usr/bin/env python3
"""Project-scoped HarmonyOS target allocation, leasing, and device operations."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import time
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.discovery import (  # noqa: E402
    connected_targets,
    resolve_emulator,
    resolve_hdc,
    run,
)
from harmony_common.evidence import (  # noqa: E402
    build_record,
    evidence_path,
    target_evidence,
    write_record,
)
from harmony_common.project import find_project_root, project_identity  # noqa: E402
from harmony_common.target_registry import (  # noqa: E402
    RegistryError,
    StateStore,
    acquire,
    allocate_port,
    bind,
    binding_drift,
    fingerprint,
    fingerprint_digest,
    get_binding,
    project_entry,
    registry_issues,
    release,
    require_active_lease,
    set_runtime_serial,
    target_key,
    unbind,
)


def is_true(value: object) -> bool:
    return value is True or str(value).lower() == "true"


def raw_emulator_inventory(emulator: str) -> list[dict[str, Any]]:
    if not emulator:
        return []
    result = run([emulator, "-list", "-details"], timeout=30)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, dict)]


def normalize_emulator(item: dict[str, Any]) -> dict[str, Any]:
    def joined(first: str, second: str) -> str:
        values = [str(item.get(first, "") or ""), str(item.get(second, "") or "")]
        return "x".join(value for value in values if value)

    return {
        "kind": "emulator",
        "name": str(item.get("name", "") or ""),
        "uuid": str(item.get("uuid", "") or ""),
        "serial": "",
        "device_type": str(item.get("deviceType", item.get("device_type", "")) or ""),
        "device_model": str(item.get("deviceModel", item.get("device_model", "")) or ""),
        "product_model": str(item.get("productModel", item.get("product_model", "")) or ""),
        "running": is_true(item.get("isRunning", item.get("running", False))),
        "hot_boot": is_true(item.get("isHotBoot", item.get("hot_boot", False))),
        "os_version": str(item.get("os.osVersion", item.get("os_version", "")) or ""),
        "api_version": str(item.get("os.apiVersion", item.get("api_version", "")) or ""),
        "cpu_arch": str(item.get("hw.cpu.arch", item.get("cpu_arch", "")) or ""),
        "cpu_cores": str(item.get("hw.cpu.ncore", item.get("cpu_cores", "")) or ""),
        "ram_mb": str(item.get("hw.ramSize", item.get("ram_mb", "")) or ""),
        "hdc_port": str(item.get("hw.hdc.port", item.get("hdc_port", "")) or ""),
        "single_screen": str(
            item.get("single_screen", "")
            or joined("hw.lcd.single.width", "hw.lcd.single.height")
        ),
        "double_screen": str(
            item.get("double_screen", "")
            or joined("hw.lcd.double.width", "hw.lcd.double.height")
        ),
        "runtime_screen": str(item.get("runtime_screen", "") or ""),
        "instance_path": str(item.get("instancePath", item.get("instance_path", "")) or ""),
        "image_root": str(item.get("imageRoot", item.get("image_root", "")) or ""),
        "image_subpath": str(item.get("imageSubPath", item.get("image_subpath", "")) or ""),
        "config_path": str(item.get("configPath", item.get("config_path", "")) or ""),
        "log_path": str(item.get("logPath", item.get("log_path", "")) or ""),
    }


def configuration_issues(items: list[dict[str, Any]], *, fixture: bool) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, list[str]]] = {
        "uuid": defaultdict(list),
        "instance_path": defaultdict(list),
    }
    for raw in items:
        item = normalize_emulator(raw)
        name = item["name"]
        uuid = item["uuid"]
        instance = item["instance_path"]
        if uuid:
            grouped["uuid"][uuid].append(name)
        else:
            issues.append(
                {"severity": "error", "code": "missing_uuid", "names": [name], "value": ""}
            )
        if instance:
            normalized = str(Path(instance).expanduser().resolve(strict=False))
            grouped["instance_path"][normalized].append(name)
            if not fixture:
                instance_path = Path(instance).expanduser()
                if not instance_path.is_dir():
                    issues.append(
                        {
                            "severity": "error",
                            "code": "missing_instance_path",
                            "names": [name],
                            "value": instance,
                        }
                    )
                elif instance_path.name != name:
                    issues.append(
                        {
                            "severity": "error",
                            "code": "instance_name_path_mismatch",
                            "names": [name],
                            "value": instance,
                        }
                    )
        else:
            issues.append(
                {
                    "severity": "error",
                    "code": "missing_instance_path",
                    "names": [name],
                    "value": "",
                }
            )
        if not item["image_root"] or not item["image_subpath"]:
            issues.append(
                {
                    "severity": "error",
                    "code": "missing_image_metadata",
                    "names": [name],
                    "value": "",
                }
            )
        elif not fixture:
            image = Path(item["image_root"]).expanduser() / item["image_subpath"]
            if not image.is_dir():
                issues.append(
                    {
                        "severity": "error",
                        "code": "missing_image_path",
                        "names": [name],
                        "value": str(image),
                    }
                )
    for field, values in grouped.items():
        for value, names in values.items():
            if value and len(names) > 1:
                issues.append(
                    {
                        "severity": "error",
                        "code": f"duplicate_{field}",
                        "names": sorted(names),
                        "value": value,
                    }
                )
    return issues


def used_hdc_ports() -> set[int]:
    if os.name != "posix":
        return set()
    result = run(["ps", "-ww", "-ax", "-o", "command="], timeout=10)
    if result.returncode != 0:
        return set()
    return {int(value) for value in re.findall(r"-hdcPort\s+(\d+)", result.stdout)}


def load_fixture(path: str) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"inventory fixture is unreadable: {source}: {error}") from error
    if isinstance(payload, list):
        payload = {"emulators": payload, "targets": []}
    if not isinstance(payload, dict):
        raise SystemExit("inventory fixture must be a JSON object or emulator array")
    return payload


def inventory(args: argparse.Namespace) -> dict[str, Any]:
    if args.inventory_file:
        payload = load_fixture(args.inventory_file)
        raw_items = [item for item in payload.get("emulators", []) if isinstance(item, dict)]
        targets = [item for item in payload.get("targets", []) if isinstance(item, dict)]
        return {
            "fixture": True,
            "emulator_cli": "",
            "hdc": "",
            "raw_emulators": raw_items,
            "emulators": [normalize_emulator(item) for item in raw_items],
            "targets": targets,
            "configuration_issues": payload.get(
                "configuration_issues",
                configuration_issues(raw_items, fixture=True),
            ),
        }
    hdc = resolve_hdc(args.hdc)
    emulator = resolve_emulator(args.emulator)
    raw_items = raw_emulator_inventory(emulator)
    targets = connected_targets(hdc) if hdc else []
    return {
        "fixture": False,
        "emulator_cli": emulator,
        "hdc": hdc,
        "raw_emulators": raw_items,
        "emulators": [normalize_emulator(item) for item in raw_items],
        "targets": targets,
        "configuration_issues": configuration_issues(raw_items, fixture=False),
    }


def project_context(args: argparse.Namespace) -> tuple[Path, str]:
    try:
        root = find_project_root(args.project)
        identity = project_identity(root, getattr(args, "project_id", ""))
    except ValueError as error:
        raise SystemExit(str(error)) from error
    return root, identity


def store_from(args: argparse.Namespace) -> StateStore:
    return StateStore(Path(args.state_file).expanduser() if args.state_file else None)


def issue_for_target(issues: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [
        issue
        for issue in issues
        if issue.get("severity") == "error" and name in issue.get("names", [])
    ]


def find_exact_emulator(items: list[dict[str, Any]], value: str) -> dict[str, Any]:
    by_uuid = [item for item in items if item.get("uuid") == value]
    if len(by_uuid) == 1:
        return by_uuid[0]
    by_name = [item for item in items if item.get("name") == value]
    if len(by_name) == 1:
        return by_name[0]
    if len(by_name) > 1 or len(by_uuid) > 1:
        raise RegistryError(f"emulator identity is ambiguous: {value}")
    raise RegistryError(f"emulator not found: {value}")


def connected_serials(items: list[dict[str, Any]]) -> set[str]:
    return {
        str(item.get("serial", ""))
        for item in items
        if str(item.get("status", "")).lower() == "connected"
    }


def matching_serial(binding: dict[str, Any], targets: list[dict[str, Any]]) -> str:
    available = connected_serials(targets)
    if binding.get("kind") == "physical":
        serial = str(binding.get("serial", ""))
        return serial if serial in available else ""
    runtime = str(binding.get("runtimeSerial", ""))
    if runtime in available:
        return runtime
    port = int(binding.get("hdcPort", 0) or 0)
    candidates = [
        serial
        for serial in available
        if serial == str(port) or serial.endswith(f":{port}")
    ]
    return candidates[0] if len(candidates) == 1 else ""


def probe_api_version(hdc: str, serial: str) -> str:
    result = run(
        [hdc, "-t", serial, "shell", "param", "get", "const.ohos.apiversion"],
        timeout=15,
    )
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip().splitlines()[0].strip() if result.stdout.strip() else ""


def resolve_runtime_serial(
    binding: dict[str, Any],
    target: dict[str, Any],
    inv: dict[str, Any],
) -> str:
    if binding.get("kind") == "physical":
        return matching_serial(binding, inv["targets"])
    if inv["fixture"]:
        return matching_serial(binding, inv["targets"])
    hdc = inv.get("hdc", "")
    if not hdc:
        return ""
    available = connected_serials(inv["targets"])
    if not available:
        return ""
    expected_api = str(target.get("api_version", ""))
    expected_screens = accepted_screens({"fingerprint": fingerprint(target)})
    preferred = str(binding.get("runtimeSerial", ""))
    ordered = ([preferred] if preferred in available else []) + sorted(available - {preferred})
    matches: list[str] = []
    for serial in ordered:
        api = probe_api_version(hdc, serial)
        screen = probe_screen(hdc, serial)
        if expected_api and api != expected_api:
            continue
        if expected_screens and screen not in expected_screens:
            continue
        matches.append(serial)
    if len(matches) > 1:
        raise RegistryError(
            "multiple connected targets match the bound emulator API and display; "
            "stop unrelated instances or bind after assigning unique ports"
        )
    return matches[0] if matches else ""


def current_target(binding: dict[str, Any], inv: dict[str, Any]) -> dict[str, Any]:
    if binding.get("kind") == "emulator":
        matches = [
            item
            for item in inv["emulators"]
            if item.get("uuid") == binding.get("uuid")
        ]
        if len(matches) != 1:
            raise RegistryError(
                f"bound emulator UUID is missing or ambiguous: {binding.get('uuid')}"
            )
        return matches[0]
    return {
        **binding.get("fingerprint", {}),
        "kind": "physical",
        "serial": binding.get("serial", ""),
        "runtime_screen": "",
    }


def screen_tuple(value: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", value or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def accepted_screens(binding: dict[str, Any]) -> set[tuple[int, int]]:
    expected: set[tuple[int, int]] = set()
    source = binding.get("fingerprint", {})
    for field in ("single_screen", "double_screen"):
        size = screen_tuple(str(source.get(field, "")))
        if size:
            expected.add(size)
            expected.add((size[1], size[0]))
    return expected


def image_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if not data.startswith(b"\xff\xd8"):
        return None
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            break
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        } and offset + 7 < len(data):
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            return width, height
        offset += max(length, 2)
    return None


def probe_screen(hdc: str, serial: str) -> tuple[int, int] | None:
    remote = f"/data/local/tmp/harmonyos-workbench-{os.getpid()}.jpeg"
    with tempfile.TemporaryDirectory(prefix="harmonyos-target-screen-") as directory:
        local = Path(directory) / "screen.jpeg"
        capture = run(
            [hdc, "-t", serial, "shell", "snapshot_display", "-f", remote],
            timeout=30,
        )
        if capture.returncode != 0:
            return None
        receive = run([hdc, "-t", serial, "file", "recv", remote, str(local)], timeout=30)
        run([hdc, "-t", serial, "shell", "rm", "-f", remote], timeout=10)
        if receive.returncode != 0 or not local.is_file():
            return None
        return image_size(local)


def geometry_check(
    binding: dict[str, Any],
    target: dict[str, Any],
    *,
    hdc: str,
    serial: str,
    fixture: bool,
) -> dict[str, Any]:
    expected = accepted_screens(binding)
    observed: tuple[int, int] | None = None
    source = ""
    if fixture and target.get("runtime_screen"):
        observed = screen_tuple(str(target.get("runtime_screen", "")))
        source = "fixture"
    elif hdc and serial:
        observed = probe_screen(hdc, serial)
        source = "snapshot"
    if not expected:
        return {
            "status": "blocked",
            "reason": "binding_has_no_accepted_display_geometry",
            "expected": [],
            "observed": observed,
        }
    if not observed:
        return {
            "status": "blocked",
            "reason": "runtime_display_geometry_unavailable",
            "expected": sorted(expected),
            "observed": None,
            "source": source,
        }
    return {
        "status": "passed" if observed in expected else "blocked",
        "reason": "" if observed in expected else "runtime_display_geometry_mismatch",
        "expected": sorted(expected),
        "observed": observed,
        "source": source,
    }


def build_start_command(
    emulator: str,
    target: dict[str, Any],
    port: int,
    bootmode: str,
) -> list[str]:
    command = [emulator, "-start", str(target["name"])]
    instance = Path(str(target.get("instance_path", ""))).expanduser()
    if instance.name == target.get("name"):
        command.extend(["-path", str(instance.parent)])
    if target.get("image_root"):
        command.extend(["-imageRoot", str(target["image_root"])])
    command.extend(["-hdcPort", str(port)])
    if bootmode:
        command.extend(["-bootmode", bootmode])
    return command


def spec_key(target: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(target.get(field, "")).lower()
        for field in (
            "device_type",
            "device_model",
            "product_model",
            "api_version",
            "cpu_arch",
            "single_screen",
            "double_screen",
        )
    )


def filter_candidates(
    items: list[dict[str, Any]],
    args: argparse.Namespace,
    issues: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    bound = {
        binding.get("targetKey")
        for project in state.get("projects", {}).values()
        for binding in project.get("bindings", {}).values()
    }
    candidates: list[dict[str, Any]] = []
    for item in items:
        if target_key(item) in bound:
            continue
        if issue_for_target(issues, str(item.get("name", ""))):
            continue
        if not target_meets_requirements(item, args):
            continue
        candidates.append(item)
    return sorted(candidates, key=lambda item: (str(item.get("name", "")), str(item.get("uuid", ""))))


def target_meets_requirements(
    item: dict[str, Any],
    args: argparse.Namespace,
) -> bool:
    if args.device_type and str(item.get("device_type", "")).lower() != args.device_type.lower():
        return False
    if args.api_version and str(item.get("api_version", "")) != args.api_version:
        return False
    if args.screen and args.screen not in {
        str(item.get("single_screen", "")),
        str(item.get("double_screen", "")),
    }:
        return False
    if args.name_pattern and not re.search(args.name_pattern, str(item.get("name", ""))):
        return False
    return True


def preflight_data(
    args: argparse.Namespace,
    *,
    require_geometry: bool,
) -> tuple[Path, str, dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    root, project_id = project_context(args)
    inv = inventory(args)
    store = store_from(args)
    with store.transaction(write=False) as state:
        binding = dict(
            get_binding(
                state,
                project_id=project_id,
                project_root=str(root),
                role=args.role,
            )
        )
        lease = dict(require_active_lease(state, project_id=project_id, binding=binding))
    target = current_target(binding, inv)
    drift = binding_drift(binding, target)
    if drift:
        raise RegistryError(f"target fingerprint drift: {json.dumps(drift, ensure_ascii=False)}")
    if binding.get("kind") == "emulator":
        errors = issue_for_target(inv["configuration_issues"], str(target.get("name", "")))
        if errors:
            raise RegistryError(f"unsafe emulator configuration: {json.dumps(errors, ensure_ascii=False)}")
        if not target.get("running"):
            raise RegistryError("bound emulator is not running")
    serial = resolve_runtime_serial(binding, target, inv)
    if not serial:
        raise RegistryError("the exact bound HDC target is not connected")
    geometry = {"status": "skipped"}
    if require_geometry:
        geometry = geometry_check(
            binding,
            target,
            hdc=inv["hdc"],
            serial=serial,
            fixture=inv["fixture"],
        )
        if geometry["status"] != "passed":
            raise RegistryError(f"geometry preflight blocked: {json.dumps(geometry, ensure_ascii=False)}")
    return root, project_id, inv, binding, lease, serial, geometry


def deploy(
    args: argparse.Namespace,
    root: Path,
    project_id: str,
    inv: dict[str, Any],
    binding: dict[str, Any],
    lease: dict[str, Any],
    serial: str,
    geometry: dict[str, Any],
) -> int:
    if not inv["hdc"]:
        raise RegistryError("HDC is unavailable; deploy cannot run from an inventory fixture")
    artifact = Path(args.artifact).expanduser().resolve()
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise RegistryError(f"deployable HAP not found: {artifact}")
    installed = run([inv["hdc"], "-t", serial, "install", str(artifact)], timeout=180)
    checks: list[dict[str, Any]] = [
        {"name": "target_preflight", "status": "passed"},
        {"name": "geometry", **geometry},
        {"name": "install", "status": "passed" if installed.returncode == 0 else "failed"},
    ]
    if installed.returncode != 0:
        payload = {
            "status": "failed",
            "target": serial,
            "error": (installed.stderr or installed.stdout).strip()[-1000:],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return installed.returncode or 1
    launched = run(
        [
            inv["hdc"],
            "-t",
            serial,
            "shell",
            "aa",
            "start",
            "-a",
            args.ability,
            "-b",
            args.bundle,
        ],
        timeout=60,
    )
    checks.append(
        {"name": "launch", "status": "passed" if launched.returncode == 0 else "failed"}
    )
    snapshot = ""
    if launched.returncode == 0 and args.snapshot_dir:
        time.sleep(max(0.0, min(args.settle_seconds, 30.0)))
        output = Path(args.snapshot_dir).expanduser()
        if not output.is_absolute():
            output = root / output
        output.mkdir(parents=True, exist_ok=True)
        remote = f"/data/local/tmp/harmonyos-workbench-{os.getpid()}.jpeg"
        local = output / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', serial)}.jpeg"
        captured = run(
            [inv["hdc"], "-t", serial, "shell", "snapshot_display", "-f", remote],
            timeout=30,
        )
        received = (
            run([inv["hdc"], "-t", serial, "file", "recv", remote, str(local)], timeout=30)
            if captured.returncode == 0
            else captured
        )
        run([inv["hdc"], "-t", serial, "shell", "rm", "-f", remote], timeout=10)
        if captured.returncode == 0 and received.returncode == 0 and local.is_file():
            local.chmod(0o600)
            snapshot = str(local.resolve())
            observed = image_size(local)
            if observed not in accepted_screens(binding):
                checks.append(
                    {
                        "name": "post_launch_geometry",
                        "status": "failed",
                        "observed": observed,
                    }
                )
        else:
            checks.append({"name": "snapshot", "status": "failed"})
    passed = launched.returncode == 0 and all(
        check.get("status") != "failed" for check in checks
    )
    payload = {
        "status": "passed" if passed else "failed",
        "project": str(root),
        "projectId": project_id,
        "role": args.role,
        "target": serial,
        "targetKey": binding["targetKey"],
        "fingerprintDigest": binding["fingerprintDigest"],
        "leaseExpiresAt": lease["expiresAt"],
        "artifact": str(artifact),
        "snapshot": snapshot,
        "checks": checks,
    }
    if args.evidence:
        evidence_path = Path(args.evidence).expanduser()
        if not evidence_path.is_absolute():
            evidence_path = root / evidence_path
        record = build_record(
            phase="targets",
            project_id=project_id,
            status=payload["status"],
            inputs={
                "artifact": evidence_path(artifact, root),
                "bundle": args.bundle,
                "ability": args.ability,
            },
            outputs={"snapshot": evidence_path(snapshot, root)},
            checks=checks,
            target=target_evidence(
                project_id=project_id,
                role=args.role,
                target_key=binding["targetKey"],
                runtime_serial=serial,
                fingerprint_digest=binding["fingerprintDigest"],
                lease_expires_at=lease["expiresAt"],
            ),
            next_phase="test",
        )
        payload["evidence"] = str(write_record(evidence_path, record))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def add_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=".")
    parser.add_argument("--project-id", default="")
    parser.add_argument("--role", default="primary")


def write_target_bridge(
    output: Path,
    *,
    project_id: str,
    role: str,
    binding: dict[str, Any],
    lease: dict[str, Any],
    serial: str,
) -> Path:
    """Write a local-only routing file for project-owned test harnesses.

    The raw runtime serial is deliberately kept out of durable evidence.  A
    bridge is short-lived local runtime state, not a file to commit or archive.
    """
    output = output.expanduser().resolve()
    parent_existed = output.parent.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        output.parent.chmod(0o700)
    payload = {
        "schema": "harmonyos.workbench.target-bridge/v1",
        "projectId": project_id,
        "role": role,
        "runtimeSerial": serial,
        "hdcPort": binding.get("hdcPort") or "",
        "fingerprintDigest": binding.get("fingerprintDigest", ""),
        "leaseExpiresAt": lease.get("expiresAt", ""),
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(output)
    output.chmod(0o600)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hdc", default="")
    parser.add_argument("--emulator", default="")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--inventory-file", default="")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("inventory")
    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--project", default="")
    doctor_parser.add_argument("--project-id", default="")
    doctor_parser.add_argument("--role", default="primary")
    doctor_parser.add_argument("--emulator-id", default="")

    status_parser = subparsers.add_parser("status")
    add_project_args(status_parser)

    bind_parser = subparsers.add_parser("bind")
    add_project_args(bind_parser)
    target_group = bind_parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--emulator-id")
    target_group.add_argument("--target-serial")
    bind_parser.add_argument("--hdc-port", default="auto")
    bind_parser.add_argument("--accept-drift", action="store_true")

    allocate_parser = subparsers.add_parser("allocate")
    add_project_args(allocate_parser)
    allocate_parser.add_argument("--device-type", default="")
    allocate_parser.add_argument("--api-version", default="")
    allocate_parser.add_argument("--screen", default="")
    allocate_parser.add_argument("--name-pattern", default="")
    allocate_parser.add_argument("--hdc-port", default="auto")

    acquire_parser = subparsers.add_parser("acquire")
    add_project_args(acquire_parser)
    acquire_parser.add_argument("--ttl-seconds", type=int, default=14400)

    release_parser = subparsers.add_parser("release")
    add_project_args(release_parser)

    unbind_parser = subparsers.add_parser("unbind")
    add_project_args(unbind_parser)

    start_parser = subparsers.add_parser("start")
    add_project_args(start_parser)
    start_parser.add_argument("--bootmode", choices=("snapshot", "coldboot", "reset"), default="")
    start_parser.add_argument("--wait-seconds", type=int, default=180)
    start_parser.add_argument("--dry-run", action="store_true")

    stop_parser = subparsers.add_parser("stop")
    add_project_args(stop_parser)
    stop_parser.add_argument("--wait-seconds", type=int, default=30)
    stop_parser.add_argument("--dry-run", action="store_true")

    preflight_parser = subparsers.add_parser("preflight")
    add_project_args(preflight_parser)
    preflight_parser.add_argument("--skip-geometry", action="store_true")
    preflight_parser.add_argument("--evidence", default="")

    bridge_parser = subparsers.add_parser("bridge")
    add_project_args(bridge_parser)
    bridge_parser.add_argument("--out", required=True)

    deploy_parser = subparsers.add_parser("deploy")
    add_project_args(deploy_parser)
    deploy_parser.add_argument("--artifact", required=True)
    deploy_parser.add_argument("--bundle", required=True)
    deploy_parser.add_argument("--ability", default="EntryAbility")
    deploy_parser.add_argument("--settle-seconds", type=float, default=2.0)
    deploy_parser.add_argument("--snapshot-dir", default="")
    deploy_parser.add_argument("--evidence", default="")
    deploy_parser.add_argument("--skip-geometry", action="store_true")

    args = parser.parse_args()
    store = store_from(args)

    try:
        if args.action == "inventory":
            inv = inventory(args)
            with store.transaction(write=False) as state:
                payload = {
                    "status": "passed",
                    "stateFile": str(store.path),
                    "targets": inv["targets"],
                    "emulators": inv["emulators"],
                    "configurationIssues": inv["configuration_issues"],
                    "registryIssues": registry_issues(state),
                    "boundProjects": len(state.get("projects", {})),
                    "activeLeases": len(
                        [
                            lease
                            for lease in state.get("leases", {}).values()
                            if lease
                        ]
                    ),
                }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.action == "doctor":
            inv = inventory(args)
            with store.transaction(write=False) as state:
                selected_emulators = inv["emulators"]
                configuration = inv["configuration_issues"]
                scope: dict[str, Any] = {"mode": "global"}
                if args.project:
                    root, project_id = project_context(args)
                    binding = get_binding(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                    )
                    target = current_target(binding, inv)
                    selected_emulators = [target] if binding.get("kind") == "emulator" else []
                    configuration = (
                        issue_for_target(
                            configuration,
                            str(target.get("name", "")),
                        )
                        if selected_emulators
                        else []
                    )
                    scope = {
                        "mode": "project",
                        "projectId": project_id,
                        "role": args.role,
                        "targetKey": binding.get("targetKey", ""),
                    }
                elif args.emulator_id:
                    target = find_exact_emulator(inv["emulators"], args.emulator_id)
                    selected_emulators = [target]
                    configuration = issue_for_target(
                        configuration,
                        str(target.get("name", "")),
                    )
                    scope = {
                        "mode": "emulator",
                        "targetKey": target_key(target),
                    }
                issues = [*configuration, *registry_issues(state)]
            blocked = any(issue.get("severity") == "error" for issue in issues)
            print(
                json.dumps(
                    {
                        "status": "blocked" if blocked else "passed",
                        "stateFile": str(store.path),
                        "scope": scope,
                        "issues": issues,
                        "emulators": selected_emulators,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2 if blocked else 0

        if args.action == "status":
            root, project_id = project_context(args)
            inv = inventory(args)
            with store.transaction(write=False) as state:
                binding = dict(
                    get_binding(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                    )
                )
                lease = dict(state.get("leases", {}).get(binding["targetKey"], {}))
                lease.pop("token", None)
            target = current_target(binding, inv)
            runtime_serial = resolve_runtime_serial(binding, target, inv)
            payload = {
                "status": "passed",
                "project": str(root),
                "projectId": project_id,
                "role": args.role,
                "binding": binding,
                "lease": lease,
                "drift": binding_drift(binding, target),
                "runtimeSerial": runtime_serial,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.action in {"bind", "allocate"}:
            root, project_id = project_context(args)
            inv = inventory(args)
            with store.transaction(write=True) as state:
                existing = (
                    state.get("projects", {})
                    .get(project_id, {})
                    .get("bindings", {})
                    .get(args.role)
                )
                selection_mode = args.action
                if args.action == "bind":
                    if args.emulator_id:
                        target = find_exact_emulator(inv["emulators"], args.emulator_id)
                        problems = issue_for_target(
                            inv["configuration_issues"], str(target.get("name", ""))
                        )
                        if problems:
                            raise RegistryError(
                                f"unsafe emulator configuration: {json.dumps(problems, ensure_ascii=False)}"
                            )
                    else:
                        serial = str(args.target_serial)
                        if serial not in connected_serials(inv["targets"]):
                            raise RegistryError(f"physical target is not connected: {serial}")
                        screen = (
                            probe_screen(inv["hdc"], serial)
                            if inv["hdc"] and not inv["fixture"]
                            else None
                        )
                        target = {
                            "kind": "physical",
                            "serial": serial,
                            "uuid": "",
                            "name": serial,
                            "single_screen": f"{screen[0]}x{screen[1]}" if screen else "",
                        }
                else:
                    if existing:
                        target = current_target(existing, inv)
                        if not target_meets_requirements(target, args):
                            raise RegistryError(
                                "the fixed target does not match new requirements; "
                                "release and unbind it explicitly before reallocating"
                            )
                        candidates = [target]
                        selection_mode = "existing_binding"
                    else:
                        candidates = filter_candidates(
                            inv["emulators"],
                            args,
                            inv["configuration_issues"],
                            state,
                        )
                        if not candidates:
                            raise RegistryError("no free emulator matches the requested specification")
                        groups = {spec_key(item) for item in candidates}
                        if len(groups) > 1:
                            raise RegistryError(
                                "matching emulators have different specifications; narrow device type, API, screen, or name"
                            )
                        target = candidates[0]
                port: int | None = None
                if target.get("kind") == "emulator":
                    live_ports = set() if inv["fixture"] else used_hdc_ports()
                    same_target = bool(
                        existing
                        and existing.get("targetKey") == target_key(target)
                    )
                    if same_target and args.hdc_port == "auto":
                        port = int(existing.get("hdcPort", 0) or 0)
                    elif args.hdc_port == "auto":
                        preferred_value = str(target.get("hdc_port", ""))
                        preferred = (
                            int(preferred_value)
                            if preferred_value.isdigit()
                            and int(preferred_value) not in live_ports
                            else None
                        )
                        try:
                            port = allocate_port(
                                state,
                                externally_used=live_ports,
                                preferred=preferred,
                            )
                        except RegistryError:
                            port = allocate_port(
                                state,
                                externally_used=live_ports,
                            )
                    else:
                        port = allocate_port(
                            state,
                            externally_used=live_ports,
                            preferred=int(args.hdc_port),
                        )
                binding = bind(
                    state,
                    project_id=project_id,
                    project_root=str(root),
                    role=args.role,
                    target=target,
                    hdc_port=port,
                    accept_drift=getattr(args, "accept_drift", False),
                )
                runtime_serial = ""
                if target.get("kind") == "emulator" and target.get("running"):
                    runtime_serial = resolve_runtime_serial(binding, target, inv)
                    if not runtime_serial:
                        raise RegistryError(
                            "running emulator could not be correlated to one exact HDC target"
                        )
                    binding = set_runtime_serial(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                        serial=runtime_serial,
                    )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "project": str(root),
                        "projectId": project_id,
                        "role": args.role,
                        "binding": binding,
                        "selection": {
                            "mode": selection_mode,
                            "candidateCount": len(candidates)
                            if args.action == "allocate"
                            else 1,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.action in {"acquire", "release", "unbind"}:
            root, project_id = project_context(args)
            with store.transaction(write=True) as state:
                binding = get_binding(
                    state,
                    project_id=project_id,
                    project_root=str(root),
                    role=args.role,
                )
                if args.action == "acquire":
                    result = acquire(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                        ttl_seconds=args.ttl_seconds,
                    )
                elif args.action == "release":
                    result = release(state, project_id=project_id, binding=binding)
                else:
                    result = unbind(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                    )
            visible_result = dict(result)
            visible_result.pop("token", None)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "projectId": project_id,
                        "role": args.role,
                        "result": visible_result,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.action == "preflight":
            root, project_id, _, binding, lease, serial, geometry = preflight_data(
                args,
                require_geometry=not args.skip_geometry,
            )
            payload = {
                "status": "passed",
                "project": str(root),
                "projectId": project_id,
                "role": args.role,
                "targetKey": binding["targetKey"],
                "runtimeSerial": serial,
                "fingerprintDigest": binding["fingerprintDigest"],
                "leaseExpiresAt": lease["expiresAt"],
                "geometry": geometry,
            }
            if args.evidence:
                evidence_path = Path(args.evidence).expanduser()
                if not evidence_path.is_absolute():
                    evidence_path = root / evidence_path
                record = build_record(
                    phase="targets",
                    project_id=project_id,
                    status="passed",
                    inputs={"role": args.role, "operation": "preflight"},
                    outputs={"geometry": geometry},
                    checks=[
                        {"name": "lease", "status": "passed"},
                        {"name": "fingerprint", "status": "passed"},
                        {"name": "geometry", **geometry},
                    ],
                    target=target_evidence(
                        project_id=project_id,
                        role=args.role,
                        target_key=binding["targetKey"],
                        runtime_serial=serial,
                        fingerprint_digest=binding["fingerprintDigest"],
                        lease_expires_at=lease["expiresAt"],
                    ),
                    next_phase="test",
                )
                payload["evidence"] = str(write_record(evidence_path, record))
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.action == "bridge":
            root, project_id, _, binding, lease, serial, _ = preflight_data(
                args,
                require_geometry=True,
            )
            bridge = write_target_bridge(
                Path(args.out),
                project_id=project_id,
                role=args.role,
                binding=binding,
                lease=lease,
                serial=serial,
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "projectId": project_id,
                        "role": args.role,
                        "bridge": str(bridge),
                        "fingerprintDigest": binding["fingerprintDigest"],
                        "leaseExpiresAt": lease["expiresAt"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.action == "deploy":
            values = preflight_data(args, require_geometry=not args.skip_geometry)
            return deploy(args, *values)

        root, project_id = project_context(args)
        inv = inventory(args)
        if inv["fixture"] and not args.dry_run:
            raise RegistryError("start/stop cannot execute against an inventory fixture")
        if not inv["emulator_cli"]:
            raise RegistryError("DevEco Emulator CLI was not found")
        with store.transaction(write=False) as state:
            binding = dict(
                get_binding(
                    state,
                    project_id=project_id,
                    project_root=str(root),
                    role=args.role,
                )
            )
            require_active_lease(state, project_id=project_id, binding=binding)
        if binding.get("kind") != "emulator":
            raise RegistryError("start/stop applies only to emulator bindings")
        target = current_target(binding, inv)
        drift = binding_drift(binding, target)
        if drift:
            raise RegistryError(f"target fingerprint drift: {json.dumps(drift, ensure_ascii=False)}")
        problems = issue_for_target(inv["configuration_issues"], str(target.get("name", "")))
        if problems:
            raise RegistryError(
                f"unsafe emulator configuration: {json.dumps(problems, ensure_ascii=False)}"
            )

        if args.action == "start":
            if target.get("running"):
                serial = resolve_runtime_serial(binding, target, inv)
                if not serial:
                    raise RegistryError("emulator reports running but its bound HDC serial is absent")
                with store.transaction(write=True) as state:
                    set_runtime_serial(
                        state,
                        project_id=project_id,
                        project_root=str(root),
                        role=args.role,
                        serial=serial,
                    )
                print(
                    json.dumps(
                        {"status": "already_running", "target": serial, "binding": binding},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            port = int(binding.get("hdcPort", 0) or 0)
            if port in used_hdc_ports():
                raise RegistryError(f"bound HDC port is used by another Emulator process: {port}")
            if args.bootmode in {"coldboot", "reset"} and not args.dry_run:
                raise RegistryError(
                    f"{args.bootmode} changes emulator state; use dry-run and obtain explicit authorization"
                )
            if args.bootmode == "snapshot" and not target.get("hot_boot"):
                raise RegistryError("snapshot boot requested for an instance without hot boot")
            command = build_start_command(
                inv["emulator_cli"], target, port, args.bootmode
            )
            if args.dry_run:
                print(
                    json.dumps(
                        {
                            "status": "planned",
                            "projectId": project_id,
                            "role": args.role,
                            "targetKey": binding["targetKey"],
                            "command": command,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            before = connected_serials(inv["targets"])
            log_path = Path(tempfile.gettempdir()) / (
                f"harmonyos-workbench-{re.sub(r'[^A-Za-z0-9_.-]', '_', str(target['name']))}.log"
            )
            with log_path.open("ab") as stream:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                )
            deadline = time.monotonic() + max(5, min(args.wait_seconds, 600))
            latest_serial = ""
            while time.monotonic() < deadline:
                current_inv = inventory(args)
                current = current_target(binding, current_inv)
                latest_serial = resolve_runtime_serial(binding, current, current_inv)
                if current.get("running") and latest_serial:
                    with store.transaction(write=True) as state:
                        set_runtime_serial(
                            state,
                            project_id=project_id,
                            project_root=str(root),
                            role=args.role,
                            serial=latest_serial,
                        )
                    print(
                        json.dumps(
                            {
                                "status": "passed",
                                "projectId": project_id,
                                "role": args.role,
                                "target": latest_serial,
                                "newTargets": sorted(
                                    connected_serials(current_inv["targets"]) - before
                                ),
                                "launchPid": process.pid,
                                "launchLog": str(log_path),
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 0
                if process.poll() not in (None, 0) and not current.get("running"):
                    break
                time.sleep(2)
            print(
                json.dumps(
                    {
                        "status": "partial",
                        "projectId": project_id,
                        "role": args.role,
                        "target": latest_serial,
                        "launchPid": process.pid,
                        "launchLog": str(log_path),
                        "note": "The detached Emulator process was left running for diagnosis.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2

        command = [inv["emulator_cli"], "-stop", str(target["name"])]
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "status": "planned",
                        "projectId": project_id,
                        "role": args.role,
                        "command": command,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        stopped = run(command, timeout=30)
        if stopped.returncode != 0:
            raise RegistryError((stopped.stderr or stopped.stdout).strip()[-1000:])
        deadline = time.monotonic() + max(5, min(args.wait_seconds, 120))
        while time.monotonic() < deadline:
            current_inv = inventory(args)
            if not current_target(binding, current_inv).get("running"):
                print(
                    json.dumps(
                        {"status": "passed", "projectId": project_id, "role": args.role},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            time.sleep(2)
        print(
            json.dumps(
                {"status": "partial", "reason": "emulator_still_running"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    except RegistryError as error:
        print(
            json.dumps(
                {"status": "blocked", "reason": str(error)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
