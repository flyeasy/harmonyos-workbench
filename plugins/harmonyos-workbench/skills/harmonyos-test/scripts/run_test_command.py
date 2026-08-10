#!/usr/bin/env python3
"""Run one test command without a shell and save a redacted evidence record."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

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
    get_binding,
    require_active_lease,
)


SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
]


def redact(text: str, project: Path | None = None) -> str:
    cleaned = text
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "<redacted>", cleaned)
    if project is not None:
        cleaned = cleaned.replace(str(project.resolve()), "<project>")
    cleaned = cleaned.replace(str(Path.home()), "~")
    return cleaned


def redact_argument(value: str, project: Path | None = None) -> str:
    if project is not None:
        if Path(value).is_absolute():
            return evidence_path(value, project)
        prefix, separator, candidate = value.partition("=")
        if separator and Path(candidate).is_absolute():
            return f"{prefix}={evidence_path(candidate, project)}"
    rendered = redact(value, project)
    return "<redacted-arg>" if rendered != value and "<redacted>" in rendered else rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--label", default="test")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--tail-lines", type=int, default=80)
    parser.add_argument("--evidence-dir", default="")
    parser.add_argument("--target", choices=("host", "emulator", "physical"), default="host")
    parser.add_argument("--project-id", default="")
    parser.add_argument("--role", default="primary")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--ui", action="store_true")
    parser.add_argument(
        "--coordinate-ui",
        action="store_true",
        help="mark a UI run that uses screen coordinates; keeps the 10 minute geometry limit",
    )
    parser.add_argument(
        "--preflight-max-age-seconds",
        type=int,
        default=1800,
        help="maximum geometry-preflight age for semantic UI runs (60-3600 seconds)",
    )
    parser.add_argument("--target-preflight-evidence", default="")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise SystemExit("pass the command after --")
    if args.coordinate_ui and not args.ui:
        raise SystemExit("--coordinate-ui requires --ui")
    if not 60 <= args.preflight_max_age_seconds <= 3600:
        raise SystemExit("--preflight-max-age-seconds must be between 60 and 3600")
    try:
        project = find_project_root(args.project)
        identity = project_identity(project, args.project_id)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    target_context: dict[str, object] = {}
    if args.target != "host":
        store = StateStore(Path(args.state_file).expanduser() if args.state_file else None)
        try:
            with store.transaction(write=False) as state:
                binding = get_binding(
                    state,
                    project_id=identity,
                    project_root=str(project),
                    role=args.role,
                )
                lease = require_active_lease(
                    state,
                    project_id=identity,
                    binding=binding,
                )
                target_context = target_evidence(
                    project_id=identity,
                    role=args.role,
                    target_key=binding.get("targetKey", ""),
                    runtime_serial=binding.get("runtimeSerial", ""),
                    fingerprint_digest=binding.get("fingerprintDigest", ""),
                    lease_expires_at=lease.get("expiresAt", ""),
                )
        except RegistryError as error:
            raise SystemExit(f"target preflight blocked: {error}") from error
    if args.ui:
        if args.target == "host":
            raise SystemExit("--ui requires --target emulator or --target physical")
        if not args.target_preflight_evidence:
            raise SystemExit("--ui requires --target-preflight-evidence from harmonyos-targets")
        preflight_path = Path(args.target_preflight_evidence).expanduser().resolve()
        try:
            preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"target preflight evidence is unreadable: {error}") from error
        if (
            preflight.get("schema") != "harmonyos.workbench.evidence/v2"
            or preflight.get("phase") != "targets"
            or preflight.get("status") != "passed"
            or preflight.get("projectId") != identity
        ):
            raise SystemExit("target preflight evidence does not match this project or a passed target phase")
        evidence_target = preflight.get("target", {})
        for field in (
            "projectId",
            "role",
            "targetKeyHash",
            "runtimeSerialHash",
            "fingerprintDigest",
            "leaseExpiresAt",
        ):
            if str(evidence_target.get(field, "")) != str(target_context.get(field, "")):
                raise SystemExit(f"target preflight evidence mismatch: {field}")
        try:
            captured_at = datetime.fromisoformat(str(preflight.get("timestampUtc", "")))
        except ValueError as error:
            raise SystemExit("target preflight evidence has an invalid timestamp") from error
        if captured_at.tzinfo is None:
            raise SystemExit("target preflight evidence timestamp must include a timezone")
        age = datetime.now(timezone.utc) - captured_at
        max_age_seconds = min(args.preflight_max_age_seconds, 600) if args.coordinate_ui else args.preflight_max_age_seconds
        if age < timedelta(minutes=-1) or age > timedelta(seconds=max_age_seconds):
            kind = "coordinate" if args.coordinate_ui else "semantic"
            raise SystemExit(
                f"target preflight evidence is stale for {kind} UI "
                f"({max_age_seconds}s limit); capture a new geometry preflight"
            )
    evidence_dir = Path(args.evidence_dir).expanduser() if args.evidence_dir else project / "artifacts/harmonyos-tests"
    if not evidence_dir.is_absolute():
        evidence_dir = project / evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = re.sub(r"[^A-Za-z0-9_.-]", "_", args.label)
    log_path = evidence_dir / f"{timestamp}-{safe_label}.log"
    json_path = evidence_dir / f"{timestamp}-{safe_label}.json"

    started = time.time()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=project,
            env=dict(os.environ),
            text=True,
            capture_output=True,
            check=False,
            timeout=args.timeout,
        )
        exit_code = completed.returncode
        output = f"{completed.stdout}{completed.stderr}"
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = 124
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        output = f"{stdout}{stderr}\nTIMEOUT after {args.timeout}s\n"
    duration = round(time.time() - started, 3)
    redacted = redact(output, project)
    log_path.write_text(redacted, encoding="utf-8")
    log_path.chmod(0o600)
    status = "passed" if exit_code == 0 else ("blocked" if timed_out else "failed")
    record = build_record(
        phase="test",
        project_id=identity,
        status=status,
        inputs={
            "label": args.label,
            "command": [redact_argument(part, project) for part in command],
            "target": args.target,
            "ui": args.ui,
            "coordinateUi": args.coordinate_ui,
            "preflightMaxAgeSeconds": (
                min(args.preflight_max_age_seconds, 600)
                if args.ui and args.coordinate_ui
                else (args.preflight_max_age_seconds if args.ui else None)
            ),
        },
        outputs={
            "exitCode": exit_code,
            "durationSeconds": duration,
            "log": evidence_path(log_path, project),
        },
        checks=[
            {
                "name": args.label,
                "status": status,
                "timedOut": timed_out,
            }
        ],
        target=target_context or None,
        next_phase="review",
    )
    write_record(json_path, record)
    payload = {
        "label": args.label,
        "project": str(project),
        "projectId": identity,
        "command": [redact_argument(part, project) for part in command],
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "log": str(log_path.resolve()),
        "target": target_context,
        "evidence": str(json_path.resolve()),
    }
    tail = redacted.splitlines()[-max(1, args.tail_lines):]
    if tail:
        print("\n".join(tail))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
