"""ARR 锚点拟合 → 曲线 + 置信带 + 实时外推参数。输出 data/derived/arr.json。

方法（docs/arr-methodology.md）：每家公司取 run_rate_arr 锚点，在 log 空间用加权
最小二乘拟合若干**候选形态**（linear / exponential / log_quadratic，近期锚点权重高，
半衰期 HALF_LIFE_DAYS），再用**滚动起点回测**（用前 i 个锚点拟合、预测第 i+1 个）
挑出预测最准的那个——形态由数据决定，不预设。最后锚点之后用该处的瞬时增速直线
延伸（不外推曲率）；置信带取预测区间，随外推距离自然张开。
projected_rev / reported_rev 仅作展示散点，不入拟合。
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
HALF_LIFE_DAYS = 120.0      # 锚点权重半衰期
MIN_FIT_ANCHORS = 3
EXTRAPOLATE_DAYS = 180      # 外推窗口（页面虚线区）
SANE_MOM_RANGE = (-0.5, 1.0)  # implied MoM 合理区间（-50% ~ +100%/月）
MAX_BAND_RATIO = 3.0        # 置信带宽于此倍数即不再画（见 _trim_unsupported）
YEAR_DAYS = 365.25          # t 以「年」为单位进设计矩阵，避免病态
DAYS_PER_MONTH = 30.44
Z95 = 1.96


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


def _weights(t: np.ndarray) -> np.ndarray:
    """近期权重高：以最后一个锚点为基准，按半衰期指数衰减。"""
    return np.power(0.5, (t[-1] - t) / HALF_LIFE_DAYS)


class Curve:
    """log 空间的一条拟合曲线。

    锚点区间内按模型本身取值；最后锚点之后**冻结增速**——用该处的瞬时对数增速做
    直线延伸，不把曲率外推出去（曲率由少数点估得，t² 放大误差，180 天外必然失真）。
    """

    def __init__(self, name: str, n_params: int, log_fn, rate_fn, jac_fn,
                 t: np.ndarray, ly: np.ndarray, w: np.ndarray):
        self.name = name
        self.n_params = n_params
        self._log_fn = log_fn          # t(天) -> ln y
        self._rate_fn = rate_fn        # t(天) -> d ln y / d 天
        self.t_last = float(t[-1])

        resid = ly - log_fn(t)
        sse = float(np.sum(w * resid**2))
        sw = float(np.sum(w))
        # Kish 有效样本量：加权后真正"顶事"的点数，用于残差自由度修正
        n_eff = sw**2 / float(np.sum(w**2))
        self.n_eff = n_eff
        dof = max(n_eff - n_params, 1.0)
        self.sigma = math.sqrt(sse / sw * n_eff / dof) if sw > 0 else 0.0

        # 参数协方差（用于预测区间随外推距离张开）
        jac = jac_fn(t)
        self._jac_fn = jac_fn
        self._cov = self.sigma**2 * np.linalg.pinv(jac.T @ (w[:, None] * jac))

    def log_at(self, t) -> np.ndarray:
        t = np.atleast_1d(np.asarray(t, dtype=float))
        inside = np.minimum(t, self.t_last)
        horizon = np.maximum(t - self.t_last, 0.0)
        return self._log_fn(inside) + horizon * self.rate_at(self.t_last)

    def rate_at(self, t: float) -> float:
        """瞬时对数增速（/天）。外推区沿用最后锚点处的值。"""
        return float(self._rate_fn(np.array([min(float(t), self.t_last)]))[0])

    def mom_at(self, t: float) -> float:
        return math.exp(self.rate_at(t) * DAYS_PER_MONTH) - 1

    def log_sd_at(self, t) -> np.ndarray:
        """预测标准差：观测噪声 + 参数不确定性（外推区含增速本身的不确定性）。"""
        t = np.atleast_1d(np.asarray(t, dtype=float))
        inside = np.minimum(t, self.t_last)
        horizon = np.maximum(t - self.t_last, 0.0)
        # 外推点 = 最后锚点处的值 + h·增速，两者都是参数的（局部）线性泛函
        g = self._jac_fn(inside)
        tail = self._jac_fn(np.array([self.t_last]))
        d_tail = (self._jac_fn(np.array([self.t_last + 0.5]))
                  - self._jac_fn(np.array([self.t_last - 0.5])))
        g = np.where(horizon[:, None] > 0, tail + horizon[:, None] * d_tail, g)
        var = np.einsum("ij,jk,ik->i", g, self._cov, g)
        return np.sqrt(np.maximum(self.sigma**2 + var, 0.0))


def _fit_poly(name: str, deg: int, t: np.ndarray, ly: np.ndarray, w: np.ndarray) -> Curve:
    """ln y = β₀ + β₁·t + … + β_deg·t^deg（deg=1 即恒定增速的指数增长）。"""
    def design(tt: np.ndarray) -> np.ndarray:
        return np.vander(np.asarray(tt, dtype=float) / YEAR_DAYS, deg + 1, increasing=True)

    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(design(t) * sw[:, None], ly * sw, rcond=None)

    def rate(tt: np.ndarray) -> np.ndarray:
        ty = np.asarray(tt, dtype=float) / YEAR_DAYS
        return sum(j * beta[j] * ty ** (j - 1) for j in range(1, deg + 1)) / YEAR_DAYS

    return Curve(name, deg + 1, lambda tt: design(tt) @ beta, rate, design, t, ly, w)


def _fit_linear(name: str, t: np.ndarray, ly: np.ndarray, w: np.ndarray) -> Curve:
    """y = b·(t − t₀)：恒定**绝对**增量的直线（b>0，写成过 x 轴 t₀ 的形式保证 y>0）。

    给定 t₀ 时 ln b 有闭式解（log 空间加权均值），故只需对 t₀ 做一维搜索。
    """
    lo, hi = t[0] - 10 * YEAR_DAYS, t[0] - 1.0
    best = None
    for _ in range(4):  # 由粗到细四轮
        for t0 in np.linspace(lo, hi, 64):
            x = np.log(t - t0)
            ln_b = float(np.sum(w * (ly - x)) / np.sum(w))
            sse = float(np.sum(w * (ly - x - ln_b) ** 2))
            if best is None or sse < best[0]:
                best = (sse, float(t0), ln_b)
        step = (hi - lo) / 32
        lo, hi = max(best[1] - step, t[0] - 40 * YEAR_DAYS), min(best[1] + step, t[0] - 1.0)
    _, t0, ln_b = best

    # 参数 (ln b, t₀) 下的雅可比：∂ln y/∂ln b = 1，∂ln y/∂t₀ = −1/(t−t₀)
    def jac(tt: np.ndarray) -> np.ndarray:
        d = np.maximum(np.asarray(tt, dtype=float) - t0, 1e-6)
        return np.vstack([np.ones_like(d), -1.0 / d]).T

    return Curve(
        name, 2,
        lambda tt: ln_b + np.log(np.maximum(np.asarray(tt, dtype=float) - t0, 1e-6)),
        lambda tt: 1.0 / np.maximum(np.asarray(tt, dtype=float) - t0, 1e-6),
        jac, t, ly, w,
    )


# 候选形态：名字 -> 拟合函数。每个都是「增速怎么随时间走」的一种假设。
#   linear         恒定绝对增量（$/天不变）
#   exponential    恒定相对增速（MoM 不变）
#   log_quadratic  相对增速线性漂移（在加速 / 在减速）
MODELS = {
    "linear": lambda t, ly, w: _fit_linear("linear", t, ly, w),
    "exponential": lambda t, ly, w: _fit_poly("exponential", 1, t, ly, w),
    "log_quadratic": lambda t, ly, w: _fit_poly("log_quadratic", 2, t, ly, w),
}


def backtest(name: str, t: np.ndarray, ly: np.ndarray, w: np.ndarray) -> float | None:
    """滚动起点回测：用前 i 个锚点拟合、预测第 i+1 个，返回加权 RMSE（log 空间）。

    折按目标锚点的近期权重加权——久远年份预测得准不准，不该左右今天用哪个形态。
    锚点刚够拟合、一折都排不出时返回 None（交由 select_model 退化成「取最简形态」）。
    """
    num = den = 0.0
    for i in range(MIN_FIT_ANCHORS, len(t)):
        try:
            curve = MODELS[name](t[:i], ly[:i], _weights(t[:i]))
            pred = float(curve.log_at(t[i])[0])
        except (np.linalg.LinAlgError, ValueError, FloatingPointError):
            return math.inf
        if not math.isfinite(pred):
            return math.inf
        num += w[i] * (ly[i] - pred) ** 2
        den += w[i]
    return math.sqrt(num / den) if den > 0 else None


def select_model(t: np.ndarray, ly: np.ndarray, w: np.ndarray) -> tuple[Curve, list[dict]]:
    """按回测误差选形态；implied MoM 离谱的候选直接出局，同分取参数少的。

    锚点少到排不出回测折时，数据本就分不出形态，退化为「取参数最少的」——
    宁可欠拟合，也不让 3 个点喂出一条 3 参数的完美曲线去外推。
    """
    report, ranked = [], []
    for name in MODELS:
        row: dict = {"model": name}
        try:
            curve = MODELS[name](t, ly, w)
        except (np.linalg.LinAlgError, ValueError) as exc:
            report.append({**row, "rejected": f"拟合失败: {exc}"})
            continue
        mom = curve.mom_at(t[-1])
        rmse = backtest(name, t, ly, w)
        row |= {
            "n_params": curve.n_params,
            "backtest_rmse_log": None if rmse is None else round(rmse, 4),
            "sigma_log": round(curve.sigma, 4),
            "mom_implied": round(mom, 4),
        }
        if not (SANE_MOM_RANGE[0] <= mom <= SANE_MOM_RANGE[1]):
            report.append({**row, "rejected": f"implied MoM {mom:.1%} 超出 {SANE_MOM_RANGE}"})
            continue
        if rmse is not None and not math.isfinite(rmse):
            report.append({**row, "rejected": "回测发散"})
            continue
        # 有折：回测误差优先；无折：参数少者优先
        key = (rmse, curve.n_params) if rmse is not None else (curve.n_params, curve.sigma)
        ranked.append((key, name, curve))
        report.append(row)

    if not ranked:
        raise SchemaError(
            "无可用形态：所有候选的 implied MoM 都超出合理区间或回测发散，检查锚点"
            f"（{[r.get('rejected') for r in report]}）"
        )
    ranked.sort(key=lambda r: r[0])
    winner = ranked[0][2]
    for row in report:
        row["selected"] = row["model"] == winner.name
    return winner, report


def _trim_unsupported(half: np.ndarray, grid: np.ndarray, t_last: float) -> int:
    """曲线从哪一格开始画：截掉早期「置信带已经宽到没意义」的一段，返回起始下标。

    近期加权 + 带曲率的形态，往回推到几年前时参数不确定性会炸开（带宽 ×10 起）。
    那段曲线不是估算，是噪声——只留锚点散点，别画一条假装知道的线。
    """
    ok = half <= math.log(MAX_BAND_RATIO)
    ok &= grid <= t_last                       # 外推区不参与判定，只裁前段
    if not ok.any():
        return 0                               # 全程都宽 → 不裁，交由页面注记自证
    return int(np.argmax(ok))


def fit_company(anchors: list[dict], today: dt.date) -> dict:
    """对单公司 run_rate_arr 锚点做形态选择 + 加权最小二乘拟合。"""
    fit_pts = sorted(
        (a for a in anchors if a["metric"] == "run_rate_arr"), key=lambda a: str(a["date"])
    )
    if len(fit_pts) < MIN_FIT_ANCHORS:
        raise SchemaError(f"run_rate_arr 锚点不足 {MIN_FIT_ANCHORS} 个（{len(fit_pts)}）")

    epoch = dt.date.fromisoformat(str(fit_pts[0]["date"]))
    last_anchor_date = dt.date.fromisoformat(str(fit_pts[-1]["date"]))
    t = np.array([_days(str(a["date"]), epoch) for a in fit_pts], dtype=float)
    ly = np.log([float(a["value_usd"]) for a in fit_pts])
    w = _weights(t)

    curve, candidates = select_model(t, ly, w)

    # 周频序列：首锚点 → 今日 + 外推窗口；置信带为 95% 预测区间（外推区自然张开）
    days = []
    day = epoch
    end = today + dt.timedelta(days=EXTRAPOLATE_DAYS)
    while day <= end:
        days.append(day)
        day += dt.timedelta(days=7)
    grid = np.array([(d - epoch).days for d in days], dtype=float)
    log_fit = curve.log_at(grid)
    half = Z95 * curve.log_sd_at(grid)
    start = _trim_unsupported(half, grid, curve.t_last)
    days, log_fit, half = days[start:], log_fit[start:], half[start:]
    series = [
        {
            "date": d.isoformat(),
            "fitted": round(math.exp(lf)),
            "lo": round(math.exp(lf - h)),
            "hi": round(math.exp(lf + h)),
            "extrapolated": d > last_anchor_date,
        }
        for d, lf, h in zip(days, log_fit, half)
    ]

    t_now = _days(today.isoformat(), epoch)
    arr_now = math.exp(float(curve.log_at(t_now)[0]))
    k_now = curve.rate_at(t_now)
    mom = curve.mom_at(t_now)
    return {
        "fit": {
            "model": curve.name,
            "k_per_day": k_now,
            "mom_implied": round(mom, 4),
            "sigma_log": round(curve.sigma, 4),
            "n_anchors": len(fit_pts),
            "n_eff_anchors": round(curve.n_eff, 2),
            "epoch": epoch.isoformat(),
            "last_anchor_date": last_anchor_date.isoformat(),
            "last_anchor_value": fit_pts[-1]["value_usd"],
            "fitted_at_last_anchor": round(math.exp(float(curve.log_at(t[-1])[0]))),
            "candidates": candidates,
        },
        "realtime": {
            "arr_at_build": round(arr_now),
            "usd_per_hour": round(arr_now * (math.exp(k_now / 24) - 1)),
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
            "models": list(MODELS),
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
        rt, fit = d["realtime"], d["fit"]
        print(
            f"[{SOURCE}] {c}: {fit['model']} → ARR≈${rt['arr_at_build']/1e9:.1f}B "
            f"(+${rt['usd_per_hour']:,}/hr, MoM {rt['mom_implied']:+.1%}, "
            f"σ_log {fit['sigma_log']}) | 回测 "
            + ", ".join(
                f"{c_['model']}={c_.get('backtest_rmse_log', 'x')}"
                + ("*" if c_.get("selected") else "")
                for c_ in fit["candidates"]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
