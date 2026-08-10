#!/usr/bin/env python3
"""Inventory HarmonyOS permission and capability hints without claiming entitlement."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.evidence import build_record, evidence_path, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402


TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".ets",
    ".h",
    ".hpp",
    ".json",
    ".json5",
    ".ts",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".git",
    ".hvigor",
    ".idea",
    "build",
    "node_modules",
    "oh_modules",
    "test-results",
}
PERMISSION_PATTERN = re.compile(r"ohos\.permission\.[A-Z0-9_]+")
CAPABILITY_HINTS: dict[str, tuple[str, ...]] = {
    "agent-framework": (
        "AgentExtensionAbility",
        "AgentAbilityExtension",
        "AgentFramework",
        "agentFramework",
    ),
    "intents": ("InsightIntent", "insightIntent", "IntentsKit"),
    "ai-networking": ("aiNetworking/v1/", "AI Networking", "ainetworking"),
    "core-speech": ("CoreSpeechKit", "textToSpeech", "speechRecognizer"),
    "core-vision": ("CoreVisionKit", "VisionKit", "textRecognition"),
    "mindspore-lite": ("mindspore", "MindSpore", "mindspore_lite"),
    "neural-network-runtime": ("NeuralNetworkRuntime", "neuralNetworkRuntime"),
    "cann": ("CANN", "AscendC", "aclmdl"),
    "account": ("AccountKit", "hwAccount", "UnionID", "OpenID"),
    "app-linking": ("AppLinking", "appLinking", "agconnect.applinking"),
    "health": ("HealthService", "healthService", "HealthKit"),
    "iap": ("IAPKit", "iap.", "createPurchase", "purchaseToken"),
    "live-view": ("LiveView", "liveView", "liveview"),
    "location": ("LocationKit", "geoLocationManager", "geofence"),
    "map": ("MapKit", "MapComponent", "mapCommon"),
    "push": ("PushKit", "pushService", "pushToken"),
    "wear-engine": ("WearEngine", "wearEngine"),
}


def source_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        result.append(path)
    return sorted(result)


def scan(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], int]:
    permissions: dict[str, set[str]] = defaultdict(set)
    capabilities: dict[str, set[str]] = defaultdict(set)
    scanned = 0
    for path in source_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        relative = path.relative_to(root).as_posix()
        for permission in PERMISSION_PATTERN.findall(text):
            permissions[permission].add(relative)
        lowered = text.lower()
        for capability, patterns in CAPABILITY_HINTS.items():
            if any(pattern.lower() in lowered for pattern in patterns):
                capabilities[capability].add(relative)
    return permissions, capabilities, scanned


def bounded_locations(values: set[str]) -> list[str]:
    ordered = sorted(values)
    return ordered[:20] + ([f"... {len(ordered) - 20} more"] if len(ordered) > 20 else [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a HarmonyOS project for permission and capability hints."
    )
    parser.add_argument("--project", default=".")
    parser.add_argument("--project-id", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        root = find_project_root(args.project)
        identity = project_identity(root, args.project_id)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    permissions, capabilities, scanned = scan(root)
    permission_items = [
        {"name": name, "locations": bounded_locations(locations)}
        for name, locations in sorted(permissions.items())
    ]
    capability_items = [
        {"name": name, "locations": bounded_locations(locations)}
        for name, locations in sorted(capabilities.items())
    ]
    checks = [
        {
            "name": "source_inventory",
            "status": "passed",
            "detail": f"scanned {scanned} project source/config files",
        },
        {
            "name": "entitlement_state",
            "status": "needs_verification",
            "detail": "source inventory cannot prove AGC switches, rights, ACL approval, quota or runtime availability",
        },
    ]
    record = build_record(
        phase="capabilities",
        project_id=identity,
        status="needs_verification",
        inputs={"project": "."},
        outputs={
            "scannedFiles": scanned,
            "permissionMentions": permission_items,
            "capabilityHints": capability_items,
            "limitations": [
                "best-effort textual inventory",
                "does not prove capability enablement, eligibility, approval or runtime authorization",
                "does not replace current official documentation and console checks",
            ],
        },
        checks=checks,
        next_phase="capability_preflight",
    )
    if args.evidence:
        destination = Path(args.evidence).expanduser()
        if not destination.is_absolute():
            destination = root / destination
        write_record(destination, record)
        record["evidencePath"] = evidence_path(destination, root)

    rendered = json.dumps(record, ensure_ascii=False, indent=2)
    if args.json or not args.evidence:
        print(rendered)
    else:
        print(
            f"capability inventory: {len(permission_items)} permission(s), "
            f"{len(capability_items)} capability hint(s); status=needs_verification"
        )
        print(f"evidence: {record['evidencePath']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
