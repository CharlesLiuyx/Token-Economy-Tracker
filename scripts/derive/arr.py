"""ARR 锚点拟合 → 曲线 + 置信带 + 实时外推参数。输出 data/derived/arr.json。

方法（docs/arr-methodology.md）：每家公司取 run_rate_arr 锚点，对数空间加权
最小二乘（近期锚点权重高，半衰期 HALF_LIFE_DAYS），得指数增长率 k；加权残差
标准差给置信带。projected_rev / reported_rev 仅作展示散点，不入拟合。
"""

from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import yaml

from scripts.lib import status, store
from scripts.lib.schema import SchemaError

SOURCE = "arr"
ANCHORS_PATH = store.DATA / "manual" / "arr_anchors.yml"
OUT_PATH = store.DATA / "derived" / "arr.json"

VALID_METRICS = {"run_rate_arr", "projected_rev", "reported_rev"}
HALF_LIFE_DAYS = 120        # 锚点权重半衰期
MIN_FIT_ANCHORS = 3
EXTRAPOLATE_DAYS = 180      # 外推窗口（页面虚线区）
SANE_MOM_RANGE = (-0.5, 1.0)  # implied MoM 合理区间（-50% ~ +100%/月）


def _days(date_str: str, epoch: dt.date) -> float:
    return (dt.date.fromisoformat(date_str) - epoch).days


def load_anchors(path: Path = ANCHORS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    anchors = data.get("anchors") or []
    for a in anchors:
        for key in ("company", "date", "value_usd", "metric", "source_url"):
            if not a.get(key):
                raise SchemaError(f"锚点缺字段 {key}: {a}")
        if a["metric"] not in VALID_METRICS:
            raise SchemaError(f"非法口径 metric={a['metric']!r}（允许 {sorted(VALID_METRICS)}）")
        if a["value_usd"] <= 0:
            raise SchemaError(f"value_usd 必须为正: {a}")
        dt.date.fromisoformat(str(a["date"]))  # 日期格式即刻校验
    return anchors


def fit_company(anchors: list[dict], today: dt.date) -> dict:
    """对单公司 run_rate_arr 锚点做对数空间加权最小二乘。"""
    fit_pts = sorted(
        (a for a in anchors if a["metric"] == "run_rate_arr"), key=lambda a: a["date"]
    )
    if len(fit_pts) < MIN_FIT_ANCHORS:
        raise SchemaError(f"run_rate_arr 锚点不足 {MIN_FIT_ANCHORS} 个（{len(fit_pts)}）")

    epoch = dt.date.fromisoformat(str(fit_pts[0]["date"]))
    last_anchor_date = dt.date.fromisoformat(str(fit_pts[-1]["date"]))
    t = np.array([_days(str(a["date"]), epoch) for a in fit_pts])
    y = np.log([a["value_usd"] for a in fit_pts])
    age = (last_anchor_date - epoch).days - t
    w = np.power(0.5, age / HALF_LIFE_DAYS)

    # 加权最小二乘：y ≈ lnA + k·t
    W = np.diag(w)
    X = np.vstack([np.ones_like(t), t]).T
    beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
    ln_a, k = float(beta[0]), float(beta[1])

    resid = y - (ln_a + k * t)
    sigma = float(np.sqrt(np.sum(w * resid**2) / np.sum(w)))

    mom = math.exp(k * 30.44) - 1
    if not (SANE_MOM_RANGE[0] <= mom <= SANE_MOM_RANGE[1]):
        raise SchemaError(f"implied MoM {mom:.1%} 超出合理区间 {SANE_MOM_RANGE}，检查锚点")

    def arr_at(day: dt.date) -> float:
        return math.exp(ln_a + k * _days(day.isoformat(), epoch))

    # 周频序列：首锚点 → 今日 + 外推窗口；置信带 ×/÷ exp(1.96σ)
    band = math.exp(1.96 * sigma)
    series = []
    day = epoch
    end = today + dt.timedelta(days=EXTRAPOLATE_DAYS)
    while day <= end:
        v = arr_at(day)
        series.append(
            {
                "date": day.isoformat(),
                "fitted": round(v),
                "lo": round(v / band),
                "hi": round(v * band),
                "extrapolated": day > last_anchor_date,
            }
        )
        day += dt.timedelta(days=7)

    arr_now = arr_at(today)
    return {
        "fit": {
            "k_per_day": k,
            "mom_implied": round(mom, 4),
            "sigma_log": round(sigma, 4),
            "n_anchors": len(fit_pts),
            "epoch": epoch.isoformat(),
            "last_anchor_date": last_anchor_date.isoformat(),
            "last_anchor_value": fit_pts[-1]["value_usd"],
        },
        "realtime": {
            "arr_at_build": round(arr_now),
            "usd_per_hour": round(arr_now * (math.exp(k / 24) - 1)),
            "mom_implied": round(mom, 4),
        },
        "anchors": [
            {**{key: a[key] for key in ("date", "value_usd", "metric", "source_url")},
             "note": a.get("note", "")}
            for a in sorted(anchors, key=lambda a: str(a["date"]))
        ],
        "series": series,
    }


def main() -> int:
    today = store.utc_now().date()
    try:
        anchors = load_anchors()
        companies = sorted({a["company"] for a in anchors})
        out = {
            "generated_at": store.utc_now().isoformat(timespec="seconds"),
            "build_date": today.isoformat(),
            "half_life_days": HALF_LIFE_DAYS,
            "companies": {
                c: fit_company([a for a in anchors if a["company"] == c], today)
                for c in companies
            },
        }
    except Exception as exc:  # noqa: BLE001
        status.record(SOURCE, ok=False, error=f"{type(exc).__name__}: {exc}")
        print(f"[{SOURCE}] FAILED: {exc}", file=sys.stderr)
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    status.record(SOURCE, ok=True)
    for c, d in out["companies"].items():
        rt = d["realtime"]
        print(
            f"[{SOURCE}] {c}: ARR≈${rt['arr_at_build']/1e9:.1f}B "
            f"(+${rt['usd_per_hour']:,}/hr, MoM {rt['mom_implied']:+.1%})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
