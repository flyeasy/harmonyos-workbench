#!/usr/bin/env python3
"""Run a reproducible HarmonyOS Hvigor build and summarize its artifact."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.artifacts import artifact_candidates, sha256_file  # noqa: E402
from harmony_common.discovery import resolve_hvigor, resolve_sdk  # noqa: E402
from harmony_common.evidence import build_record, evidence_path, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--artifact", choices=("hap", "app"), default="hap")
    parser.add_argument("--mode", choices=("debug", "release"), default="debug")
    parser.add_argument("--module", default="entry")
    parser.add_argument("--target", default="default")
    parser.add_argument("--product", default="default")
    parser.add_argument("--sdk-home", default="")
    parser.add_argument("--hvigorw", default="")
    parser.add_argument("--no-daemon", action="store_true")
    parser.add_argument("--no-parallel", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        root = find_project_root(args.project, require_build_files=True)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    sdk_home = resolve_sdk(args.sdk_home)
    hvigor = resolve_hvigor(args.hvigorw, root, sdk_home)
    if not sdk_home:
        raise SystemExit("DevEco SDK not found; pass --sdk-home or set DEVECO_SDK_HOME")
    if not hvigor:
        raise SystemExit("hvigorw not found; pass --hvigorw or set HVIGORW_PATH")
    identity = project_identity(root)

    if args.artifact == "hap":
        command = [
            hvigor, "assembleHap", "--mode", "module",
            "-p", f"module={args.module}@{args.target}",
            "-p", f"product={args.product}",
        ]
    else:
        command = [hvigor, "assembleApp", "--mode", "project", "-p", f"product={args.product}"]
    if not args.no_daemon:
        command.append("--daemon")
    if not args.no_parallel:
        command.append("--parallel")
    command.extend(["-p", f"buildMode={args.mode}"])

    summary: dict[str, object] = {
        "project": str(root),
        "artifact_type": args.artifact,
        "mode": args.mode,
        "module": args.module if args.artifact == "hap" else None,
        "target": args.target if args.artifact == "hap" else None,
        "product": args.product,
        "sdk_home": sdk_home,
        "hvigorw": hvigor,
        "command": command,
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        summary["status"] = "planned"
    else:
        environment = dict(os.environ)
        environment["DEVECO_SDK_HOME"] = sdk_home
        started = time.time()
        completed = subprocess.run(command, cwd=root, env=environment, check=False)
        summary["duration_seconds"] = round(time.time() - started, 3)
        summary["exit_code"] = completed.returncode
        if completed.returncode != 0:
            summary["status"] = "failed"
        else:
            candidates = artifact_candidates(root, args.artifact, args.mode)
            if not candidates:
                summary["status"] = "failed_no_artifact"
            else:
                artifact = candidates[0]
                summary.update({
                    "status": "passed",
                    "artifact": str(artifact),
                    "artifact_size": artifact.stat().st_size,
                    "sha256": sha256_file(artifact),
                })

    if args.evidence:
        evidence = Path(args.evidence).expanduser()
        if not evidence.is_absolute():
            evidence = root / evidence
        record = build_record(
            phase="build",
            project_id=identity,
            status=str(summary.get("status", "failed")),
            inputs={
                "artifactType": args.artifact,
                "mode": args.mode,
                "module": args.module,
                "target": args.target,
                "product": args.product,
                "command": [Path(command[0]).name, *command[1:]],
            },
            outputs={
                key: (
                    evidence_path(str(summary[key]), root)
                    if key == "artifact"
                    else summary[key]
                )
                for key in ("artifact", "artifact_size", "sha256", "duration_seconds")
                if key in summary
            },
            checks=[
                {
                    "name": "hvigor",
                    "status": "passed"
                    if summary.get("status") in {"planned", "passed"}
                    else "failed",
                }
            ],
            next_phase="targets" if args.artifact == "hap" else "release",
        )
        summary["evidence"] = str(write_record(evidence, record))

    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    return 0 if summary.get("status") in {"planned", "passed"} else int(summary.get("exit_code", 1) or 1)


if __name__ == "__main__":
    sys.exit(main())
