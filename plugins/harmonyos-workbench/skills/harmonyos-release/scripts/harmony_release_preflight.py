#!/usr/bin/env python3
"""Read-only HarmonyOS release preflight and APP signature verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.artifacts import (  # noqa: E402
    app_metadata,
    artifact_candidates,
    sha256_file,
)
from harmony_common.discovery import (  # noqa: E402
    resolve_java,
    resolve_sign_tool,
    run,
)
from harmony_common.evidence import build_record, evidence_path, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402
from harmony_common.profile import verify_artifact_profile  # noqa: E402


PRIVATE_SUFFIXES = {".p12", ".jks", ".keystore", ".pem", ".key", ".p7b"}
EPHEMERAL_EVIDENCE = re.compile(r"(?:/private)?/tmp/|/Users/[^\s\"']+", re.IGNORECASE)


def latest_app(root: Path) -> Path | None:
    apps = artifact_candidates(root, "app", "release")
    return apps[0] if apps else None


def tracked_files(root: Path) -> list[str]:
    if not (root / ".git").exists() and not any((parent / ".git").exists() for parent in root.parents):
        return []
    result = run(["git", "ls-files"], cwd=root)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []


def git_snapshot(root: Path) -> dict[str, object]:
    head = run(["git", "rev-parse", "HEAD"], cwd=root)
    status = run(["git", "status", "--porcelain"], cwd=root)
    diff_check = run(["git", "diff", "--check"], cwd=root)
    return {
        "commit": head.stdout.strip() if head.returncode == 0 else "",
        "dirtyPathCount": len([line for line in status.stdout.splitlines() if line.strip()]) if status.returncode == 0 else 0,
        "diffCheckPassed": diff_check.returncode == 0,
    }


def evidence_durability(root: Path, location: Path) -> dict[str, object]:
    try:
        relative = location.resolve().relative_to(root.resolve())
    except ValueError:
        return {"status": "failed", "reason": "evidence_root_outside_project", "files": 0, "temporaryRefs": 0}
    if not location.is_dir():
        return {"status": "failed", "reason": "evidence_root_missing", "files": 0, "temporaryRefs": 0}
    files = 0
    temporary_refs = 0
    for item in location.rglob("*"):
        if not item.is_file() or item.suffix.lower() not in {".json", ".md", ".txt", ".html", ".log"}:
            continue
        files += 1
        try:
            temporary_refs += len(EPHEMERAL_EVIDENCE.findall(item.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    if temporary_refs:
        return {"status": "failed", "reason": "ephemeral_or_home_path_in_evidence", "files": files, "temporaryRefs": temporary_refs, "path": relative.as_posix()}
    return {"status": "passed", "reason": "", "files": files, "temporaryRefs": 0, "path": relative.as_posix()}


def version_findings(
    metadata: dict[str, str],
    *,
    expected_name: str = "",
    expected_code: str = "",
    previous_code: str = "",
) -> list[tuple[str, str]]:
    """Validate only explicit version expectations; never guess a store's history."""
    findings: list[tuple[str, str]] = []
    current_name = metadata.get("versionName", "")
    current_code = metadata.get("versionCode", "")
    if expected_name and current_name != expected_name:
        findings.append(("version_name_mismatch", "AppScope versionName does not match the expected release version"))
    if expected_code and current_code != expected_code:
        findings.append(("version_code_mismatch", "AppScope versionCode does not match the expected release version"))
    if previous_code:
        try:
            previous = int(previous_code)
            current = int(current_code)
        except ValueError:
            findings.append(("version_code_not_numeric", "previous and current versionCode must be numeric for monotonicity checking"))
        else:
            if current <= previous:
                findings.append(("version_code_not_incremented", "versionCode must be greater than the explicitly supplied previous release versionCode"))
    return findings

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--artifact", default="")
    parser.add_argument("--sdk-home", default="")
    parser.add_argument("--sign-tool", default="")
    parser.add_argument("--java", default="")
    parser.add_argument("--expected-bundle", default="")
    parser.add_argument("--expected-version-name", default="")
    parser.add_argument("--expected-version-code", default="")
    parser.add_argument("--previous-version-code", default="")
    parser.add_argument("--expected-distribution", default="app_gallery")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    parser.add_argument("--require-git-commit", action="store_true")
    parser.add_argument("--evidence-root", default="")
    parser.add_argument("--require-durable-evidence", action="store_true")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        root = find_project_root(args.project)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    identity = project_identity(root)
    findings: list[dict[str, str]] = []

    def finding(level: str, code: str, message: str) -> None:
        findings.append({"level": level, "code": code, "message": message})

    local_profile = root / "build-profile.json5"
    template_profile = root / "build-profile.template.json5"
    if not local_profile.exists():
        finding("error", "local_build_profile_missing", "local build-profile.json5 is missing")
    if not template_profile.exists():
        finding("warning", "build_profile_template_missing", "repository build-profile template is missing")

    tracked = tracked_files(root)
    if "build-profile.json5" in tracked:
        finding("error", "local_build_profile_tracked", "local build-profile.json5 is tracked")
    private_tracked = [
        item for item in tracked
        if Path(item).suffix.lower() in PRIVATE_SUFFIXES or "/material/" in f"/{item}/" or item.startswith("material/")
    ]
    if private_tracked:
        finding("error", "signing_material_tracked", f"{len(private_tracked)} private signing material path(s) are tracked")
    certificates = [item for item in tracked if Path(item).suffix.lower() == ".cer"]
    if certificates:
        finding("warning", "certificate_tracked", f"{len(certificates)} certificate file(s) are tracked; confirm project policy")

    snapshot = git_snapshot(root)
    dirty_count = int(snapshot["dirtyPathCount"])
    if dirty_count:
        finding("error" if args.require_clean_worktree else "warning", "dirty_worktree", f"worktree contains {dirty_count} changed path(s)")
    if args.require_git_commit and not snapshot["commit"]:
        finding("error", "git_commit_missing", "a release handoff requires a Git commit")
    if not snapshot["diffCheckPassed"]:
        finding("error" if args.require_clean_worktree else "warning", "git_diff_check_failed", "git diff --check reported whitespace errors")
    durability: dict[str, object] = {"status": "skipped"}
    if args.evidence_root:
        evidence_root = Path(args.evidence_root).expanduser()
        if not evidence_root.is_absolute():
            evidence_root = root / evidence_root
        durability = evidence_durability(root, evidence_root)
        if durability["status"] != "passed":
            finding("error" if args.require_durable_evidence else "warning", str(durability["reason"]), "release evidence is missing, outside the project, or refers to temporary/private paths")
    elif args.require_durable_evidence:
        finding("error", "evidence_root_missing", "--require-durable-evidence requires --evidence-root")

    artifact = Path(args.artifact).expanduser().resolve() if args.artifact else latest_app(root)
    artifact_info: dict[str, object] = {}
    if artifact and artifact.is_file() and artifact.stat().st_size > 0:
        artifact_info = {
            "path": str(artifact),
            "size": artifact.stat().st_size,
            "sha256": sha256_file(artifact),
            "signed_name": "signed" in artifact.name.lower(),
        }
        if artifact.suffix.lower() != ".app":
            finding("error", "wrong_artifact_type", "final AppGallery candidate must be a .app package")
        if "signed" not in artifact.name.lower():
            finding("warning", "artifact_name_unsigned", "artifact name does not indicate a signed APP")
    else:
        finding("warning", "release_artifact_missing", "no non-empty release APP artifact was found")

    metadata = app_metadata(root)
    for code, message in version_findings(
        metadata,
        expected_name=args.expected_version_name,
        expected_code=args.expected_version_code,
        previous_code=args.previous_version_code,
    ):
        finding("error", code, message)
    expected_bundle = args.expected_bundle or metadata.get("bundleName", "")
    verification: dict[str, object] = {"status": "skipped"}
    if args.verify:
        if not artifact or not artifact.is_file():
            finding("error", "verify_artifact_missing", "cannot verify a missing APP")
        else:
            sign_tool = resolve_sign_tool(args.sign_tool, args.sdk_home)
            if not sign_tool:
                finding("error", "sign_tool_missing", "hap-sign-tool.jar was not found")
            else:
                java = resolve_java(args.java)
                if not java:
                    finding("error", "java_missing", "a runnable Java executable was not found")
                else:
                    verification = verify_artifact_profile(
                        artifact,
                        sign_tool=sign_tool,
                        java=java,
                        expected_type="release",
                        expected_bundle=expected_bundle,
                        expected_distribution=args.expected_distribution,
                        forbid_debug_info=True,
                    )
                    if verification.get("status") != "passed":
                        finding("error", "signature_verification_failed", "; ".join(verification.get("errors", [])) or str(verification.get("message", "verification failed")))

    errors = sum(item["level"] == "error" for item in findings)
    warnings = sum(item["level"] == "warning" for item in findings)
    payload = {
        "status": "failed" if errors or (args.strict and warnings) else "passed",
        "project": str(root),
        "metadata": metadata,
        "gitSnapshot": snapshot,
        "evidenceDurability": durability,
        "artifact": artifact_info,
        "verification": verification,
        "findings": findings,
        "error_count": errors,
        "warning_count": warnings,
    }
    if args.evidence:
        evidence = Path(args.evidence).expanduser()
        if not evidence.is_absolute():
            evidence = root / evidence
        record = build_record(
            phase="release",
            project_id=identity,
            status=payload["status"],
            inputs={
                "artifact": evidence_path(artifact, root),
                "verify": args.verify,
                "strict": args.strict,
                "expectedBundle": expected_bundle,
                "expectedDistribution": args.expected_distribution,
                "expectedVersionName": args.expected_version_name,
                "expectedVersionCode": args.expected_version_code,
                "previousVersionCode": args.previous_version_code,
            },
            outputs={
                "metadata": metadata,
                "gitSnapshot": snapshot,
                "evidenceDurability": durability,
                "artifact": {
                    **artifact_info,
                    "path": evidence_path(artifact, root),
                }
                if artifact_info
                else {},
                "verification": verification,
            },
            checks=[
                {
                    "name": item["code"],
                    "status": "failed" if item["level"] == "error" else "needs_verification",
                    "message": item["message"],
                }
                for item in findings
            ],
            next_phase="",
        )
        payload["evidence"] = str(write_record(evidence, record))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
