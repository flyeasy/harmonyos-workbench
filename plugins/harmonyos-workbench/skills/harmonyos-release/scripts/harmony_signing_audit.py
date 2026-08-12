#!/usr/bin/env python3
"""Read-only audit for HarmonyOS signing identity and debug/release Profiles.

The command deliberately never creates, moves, copies, or unlocks signing material
unless --verify-p12 is explicitly supplied.  Its JSON output contains only boolean
facts and redacted material roles, never passwords, certificate bodies, or paths.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.discovery import resolve_java, resolve_sign_tool  # noqa: E402
from harmony_common.evidence import build_record, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402


CERTIFICATE_PATTERN = re.compile(
    rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL
)


def command(command: list[str], *, input_bytes: bytes | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run one local tool without a shell and without relaying its sensitive output."""
    try:
        return subprocess.run(
            command,
            input=input_bytes,
            env=env,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(command, 1, b"", b"")


def public_key_hash(public_key: bytes) -> str:
    converted = command(["openssl", "pkey", "-pubin", "-outform", "DER"], input_bytes=public_key)
    if converted.returncode != 0 or not converted.stdout:
        raise ValueError("a public key could not be normalized")
    return hashlib.sha256(converted.stdout).hexdigest()


def csr_key_hash(path: Path) -> str:
    verified = command(["openssl", "req", "-in", str(path), "-noout", "-verify"])
    if verified.returncode != 0:
        raise ValueError("CSR signature is invalid or unreadable")
    public_key = command(["openssl", "req", "-in", str(path), "-pubkey", "-noout"])
    if public_key.returncode != 0 or not public_key.stdout:
        raise ValueError("CSR public key could not be read")
    return public_key_hash(public_key.stdout)


def certificate_blocks(path: Path) -> list[bytes]:
    raw = path.read_bytes()
    blocks = CERTIFICATE_PATTERN.findall(raw)
    if blocks:
        return blocks
    for form in ("DER", "PEM"):
        rendered = command(
            ["openssl", "pkcs7", "-inform", form, "-in", str(path), "-print_certs"]
        )
        blocks = CERTIFICATE_PATTERN.findall(rendered.stdout)
        if blocks:
            return blocks
    rendered = command(["openssl", "x509", "-inform", "DER", "-in", str(path), "-outform", "PEM"])
    blocks = CERTIFICATE_PATTERN.findall(rendered.stdout)
    return blocks


def certificate_key_hash(certificate: bytes) -> str:
    public_key = command(["openssl", "x509", "-pubkey", "-noout"], input_bytes=certificate)
    if public_key.returncode != 0 or not public_key.stdout:
        raise ValueError("certificate public key could not be read")
    return public_key_hash(public_key.stdout)


def certificate_is_current(certificate: bytes) -> bool:
    return command(["openssl", "x509", "-checkend", "0", "-noout"], input_bytes=certificate).returncode == 0


def decoded_profile(path: Path, *, sign_tool: str, java: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="harmony-signing-audit-") as directory:
        output = Path(directory) / "profile.json"
        result = command(
            [java, "-jar", sign_tool, "verify-profile", "-inFile", str(path), "-outFile", str(output)]
        )
        if result.returncode != 0 or not output.is_file():
            raise ValueError("Profile signature could not be verified")
        try:
            return json.loads(output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("verified Profile could not be decoded") from error


def profile_facts(profile: dict[str, Any]) -> dict[str, Any]:
    content = profile.get("content") or {}
    bundle = content.get("bundle-info") or {}
    return {
        "verified": profile.get("verifiedPassed") is True,
        "type": str(content.get("type") or ""),
        "bundle": str(bundle.get("bundle-name") or ""),
        "app_id": str(bundle.get("app-identifier") or ""),
        "distribution": str(content.get("app-distribution-type") or ""),
        "debug_info_present": bool(content.get("debug-info")),
        "distribution_certificate": str(bundle.get("distribution-certificate") or ""),
    }


def profile_findings(
    facts: dict[str, Any],
    *,
    kind: str,
    expected_bundle: str,
    expected_app_id: str,
    expected_distribution: str,
    identity_key_hash: str,
) -> list[str]:
    """Return generic failures only; no identity, path, or certificate contents leak."""
    errors: list[str] = []
    if not facts["verified"]:
        errors.append("Profile signature verification failed")
    if facts["type"] != kind:
        errors.append("Profile type does not match the requested signing kind")
    if expected_bundle and facts["bundle"] != expected_bundle:
        errors.append("Profile bundle does not match the expected bundle")
    if expected_app_id and facts["app_id"] != expected_app_id:
        errors.append("Profile App ID does not match the expected App ID")
    if kind == "release":
        if facts["distribution"] != expected_distribution:
            errors.append("release Profile distribution does not match the expected distribution")
        if facts["debug_info_present"]:
            errors.append("release Profile contains debug device information")
    elif not facts["debug_info_present"]:
        errors.append("debug Profile has no debug device information")
    certificate = facts["distribution_certificate"].encode("utf-8")
    blocks = CERTIFICATE_PATTERN.findall(certificate)
    if len(blocks) != 1:
        errors.append("Profile does not contain one readable distribution certificate")
    else:
        try:
            if certificate_key_hash(blocks[0]) != identity_key_hash:
                errors.append("Profile distribution certificate does not match the CSR/CER identity")
        except ValueError:
            errors.append("Profile distribution certificate could not be checked")
    return errors


def verify_p12(path: Path, expected_key_hash: str) -> tuple[bool, str]:
    password = getpass.getpass("P12 store password (input is hidden): ")
    environment = dict(os.environ)
    environment["HARMONYOS_SIGNING_AUDIT_PASSWORD"] = password
    result = command(
        [
            "keytool", "-list", "-rfc", "-storetype", "PKCS12", "-keystore", str(path),
            "-storepass:env", "HARMONYOS_SIGNING_AUDIT_PASSWORD",
        ],
        env=environment,
    )
    password = ""
    environment.pop("HARMONYOS_SIGNING_AUDIT_PASSWORD", None)
    if result.returncode != 0:
        return False, "P12 could not be unlocked or read"
    blocks = CERTIFICATE_PATTERN.findall(result.stdout)
    try:
        matched = any(certificate_key_hash(block) == expected_key_hash for block in blocks)
    except ValueError:
        matched = False
    return matched, "P12 certificate public key was checked" if matched else "P12 public key does not match the CSR/CER identity"


def existing_file(value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{label} is missing or empty")
    return path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only HarmonyOS signing quartet audit")
    parser.add_argument("--kind", choices=("debug", "release"), default="release")
    parser.add_argument("--p12", required=True, help="local PKCS#12 keystore; its path is never emitted")
    parser.add_argument("--csr", required=True, help="CSR corresponding to the signing identity")
    parser.add_argument("--certificate", required=True, help="CER/PEM/PKCS7 signing certificate")
    parser.add_argument("--profile", default="", help="debug or release Profile (.p7b)")
    parser.add_argument("--allow-identity-only", action="store_true")
    parser.add_argument("--verify-p12", action="store_true", help="prompt locally to prove P12 ↔ CSR/CER key continuity")
    parser.add_argument("--expected-bundle", default="")
    parser.add_argument("--expected-app-id", default="")
    parser.add_argument("--expected-distribution", default="app_gallery")
    parser.add_argument("--sdk-home", default="")
    parser.add_argument("--sign-tool", default="")
    parser.add_argument("--java", default="")
    parser.add_argument("--project", default=".")
    parser.add_argument("--evidence", default="")
    args = parser.parse_args()

    errors: list[str] = []
    checks: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "status": "failed",
        "kind": args.kind,
        "identity": {"p12Present": False, "csrCerMatch": False, "p12KeyMatch": "not_checked"},
        "profile": {"status": "not_checked"},
        "errors": errors,
    }
    root: Path | None = None
    if args.evidence:
        try:
            root = find_project_root(args.project)
        except ValueError:
            errors.append("project root could not be resolved for evidence")

    try:
        p12 = existing_file(args.p12, "P12 keystore")
        csr = existing_file(args.csr, "CSR")
        certificate = existing_file(args.certificate, "certificate")
        result["identity"]["p12Present"] = True
        identity_hash = csr_key_hash(csr)
        matches: list[bytes] = []
        for block in certificate_blocks(certificate):
            try:
                if certificate_key_hash(block) == identity_hash:
                    matches.append(block)
            except ValueError:
                continue
        if len(matches) != 1:
            errors.append("CSR/CER public keys do not identify exactly one signing certificate")
        else:
            result["identity"]["csrCerMatch"] = True
            if not certificate_is_current(matches[0]):
                errors.append("signing certificate has expired or is not yet valid")
        if args.verify_p12:
            p12_matches, message = verify_p12(p12, identity_hash)
            result["identity"]["p12KeyMatch"] = p12_matches
            if not p12_matches:
                errors.append(message)
        elif args.kind == "release":
            result["identity"]["p12KeyMatch"] = "not_unlocked"
            checks.append({"name": "p12_key_continuity", "status": "needs_verification"})

        if args.profile:
            profile = existing_file(args.profile, "Profile")
            sign_tool = resolve_sign_tool(args.sign_tool, args.sdk_home)
            java = resolve_java(args.java)
            if not sign_tool or not java:
                errors.append("hap-sign-tool.jar and runnable Java are required to verify a Profile")
            else:
                facts = profile_facts(decoded_profile(profile, sign_tool=sign_tool, java=java))
                profile_errors = profile_findings(
                    facts,
                    kind=args.kind,
                    expected_bundle=args.expected_bundle,
                    expected_app_id=args.expected_app_id,
                    expected_distribution=args.expected_distribution,
                    identity_key_hash=identity_hash,
                )
                errors.extend(profile_errors)
                result["profile"] = {
                    "status": "passed" if not profile_errors else "failed",
                    "typeMatches": facts["type"] == args.kind,
                    "bundleMatches": not args.expected_bundle or facts["bundle"] == args.expected_bundle,
                    "appIdMatches": not args.expected_app_id or facts["app_id"] == args.expected_app_id,
                    "distributionMatches": args.kind != "release" or facts["distribution"] == args.expected_distribution,
                    "hasDebugInfo": facts["debug_info_present"],
                    "certificateMatches": not any("distribution certificate" in value for value in profile_errors),
                }
        elif not args.allow_identity_only:
            errors.append("Profile is required unless --allow-identity-only is explicitly used")
    except ValueError as error:
        errors.append(str(error))

    result["status"] = "passed" if not errors else "failed"
    if args.evidence:
        if root is None:
            errors.append("cannot write evidence without a resolved project root")
            result["status"] = "failed"
        else:
            evidence = Path(args.evidence).expanduser()
            if not evidence.is_absolute():
                evidence = root / evidence
            record = build_record(
                phase="release",
                project_id=project_identity(root),
                status=result["status"],
                inputs={
                    "kind": args.kind,
                    "expectedBundleProvided": bool(args.expected_bundle),
                    "expectedAppIdProvided": bool(args.expected_app_id),
                    "profileProvided": bool(args.profile),
                    "verifyP12": args.verify_p12,
                },
                outputs={"identity": result["identity"], "profile": result["profile"]},
                checks=[*checks, *[{"name": "signing_quartet", "status": result["status"]}]],
                next_phase="build" if result["status"] == "passed" else "",
            )
            result["evidence"] = str(write_record(evidence, record))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
