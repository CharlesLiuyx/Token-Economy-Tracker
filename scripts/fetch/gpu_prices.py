"""GPU 租赁价格：Vast.ai 公开市场 API（官方、免鉴权），每卡型报价分布。

口径：Vast.ai 市场 on-demand 报价的分位数（$/GPU-hr），是全市场的低价切片，
不等于超算云牌价。源选型见 ADR-004；字段与坑见 docs/sources/gpu_prices.md。
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "gpu_prices"
API = "https://console.vast.ai/api/v0/bundles/"


def _quantiles(values: list[float]) -> dict:
    values = sorted(values)
    q = statistics.quantiles(values, n=4) if len(values) >= 4 else [values[0], statistics.median(values), values[-1]]
    return {
        "min": round(values[0], 3),
        "p25": round(q[0], 3),
        "median": round(statistics.median(values), 3),
        "p75": round(q[-1], 3),
        "max": round(values[-1], 3),
        "offers": len(values),
    }


def fetch(cfg: dict) -> dict:
    gpus = {}
    for label, gpu_name in cfg["gpus"].items():
        query = {
            "gpu_name": {"eq": gpu_name},
            "rentable": {"eq": True},
            "external": {"eq": False},
            "type": "on-demand",
        }
        data = net.get_json(API, params={"q": json.dumps(query)})
        per_gpu = [
            o["dph_total"] / max(o.get("num_gpus") or 1, 1)
            for o in data.get("offers", [])
            if o.get("dph_total")
        ]
        gpus[label] = _quantiles(per_gpu) if per_gpu else {"offers": 0}
    return {"unit": "usd_per_gpu_hour", "marketplace": "vast.ai on-demand", "gpus": gpus}


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["gpus"])
    if not payload["gpus"]:
        raise schema.SchemaError("gpus 为空")
    ok = 0
    for label, q in payload["gpus"].items():
        if q.get("offers", 0) >= 3:
            if not (0.05 <= q["median"] <= 50):
                raise schema.SchemaError(f"{label}: median={q['median']} 超出合理区间")
            ok += 1
    if ok < 3:
        raise schema.SchemaError(f"仅 {ok} 个卡型有足量报价（≥3），疑似 API 异常")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
