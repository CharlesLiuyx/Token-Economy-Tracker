"""data/_status.json：每源 last_success / last_attempt / error。

build 读它生成页面新鲜度徽章（>48h 黄、>7d 红）；runbook 用它排查缺数。
按源合并更新（fetcher 各自上报，互不覆盖）。
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.store import DATA, read_json, utc_now


def status_path(data_dir: Path = DATA) -> Path:
    return data_dir / "_status.json"


def load(data_dir: Path = DATA) -> dict:
    return read_json(status_path(data_dir)) or {}

def record(source: str, *, ok: bool, error: str | None = None, data_dir: Path = DATA) -> dict:
    now = utc_now().isoformat(timespec="seconds")
    all_status = load(data_dir)
    entry = all_status.get(source, {})
    entry["last_attempt"] = now
    if ok:
        entry["last_success"] = now
        entry["error"] = None
    else:
        entry["error"] = (error or "unknown error")[:500]
    all_status[source] = entry

    path = status_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(all_status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return entry
