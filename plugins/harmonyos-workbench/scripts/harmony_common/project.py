"""HarmonyOS project discovery and stable local identities."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re


def find_project_root(value: str | Path, *, require_build_files: bool = False) -> Path:
    start = Path(value).expanduser().resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        has_package = (candidate / "oh-package.json5").exists()
        has_build = (candidate / "hvigorfile.ts").exists() or (
            candidate / "build-profile.json5"
        ).exists()
        if has_package and (has_build or not require_build_files):
            return candidate
    raise ValueError(f"HarmonyOS project root not found from: {start}")


def project_identity(root: Path, explicit: str = "") -> str:
    if explicit:
        normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", explicit).strip("-")
        if not normalized:
            raise ValueError("project id contains no usable characters")
        return normalized
    canonical = str(root.expanduser().resolve())
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", root.name).strip("-") or "project"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"
