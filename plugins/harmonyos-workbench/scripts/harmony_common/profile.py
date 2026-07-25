"""Verify a HAP/APP signature and expose only non-secret Profile facts."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from .discovery import run


def verify_artifact_profile(
    artifact: Path,
    *,
    sign_tool: str,
    java: str,
    expected_type: str = "",
    expected_bundle: str = "",
    expected_distribution: str = "",
    forbid_debug_info: bool = False,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="harmony-profile-") as directory:
        temp = Path(directory)
        cert = temp / "cert-chain.cer"
        profile = temp / "profile.p7b"
        decoded_file = temp / "profile.json"
        verified = run(
            [
                java,
                "-jar",
                sign_tool,
                "verify-app",
                "-inFile",
                str(artifact),
                "-outCertChain",
                str(cert),
                "-outProfile",
                str(profile),
            ],
            timeout=120,
        )
        if verified.returncode != 0:
            return {"status": "error", "message": "verify-app failed", "errors": ["verify-app failed"]}
        decoded = run(
            [
                java,
                "-jar",
                sign_tool,
                "verify-profile",
                "-inFile",
                str(profile),
                "-outFile",
                str(decoded_file),
            ],
            timeout=120,
        )
        if decoded.returncode != 0 or not decoded_file.exists():
            return {
                "status": "error",
                "message": "verify-profile failed",
                "errors": ["verify-profile failed"],
            }
        try:
            data = json.loads(decoded_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "status": "error",
                "message": "verified Profile could not be decoded",
                "errors": ["verified Profile could not be decoded"],
            }

    content = data.get("content", {})
    facts = {
        "verified": data.get("verifiedPassed") is True,
        "type": content.get("type", ""),
        "distribution": content.get("app-distribution-type", ""),
        "bundle": content.get("bundle-info", {}).get("bundle-name", ""),
        "debug_info_present": bool(content.get("debug-info")),
    }
    errors: list[str] = []
    if not facts["verified"]:
        errors.append("Profile signature is invalid")
    if expected_type and facts["type"] != expected_type:
        errors.append(f"expected type {expected_type}, got {facts['type'] or 'missing'}")
    if expected_bundle and facts["bundle"] != expected_bundle:
        errors.append(
            f"expected bundle {expected_bundle}, got {facts['bundle'] or 'missing'}"
        )
    if expected_distribution and facts["distribution"] != expected_distribution:
        errors.append(
            "expected distribution "
            f"{expected_distribution}, got {facts['distribution'] or 'missing'}"
        )
    if forbid_debug_info and facts["debug_info_present"]:
        errors.append("release Profile contains debug-info")
    return {
        "status": "error" if errors else "passed",
        **facts,
        "errors": errors,
    }
