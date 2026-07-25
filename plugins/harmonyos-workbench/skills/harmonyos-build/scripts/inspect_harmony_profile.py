#!/usr/bin/env python3
"""Verify a signed HAP/APP and report only non-secret embedded Profile facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.discovery import resolve_java, resolve_sign_tool  # noqa: E402
from harmony_common.profile import verify_artifact_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--sdk-home", default="")
    parser.add_argument("--sign-tool", default="")
    parser.add_argument("--java", default="")
    parser.add_argument("--expected-type", choices=("debug", "release"), default="")
    parser.add_argument("--expected-bundle", default="")
    parser.add_argument("--expected-distribution", default="")
    args = parser.parse_args()

    artifact = Path(args.artifact).expanduser().resolve()
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise SystemExit(f"signed artifact not found: {artifact}")
    tool = resolve_sign_tool(args.sign_tool, args.sdk_home)
    java = resolve_java(args.java)
    if not tool:
        raise SystemExit("hap-sign-tool.jar not found")
    if not java:
        raise SystemExit("runnable Java not found")

    result = verify_artifact_profile(
        artifact,
        sign_tool=tool,
        java=java,
        expected_type=args.expected_type,
        expected_bundle=args.expected_bundle,
        expected_distribution=args.expected_distribution,
    )
    errors = result.get("errors", [])
    facts = {
        key: result.get(key)
        for key in ("verified", "type", "distribution", "bundle", "debug_info_present")
    }
    payload = {
        "status": "failed" if errors else "passed",
        "artifact": str(artifact),
        "profile": facts,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
