#!/usr/bin/env python3
"""Inventory recent DevEco Testing task artifacts without opening private payloads."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
import time


REPORT_EXTENSIONS = {".html", ".htm", ".xml", ".pdf"}


def task_directories(root: Path) -> list[Path]:
    tasks: list[Path] = []
    for parent in root.glob("*/tasks"):
        if not parent.is_dir():
            continue
        tasks.extend(path for path in parent.iterdir() if path.is_dir())
    return tasks


def task_metadata(root: Path) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for database in root.glob("*/modules/task/task.db"):
        try:
            connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "select taskId, taskName, solutionName, taskState, taskProgress, "
                "taskErrorCode, createTimestamp, startTimestamp, endTimestamp from task_info"
            ).fetchall()
            connection.close()
        except sqlite3.Error:
            continue
        for row in rows:
            records[str(row["taskId"])] = dict(row)
    return records


def safe_report_summary(path: Path) -> dict[str, object]:
    candidates = [
        item for item in (path / "report").glob("*_report.json")
        if not item.name.endswith("_report_expand.json")
    ] if (path / "report").is_dir() else []
    if not candidates:
        return {}
    try:
        report = json.loads(candidates[0].read_text(encoding="utf-8"))
        data_infos = report.get("dataInfos", {})
        info = next(iter(data_infos.values())) if data_infos else {}
        page_items = info.get("pageCount", {}).get("data", [])
        page_count = page_items[0].get("tags", {}) if page_items else {}
        result_items = info.get("executeResult", {}).get("data", [])
        rules = result_items[0].get("tags", {}).get("ruleList", []) if result_items else []
    except (OSError, json.JSONDecodeError, AttributeError, StopIteration):
        return {"status": "unreadable"}
    findings = [
        {
            "rule": item.get("ruleNum", ""),
            "name": item.get("ruleName", ""),
            "status": item.get("stepStatus", ""),
            "pass_rate": item.get("passRate"),
        }
        for item in rules
        if item.get("stepStatus") in {"failed", "conditional", "error"}
    ]
    return {
        "status": "available",
        "task_execution_pass": report.get("taskResult", {}).get("taskPass"),
        "pages": {
            "total": page_count.get("allCount"),
            "passed": page_count.get("passCount"),
            "failed": page_count.get("errorCount"),
        },
        "findings": findings,
    }


def summarize(path: Path, metadata: dict[str, dict[str, object]]) -> dict[str, object]:
    files = [item for item in path.rglob("*") if item.is_file()]
    newest = max((item.stat().st_mtime for item in files), default=path.stat().st_mtime)
    report_candidates = [
        item for item in files
        if item.suffix.lower() in REPORT_EXTENSIONS or "report" in item.name.lower()
    ]
    extensions = Counter(item.suffix.lower() or "<none>" for item in files)
    result = {
        "task_id": path.name,
        "path": str(path),
        "modified_utc": datetime.fromtimestamp(newest, timezone.utc).isoformat(),
        "active_recently": time.time() - newest < 300,
        "file_count": len(files),
        "total_bytes": sum(item.stat().st_size for item in files),
        "extensions": dict(extensions.most_common(12)),
        "report_candidates": [str(item.relative_to(path)) for item in report_candidates[:50]],
    }
    if path.name in metadata:
        result["task"] = metadata[path.name]
    report_summary = safe_report_summary(path)
    if report_summary:
        result["report_summary"] = report_summary
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "DEVECO_TESTING_DATA_HOME",
            str(Path.home() / "Library/Application Support/DevEco Testing"),
        ),
    )
    parser.add_argument("--task-id", default="")
    parser.add_argument("--latest", type=int, default=5)
    args = parser.parse_args()

    root = Path(args.data_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"DevEco Testing data root not found: {root}")
    tasks = task_directories(root)
    metadata = task_metadata(root)
    if args.task_id:
        tasks = [path for path in tasks if path.name == args.task_id]
    tasks.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    payload = {
        "data_root": str(root),
        "tasks": [summarize(path, metadata) for path in tasks[:max(1, args.latest)]],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["tasks"] else 1


if __name__ == "__main__":
    sys.exit(main())
