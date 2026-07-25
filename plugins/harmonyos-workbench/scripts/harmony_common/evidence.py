"""Normalized evidence records for every HarmonyOS Workbench phase."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from typing import Any


SCHEMA = "harmonyos.workbench.evidence/v2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def privacy_hash(value: object) -> str:
    """Return a stable pseudonymous digest, preserving empty values."""
    rendered = str(value or "")
    if not rendered:
        return ""
    return hashlib.sha256(
        f"harmonyos-workbench:{rendered}".encode("utf-8")
    ).hexdigest()


def evidence_path(value: str | Path | None, project_root: Path) -> str:
    """Represent a path without persisting a user or workspace directory."""
    if value is None or str(value) == "":
        return ""
    path = Path(value).expanduser()
    if not path.is_absolute():
        return path.as_posix()
    resolved = path.resolve()
    try:
        return resolved.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return resolved.name


def target_evidence(
    *,
    project_id: str,
    role: str,
    target_key: object,
    runtime_serial: object = "",
    fingerprint_digest: object = "",
    lease_expires_at: object = "",
) -> dict[str, str]:
    """Build a durable target reference without raw device identifiers."""
    return {
        "projectId": project_id,
        "role": role,
        "targetKeyHash": privacy_hash(target_key),
        "runtimeSerialHash": privacy_hash(runtime_serial),
        "fingerprintDigest": str(fingerprint_digest or ""),
        "leaseExpiresAt": str(lease_expires_at or ""),
    }


def build_record(
    *,
    phase: str,
    project_id: str,
    status: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    checks: list[dict[str, Any]] | None = None,
    target: dict[str, Any] | None = None,
    next_phase: str = "",
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "runId": secrets.token_hex(8),
        "timestampUtc": utc_now(),
        "phase": phase,
        "projectId": project_id,
        "status": status,
        "inputs": inputs or {},
        "outputs": outputs or {},
        "checks": checks or [],
    }
    if target:
        record["target"] = target
    if next_phase:
        record["nextPhase"] = next_phase
    return record


def write_record(path: Path, record: dict[str, Any]) -> Path:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)
    return path.resolve()
