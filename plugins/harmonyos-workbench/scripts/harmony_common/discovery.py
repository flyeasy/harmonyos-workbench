"""Discover HarmonyOS tools and run subprocesses without a shell."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Iterable


def first_path(
    candidates: Iterable[str | Path],
    *,
    file_only: bool = False,
    executable: bool = False,
) -> str:
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if file_only and not path.is_file():
            continue
        if not file_only and not path.exists():
            continue
        if executable and not os.access(path, os.X_OK):
            continue
        return str(path.resolve())
    return ""


def resolve_sdk(explicit: str = "") -> str:
    return first_path(
        [
            explicit,
            os.environ.get("DEVECO_SDK_HOME", ""),
            Path.home() / "Downloads/command-line-tools/sdk/default",
            "/Applications/DevEco-Studio.app/Contents/sdk/default",
            "/Applications/DevEco-Studio.app/Contents/sdk",
        ]
    )


def resolve_hvigor(explicit: str, project_root: Path, sdk_home: str = "") -> str:
    sdk = Path(sdk_home) if sdk_home else None
    candidates: list[str | Path] = [
        explicit,
        os.environ.get("HVIGORW_PATH", ""),
        shutil.which("hvigorw") or "",
        project_root / "hvigorw",
        project_root / "hvigor/bin/hvigorw",
    ]
    if sdk:
        candidates.append(sdk.parent.parent / "hvigor/bin/hvigorw")
    candidates.append(Path.home() / "Downloads/command-line-tools/hvigor/bin/hvigorw")
    return first_path(candidates, file_only=True, executable=True)


def resolve_hdc(explicit: str = "", sdk_home: str = "") -> str:
    sdk = sdk_home or os.environ.get("DEVECO_SDK_HOME", "")
    candidates: list[str | Path] = [
        explicit,
        os.environ.get("HDC_PATH", ""),
        shutil.which("hdc") or "",
    ]
    if sdk:
        candidates.extend(
            [
                Path(sdk) / "openharmony/toolchains/hdc",
                Path(sdk) / "default/openharmony/toolchains/hdc",
            ]
        )
    candidates.extend(
        [
            Path.home() / "Downloads/command-line-tools/sdk/default/openharmony/toolchains/hdc",
            "/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/hdc",
        ]
    )
    return first_path(candidates, file_only=True, executable=True)


def resolve_emulator(explicit: str = "") -> str:
    return first_path(
        [
            explicit,
            os.environ.get("DEVECO_EMULATOR_BIN", ""),
            "/Applications/DevEco-Studio.app/Contents/tools/emulator/Emulator",
        ],
        file_only=True,
        executable=True,
    )


def resolve_java(explicit: str = "") -> str:
    candidates: list[str | Path] = [explicit]
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        candidates.append(Path(java_home) / "bin/java")
    candidates.extend(
        [
            "/Applications/DevEco-Studio.app/Contents/jbr/Contents/Home/bin/java",
            "/Applications/DevEco_Testing_for_App.app/Contents/PlugIns/java.jdk/Contents/Home/bin/java",
            shutil.which("java") or "",
        ]
    )
    return first_path(candidates, file_only=True, executable=True)


def resolve_sign_tool(explicit: str = "", sdk_home: str = "") -> str:
    candidates: list[str | Path] = [explicit, os.environ.get("HAP_SIGN_TOOL", "")]
    for value in filter(None, [sdk_home, os.environ.get("DEVECO_SDK_HOME", "")]):
        root = Path(value).expanduser()
        candidates.extend(
            [
                root / "openharmony/toolchains/lib/hap-sign-tool.jar",
                root / "default/openharmony/toolchains/lib/hap-sign-tool.jar",
            ]
        )
    candidates.extend(
        [
            Path.home()
            / "Downloads/command-line-tools/sdk/default/openharmony/toolchains/lib/hap-sign-tool.jar",
            "/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/lib/hap-sign-tool.jar",
        ]
    )
    return first_path(candidates, file_only=True)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 60,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        stderr = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        return subprocess.CompletedProcess(
            command,
            124,
            stdout,
            stderr or f"command timed out after {timeout}s",
        )


def parse_targets(output: str) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line == "[Empty]":
            continue
        fields = re.split(r"\s+", line)
        targets.append(
            {
                "serial": fields[0],
                "transport": fields[1] if len(fields) > 1 else "",
                "status": fields[2] if len(fields) > 2 else "Unknown",
                "raw": line,
            }
        )
    return targets


def connected_targets(hdc: str) -> list[dict[str, str]]:
    if not hdc:
        return []
    result = run([hdc, "list", "targets", "-v"], timeout=30)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "hdc target listing failed").strip())
    return parse_targets(result.stdout)
