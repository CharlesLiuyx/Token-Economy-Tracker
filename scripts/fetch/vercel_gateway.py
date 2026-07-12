"""Vercel AI Gateway 排行榜（非官方：解析页面 RSC flight 载荷，高风险源）。

/ai-gateway/leaderboards 内嵌 rawData：~61 天 × {tokens, cost, requests} 每日
各模型份额（百分比，非绝对量）。解析细节与坑见 docs/sources/vercel_gateway.md 与 ADR-003。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "vercel_gateway"
PAGE = "https://vercel.com/ai-gateway/leaderboards"
UA_BROWSER = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
KEEP_METRICS = ("tokens", "cost", "requests")
TOP_N = 20


def _flight_blob(html: str) -> str:
    """拼接 Next.js RSC flight 载荷（self.__next_f.push([1,"..."]) 的字符串块）。"""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"((?:[^"\\]|\\.)*)"\]\)', html)
    return "".join(json.loads(f'"{c}"') for c in chunks)


def _balanced_array(s: str, start: int) -> str:
    depth = 0
    for j in range(start, len(s)):
        if s[j] == "[":
            depth += 1
        elif s[j] == "]":
            depth -= 1
            if depth == 0:
                return s[start : j + 1]
    raise ValueError("未找到闭合的 JSON 数组")


def fetch(cfg: dict) -> dict:
    html = net.get_text(PAGE, headers=UA_BROWSER)
    blob = _flight_blob(html)
    m = re.search(r'"rawData":', blob)
    if not m:
        raise schema.SchemaError("flight 载荷中找不到 rawData（页面结构可能已改版）")
    raw = json.loads(_balanced_array(blob, blob.index("[", m.end())))

    days = []
    for row in raw:
        if row.get("metric") not in KEEP_METRICS:
            continue
        shares = [[name, round(pct, 4)] for name, pct in row["chef_values"][:TOP_N]]
        others = round(sum(pct for _, pct in row["chef_values"][TOP_N:]), 4)
        days.append(
            {
                "day": row["day"][:10],
                "metric": row["metric"],
                "shares": shares,
                "others_share": others,
            }
        )
    days.sort(key=lambda r: (r["day"], r["metric"]))
    return {"series": days, "note": "share_percent（份额%），非绝对量"}


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["series"])
    schema.require_nonempty_list(payload["series"], "series")
    days = {r["day"] for r in payload["series"]}
    metrics = {r["metric"] for r in payload["series"]}
    if len(days) < 30:
        raise schema.SchemaError(f"series 仅覆盖 {len(days)} 天，疑似截断")
    if "tokens" not in metrics:
        raise schema.SchemaError(f"缺 tokens 指标，实际 {metrics}")
    sample = payload["series"][-1]["shares"]
    for name, pct in sample[:5]:
        if not (0 <= pct <= 100):
            raise schema.SchemaError(f"份额越界: {name}={pct}")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
