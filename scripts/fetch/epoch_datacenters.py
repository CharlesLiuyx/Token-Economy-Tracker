"""Epoch AI Frontier Data Centers 数据集（官方 CSV 下载，CC-BY）。

两个文件：data_centers.csv（当前状态，面板 4a 汇总卡片）+
data_center_timelines.csv（按日期的建设进度，面板 4b 累计增长图）。
字段口径与坑见 docs/sources/epoch_datacenters.md。
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "epoch_datacenters"


def _num(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _strip_tags(value: str) -> str:
    """去掉 Epoch 的置信度标注，如 'SpaceXAI #confident' -> 'SpaceXAI'。"""
    return re.sub(r"\s*#\w+", "", value or "").strip()


def _rows(csv_text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(csv_text.lstrip("﻿"))))


def fetch(cfg: dict) -> dict:
    sites_raw = _rows(net.get_text(cfg["endpoints"]["data_centers_csv"]))
    timeline_raw = _rows(net.get_text(cfg["endpoints"]["timelines_csv"]))

    sites = [
        {
            "name": r["Name"],
            "h100_equivalents": _num(r["Current H100 equivalents"]),
            "power_mw": _num(r["Current power (MW)"]),
            "capital_cost_busd": _num(r["Current total capital cost (2025 USD billions)"]),
            "owner": _strip_tags(r["Owner"]),
            "users": [u for u in (_strip_tags(r["Users"])).split(",") if u.strip()],
            "chip_types": [c for c in (r["Current chip types"] or "").split(",") if c],
            "country": r["Country"],
        }
        for r in sites_raw
    ]
    # 只保留数值列；建设状态描述/来源链接留在源头，不进快照
    timelines = [
        {
            "site": r["Data center"],
            "date": r["Date"],
            "it_power_mw": _num(r["IT power (MW)"]),
            "power_mw": _num(r["Power (MW)"]),
            "h100_equivalents": _num(r["H100 equivalents"]),
        }
        for r in timeline_raw
        if r.get("Date")
    ]

    aggregates = {
        "site_count": len(sites),
        "total_power_mw": round(sum(s["power_mw"] or 0 for s in sites), 1),
        "total_h100_equivalents": round(sum(s["h100_equivalents"] or 0 for s in sites)),
        "total_capital_cost_busd": round(
            sum(s["capital_cost_busd"] or 0 for s in sites), 2
        ),
    }
    return {"sites": sites, "timelines": timelines, "aggregates": aggregates}


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["sites", "timelines", "aggregates"])
    schema.require_nonempty_list(payload["sites"], "sites")
    schema.require_nonempty_list(payload["timelines"], "timelines")
    if len(payload["sites"]) < 30:
        raise schema.SchemaError(f"sites 仅 {len(payload['sites'])} 条，疑似源头截断")
    agg = payload["aggregates"]
    schema.require_positive_number(agg["total_power_mw"], "aggregates.total_power_mw")
    schema.require_positive_number(
        agg["total_h100_equivalents"], "aggregates.total_h100_equivalents"
    )


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
