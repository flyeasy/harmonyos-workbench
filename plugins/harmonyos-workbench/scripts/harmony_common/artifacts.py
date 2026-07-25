"""Artifact discovery, hashing, and non-secret app metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_candidates(root: Path, suffix: str, mode: str = "") -> list[Path]:
    found = [
        path
        for path in root.rglob(f"*.{suffix}")
        if "build" in path.parts
        and "outputs" in path.parts
        and path.is_file()
        and path.stat().st_size > 0
    ]
    if mode == "release":
        found.sort(
            key=lambda path: ("signed" in path.name.lower(), path.stat().st_mtime),
            reverse=True,
        )
    else:
        found.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return found


def app_metadata(root: Path) -> dict[str, str]:
    app_file = root / "AppScope/app.json5"
    if not app_file.exists():
        return {}
    text = app_file.read_text(encoding="utf-8", errors="ignore")
    result: dict[str, str] = {}
    for key in ("bundleName", "versionName", "versionCode"):
        match = re.search(
            rf'["\']?{key}["\']?\s*:\s*["\']?([^,"\'\n}}]+)',
            text,
        )
        if match:
            result[key] = match.group(1).strip()
    return result
