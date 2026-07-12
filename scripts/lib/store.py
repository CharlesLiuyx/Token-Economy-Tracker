"""append-only 数据层：daily 快照 + latest.json，写入统一走这里。

约定（docs/conventions.md）：
- data/<source>/daily/<YYYY>/<YYYY-MM-DD>.json 写后不改；
  仅当日期落在 refetch_window_days 内允许覆盖（源头数字会修订）。
- data/<source>/latest.json 记录最近一次成功结果，build 的主要输入。
- 每个快照顶层信封：{schema_version, source, fetched_at, source_meta, payload}。
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SCHEMA_VERSION = 1


class ImmutableSnapshotError(Exception):
    """试图改写 refetch 窗口之外的历史快照。"""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def utc_today() -> str:
    return utc_now().strftime("%Y-%m-%d")


def snapshot_path(source: str, date: str, data_dir: Path = DATA) -> Path:
    year = date[:4]
    return data_dir / source / "daily" / year / f"{date}.json"


def latest_path(source: str, data_dir: Path = DATA) -> Path:
    return data_dir / source / "latest.json"


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_latest(source: str, data_dir: Path = DATA) -> dict | None:
    return read_json(latest_path(source, data_dir))


def write_snapshot(
    source: str,
    payload: dict,
    *,
    date: str | None = None,
    refetch_window_days: int = 3,
    source_meta: dict | None = None,
    data_dir: Path = DATA,
) -> Path:
    """写当日（或 --date 回补日）快照并按需更新 latest.json。

    - 目标日期在 refetch 窗口外且文件已存在 -> ImmutableSnapshotError。
    - latest.json 只在快照日期 >= 现有 latest 日期时更新（回补旧数据不回滚 latest）。
    """
    date = date or utc_today()
    path = snapshot_path(source, date, data_dir)

    window_start = utc_now().date() - dt.timedelta(days=refetch_window_days)
    target = dt.date.fromisoformat(date)
    if path.exists() and target < window_start:
        raise ImmutableSnapshotError(
            f"{path} 在 refetch 窗口（{refetch_window_days}d）之外，历史快照不可改写"
        )

    envelope = {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "snapshot_date": date,
        "fetched_at": utc_now().isoformat(timespec="seconds"),
        "source_meta": source_meta or {},
        "payload": payload,
    }
    _write_json(path, envelope)

    existing = read_latest(source, data_dir)
    if existing is None or existing.get("snapshot_date", "") <= date:
        _write_json(latest_path(source, data_dir), envelope)
    return path
