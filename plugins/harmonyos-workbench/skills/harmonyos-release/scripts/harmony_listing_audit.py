#!/usr/bin/env python3
"""Validate AppGallery listing assets without uploading or rewriting them.

The audit applies the Workbench AppGallery icon baseline: a 1024 px square PNG,
at most 3 MiB, with no alpha channel/transparency. It intentionally reports only
field-presence and image facts, never listing copy, private links, or file paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Any
from urllib.parse import urlparse

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harmony_common.evidence import build_record, write_record  # noqa: E402
from harmony_common.project import find_project_root, project_identity  # noqa: E402


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_ICON_BYTES = 3 * 1024 * 1024
REQUIRED_LISTING_FIELDS = (
    "appName",
    "oneLineIntroduction",
    "introduction",
    "privacyStatementUrl",
    "privacyStatementVersion",
    "privacyStatementReviewedAt",
    "screenshots",
)


def png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("icon is not a PNG file")
    position = len(PNG_SIGNATURE)
    chunks: list[tuple[bytes, bytes]] = []
    while position + 12 <= len(data):
        length = struct.unpack(">I", data[position : position + 4]
        )[0]
        kind = data[position + 4 : position + 8]
        end = position + 8 + length
        if end + 4 > len(data):
            raise ValueError("PNG file is truncated")
        chunks.append((kind, data[position + 8 : end]))
        position = end + 4
        if kind == b"IEND":
            break
    if not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise ValueError("PNG IHDR is missing or invalid")
    if chunks[-1][0] != b"IEND":
        raise ValueError("PNG IEND is missing")
    return chunks


def icon_facts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    chunks = png_chunks(data)
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1]
    )
    has_alpha_channel = color_type in {4, 6}
    has_transparency_chunk = any(kind == b"tRNS" for kind, _ in chunks)
    return {
        "png": True,
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "hasAlphaChannel": has_alpha_channel,
        "hasTransparencyChunk": has_transparency_chunk,
        "byteSize": len(data),
        "compressionMethod": compression,
        "filterMethod": filter_method,
        "interlaceMethod": interlace,
    }


def icon_findings(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if facts["width"] != 1024 or facts["height"] != 1024:
        errors.append("icon dimensions must be exactly 1024×1024")
    if facts["byteSize"] > MAX_ICON_BYTES:
        errors.append("icon must not exceed 3 MiB")
    if facts["hasAlphaChannel"] or facts["hasTransparencyChunk"]:
        errors.append("icon must not contain an alpha channel or transparency")
    return errors


def listing_facts(data: object) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"localeCount": 0, "locales": {}}, ["listing JSON must be an object"]
    locales = data.get("locales")
    if not isinstance(locales, dict) or not locales:
        return {"localeCount": 0, "locales": {}}, ["listing must declare at least one locale"]
    summary: dict[str, Any] = {}
    for locale, value in locales.items():
        key = str(locale)
        locale_errors: list[str] = []
        if not isinstance(value, dict):
            errors.append(f"listing locale {key} must be an object")
            summary[key] = {"status": "failed", "fieldPresence": {}}
            continue
        presence = {
            field: (
                isinstance(value.get(field), list) and bool(value[field])
                if field == "screenshots"
                else isinstance(value.get(field), str) and bool(value[field].strip())
            )
            for field in REQUIRED_LISTING_FIELDS
        }
        for field, present in presence.items():
            if not present:
                locale_errors.append(f"listing locale {key} is missing {field}")
        privacy_url = str(value.get("privacyStatementUrl") or "")
        parsed = urlparse(privacy_url)
        if privacy_url and (parsed.scheme != "https" or not parsed.netloc):
            locale_errors.append(f"listing locale {key} privacyStatementUrl must be an HTTPS URL")
        screenshots = value.get("screenshots")
        if screenshots and (not isinstance(screenshots, list) or not all(isinstance(item, str) and item for item in screenshots)):
            locale_errors.append(f"listing locale {key} screenshots must be a non-empty string list")
        summary[key] = {
            "status": "failed" if locale_errors else "passed",
            "fieldPresence": presence,
            "screenshotCount": len(screenshots) if isinstance(screenshots, list) else 0,
            "privacyUrlIsHttps": bool(privacy_url and parsed.scheme == "https" and parsed.netloc),
        }
        errors.extend(locale_errors)
    return {"localeCount": len(summary), "locales": summary}, errors


def read_listing(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("listing JSON could not be read") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only AppGallery listing and icon audit")
    parser.add_argument("--icon", required=True, help="1024×1024 opaque PNG; path is not emitted")
    parser.add_argument("--listing", required=True, help="release listing JSON; copy is not emitted")
    parser.add_argument("--project", default=".")
    parser.add_argument("--evidence", default="")
    args = parser.parse_args()

    errors: list[str] = []
    result: dict[str, Any] = {
        "status": "failed",
        "icon": {},
        "listing": {},
        "errors": errors,
    }
    try:
        icon = Path(args.icon).expanduser().resolve()
        if not icon.is_file() or icon.stat().st_size == 0:
            raise ValueError("icon is missing or empty")
        facts = icon_facts(icon)
        icon_errors = icon_findings(facts)
        errors.extend(icon_errors)
        result["icon"] = {
            "status": "failed" if icon_errors else "passed",
            "png": facts["png"],
            "width": facts["width"],
            "height": facts["height"],
            "byteSize": facts["byteSize"],
            "hasAlphaChannel": facts["hasAlphaChannel"],
            "hasTransparencyChunk": facts["hasTransparencyChunk"],
            "opaqueCornerShapeRequiresVisualReview": True,
        }
        listing = Path(args.listing).expanduser().resolve()
        if not listing.is_file() or listing.stat().st_size == 0:
            raise ValueError("listing JSON is missing or empty")
        listing_summary, listing_errors = listing_facts(read_listing(listing))
        result["listing"] = listing_summary
        errors.extend(listing_errors)
    except ValueError as error:
        errors.append(str(error))

    result["status"] = "passed" if not errors else "failed"
    if args.evidence:
        try:
            root = find_project_root(args.project)
        except ValueError:
            errors.append("project root could not be resolved for evidence")
            result["status"] = "failed"
        else:
            evidence = Path(args.evidence).expanduser()
            if not evidence.is_absolute():
                evidence = root / evidence
            record = build_record(
                phase="release",
                project_id=project_identity(root),
                status=result["status"],
                inputs={"iconBaseline": "1024px_png_3MiB_opaque", "listingProvided": True},
                outputs={"icon": result["icon"], "listing": result["listing"]},
                checks=[{"name": "store_listing", "status": result["status"]}],
            )
            result["evidence"] = str(write_record(evidence, record))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
