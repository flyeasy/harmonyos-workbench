#!/usr/bin/env python3
"""Validate a safe external-integration test matrix without contacting services."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.evidence import build_record, evidence_path, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402


SCHEMA = "harmonyos.workbench.integration/v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
PLACEHOLDER = re.compile(r"(?i)(^$|example|change[_-]?me|todo|/path/to|\.\.\.)")


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key.strip()):
            raise ValueError(f"invalid env-file line {number}")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def configured(names: list[str], env: dict[str, str]) -> tuple[list[str], list[str]]:
    ready: list[str] = []
    missing: list[str] = []
    for name in names:
        value = env.get(name, "")
        (missing if PLACEHOLDER.search(value) else ready).append(name)
    return ready, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--env-file", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        root = find_project_root(args.project)
        identity = project_identity(root)
        manifest_path = Path(args.manifest).expanduser().resolve()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA or not isinstance(data.get("integrations"), list):
            raise ValueError(f"manifest must use {SCHEMA} and an integrations array")
        env = dict(__import__("os").environ)
        if args.env_file:
            env.update({key: value for key, value in load_env(Path(args.env_file).expanduser()).items() if not env.get(key)})
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"integration plan blocked: {error}") from error

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for raw in data["integrations"]:
        if not isinstance(raw, dict):
            raise SystemExit("integration plan blocked: every integration must be an object")
        item_id = str(raw.get("id", ""))
        if not SAFE_ID.fullmatch(item_id) or item_id in seen:
            raise SystemExit(f"integration plan blocked: invalid or duplicate integration id: {item_id!r}")
        seen.add(item_id)
        required_env = raw.get("requiredEnv", [])
        if not isinstance(required_env, list) or not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)) for name in required_env):
            raise SystemExit(f"integration plan blocked: {item_id}.requiredEnv must contain only variable names")
        execution = str(raw.get("execution", "read_only"))
        if execution not in {"read_only", "writes_isolated_data", "manual"}:
            raise SystemExit(f"integration plan blocked: {item_id}.execution is unsupported")
        ready, missing = configured([str(name) for name in required_env], env)
        isolation_name = str(raw.get("isolationConfirmationEnv", ""))
        isolation_ok = execution != "writes_isolated_data" or (
            bool(isolation_name) and not PLACEHOLDER.search(env.get(isolation_name, ""))
        )
        if missing:
            status, reason = "blocked", "missing_or_placeholder_configuration"
        elif not isolation_ok:
            status, reason = "blocked", "isolated_test_target_not_confirmed"
        else:
            status = "needs_verification" if execution == "manual" else "ready_to_run"
            reason = "manual_evidence_required" if execution == "manual" else "safe_preflight_complete"
        items.append({
            "id": item_id,
            "kind": str(raw.get("kind", "external_service")),
            "requiredFor": str(raw.get("requiredFor", "release")),
            "execution": execution,
            "status": status,
            "reason": reason,
            "configuredEnvNames": ready,
            "missingEnvNames": missing,
            "isolationConfirmationEnv": isolation_name,
            "isolationConfirmed": isolation_ok,
            "evidenceMode": str(raw.get("evidenceMode", "automated")),
        })
    overall = "blocked" if any(item["status"] == "blocked" for item in items) else "needs_verification"
    payload: dict[str, Any] = {
        "schema": "harmonyos.workbench.integration.plan/v1",
        "status": overall,
        "projectId": identity,
        "manifest": evidence_path(manifest_path, root),
        "externalCalls": False,
        "items": items,
    }
    if args.evidence:
        output = Path(args.evidence).expanduser()
        if not output.is_absolute():
            output = root / output
        record = build_record(
            phase="test", project_id=identity, status=overall,
            inputs={"manifest": evidence_path(manifest_path, root), "externalCalls": False},
            outputs={"integrationSummary": [{key: item[key] for key in ("id", "status", "reason")} for item in items]},
            checks=[{"name": item["id"], "status": item["status"], "message": item["reason"]} for item in items],
            next_phase="release",
        )
        payload["evidence"] = str(write_record(output, record))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if overall == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
