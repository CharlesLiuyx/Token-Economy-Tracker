import datetime as dt
import math

import pytest

from scripts.derive import arr
from scripts.lib.schema import SchemaError


def _mk(date, value, metric="run_rate_arr", company="acme"):
    return {
        "company": company,
        "date": date,
        "value_usd": value,
        "metric": metric,
        "source_url": "https://example.com",
    }


def _synth(shape_fn, n=8, step=60, start=dt.date(2025, 1, 1)):
    return [
        _mk((start + dt.timedelta(days=step * i)).isoformat(), round(shape_fn(step * i)))
        for i in range(n)
    ]


def synth_exponential(k_per_day=0.01, n=8, v0=1e9, start=dt.date(2025, 1, 1)):
    return _synth(lambda d: v0 * math.exp(k_per_day * d), n=n, start=start)


def test_fit_recovers_growth_rate():
    anchors = synth_exponential(k_per_day=0.01)
    out = arr.fit_company(anchors, today=dt.date(2026, 7, 1))
    assert out["fit"]["k_per_day"] == pytest.approx(0.01, rel=0.02)
    assert out["fit"]["mom_implied"] == pytest.approx(math.exp(0.01 * 30.44) - 1, rel=0.05)
    assert out["fit"]["sigma_log"] < 0.01  # 无噪声 → 残差近零


def test_fitted_curve_passes_anchors():
    anchors = synth_exponential()
    out = arr.fit_company(anchors, today=dt.date(2026, 7, 1))
    by_date = {p["date"]: p for p in out["series"]}
    last = anchors[-1]
    # 周频序列未必正好落在锚点日，取拟合函数口径：容差 10%
    near = min(by_date.values(), key=lambda p: abs(dt.date.fromisoformat(p["date"]) - dt.date.fromisoformat(last["date"])))
    assert near["fitted"] == pytest.approx(last["value_usd"], rel=0.1)


def test_extrapolation_marked():
    anchors = synth_exponential()
    out = arr.fit_company(anchors, today=dt.date(2026, 7, 1))
    flags = [p["extrapolated"] for p in out["series"]]
    assert flags[0] is False and flags[-1] is True


def test_non_run_rate_metrics_excluded_from_fit():
    anchors = synth_exponential()
    # 加一个离谱的 projected_rev，不应影响拟合
    polluted = anchors + [_mk("2025-06-01", 10**13, metric="projected_rev")]
    a = arr.fit_company(anchors, today=dt.date(2026, 7, 1))
    b = arr.fit_company(polluted, today=dt.date(2026, 7, 1))
    assert a["fit"]["k_per_day"] == pytest.approx(b["fit"]["k_per_day"])
    assert b["fit"]["n_anchors"] == len(anchors)


def test_insufficient_anchors_rejected():
    with pytest.raises(SchemaError, match="不足"):
        arr.fit_company(synth_exponential(n=2), today=dt.date(2026, 7, 1))


def test_absurd_growth_rejected():
    crazy = [_mk("2025-01-01", 1_000_000), _mk("2025-01-10", 5_000_000), _mk("2025-01-20", 40_000_000)]
    with pytest.raises(SchemaError, match="MoM"):
        arr.fit_company(crazy, today=dt.date(2025, 2, 1))


# ---- 形态选择：曲线家族由数据决定，不预设 ----

def test_exponential_data_picks_exponential():
    """指数数据不该被更花哨的形态抢走（回测相当时取参数少的）。"""
    out = arr.fit_company(synth_exponential(k_per_day=0.008), today=dt.date(2026, 7, 1))
    assert out["fit"]["model"] == "exponential"


def test_linear_data_picks_linear():
    """恒定绝对增量（$/天不变）→ linear 胜出，不该报出个假的月复合增速。"""
    anchors = _synth(lambda d: 1e9 + 5e6 * d, n=10)
    out = arr.fit_company(anchors, today=dt.date(2027, 1, 1))
    assert out["fit"]["model"] == "linear"
    assert out["fit"]["sigma_log"] < 0.01
    # 直线的瞬时增速随时间稀释，末端 MoM 远低于早期
    assert out["fit"]["mom_implied"] < 0.1


def test_accelerating_data_picks_log_quadratic():
    """增速本身在漂移（log 空间弯曲）→ log_quadratic 胜出。"""
    anchors = _synth(lambda d: 1e9 * math.exp(0.002 * d + 8e-6 * d**2), n=12, step=45)
    out = arr.fit_company(anchors, today=dt.date(2026, 9, 1))
    assert out["fit"]["model"] == "log_quadratic"


def test_curved_fit_tracks_last_anchor():
    """回归护栏：形态选对后，拟合值应贴住最近的锚点（旧的全局指数会系统性落后）。"""
    anchors = _synth(lambda d: 1e9 * math.exp(0.002 * d + 8e-6 * d**2), n=12, step=45)
    out = arr.fit_company(anchors, today=dt.date(2026, 9, 1))
    fit = out["fit"]
    assert fit["fitted_at_last_anchor"] == pytest.approx(fit["last_anchor_value"], rel=0.03)


def test_candidates_reported_with_selection():
    out = arr.fit_company(synth_exponential(), today=dt.date(2026, 7, 1))
    cands = out["fit"]["candidates"]
    assert {c["model"] for c in cands} == set(arr.MODELS)
    assert sum(1 for c in cands if c.get("selected")) == 1


def test_too_few_anchors_falls_back_to_simplest():
    """锚点刚够拟合、排不出回测折时，不允许 3 参数曲线吃满 3 个点去外推。"""
    anchors = synth_exponential(n=3)
    out = arr.fit_company(anchors, today=dt.date(2025, 8, 1))
    assert out["fit"]["candidates"][0]["backtest_rmse_log"] is None
    assert out["fit"]["model"] in {"linear", "exponential"}


# ---- 外推与置信带 ----

def test_extrapolation_freezes_growth_rate():
    """外推区用最后锚点处的瞬时增速直线延伸，曲率不外推（否则 t² 项 180 天必失真）。"""
    anchors = _synth(lambda d: 1e9 * math.exp(0.002 * d + 8e-6 * d**2), n=12, step=45)
    out = arr.fit_company(anchors, today=dt.date(2026, 9, 1))
    assert out["fit"]["model"] == "log_quadratic"
    tail = [p for p in out["series"] if p["extrapolated"]]
    steps = [math.log(b["fitted"] / a["fitted"]) for a, b in zip(tail, tail[1:])]
    assert max(steps) - min(steps) < 1e-6  # log 空间等步长 = 直线


def test_band_widens_with_horizon():
    """置信带在外推区必须张开——恒定宽度是在撒谎。"""
    anchors = synth_exponential(k_per_day=0.008)
    # 加一点噪声，否则 sigma≈0 带宽退化
    anchors[3]["value_usd"] = round(anchors[3]["value_usd"] * 1.15)
    out = arr.fit_company(anchors, today=dt.date(2026, 7, 1))
    width = [(p["hi"] / p["fitted"], p["extrapolated"]) for p in out["series"]]
    at_last_anchor = [w for w, ext in width if not ext][-1]
    tail = [w for w, ext in width if ext]
    assert tail == sorted(tail)                    # 越往外越宽，单调
    assert tail[-1] > at_last_anchor * 1.05


def test_unsupported_head_trimmed_not_drawn():
    """近期加权 + 曲率，往回推几年参数不确定性会炸开；那段只留散点，不画线。"""
    old = [_mk("2022-01-01", 1e8), _mk("2022-06-01", 1.1e8)]
    anchors = old + _synth(lambda d: 1e9 * math.exp(0.002 * d + 8e-6 * d**2), n=12, step=45)
    out = arr.fit_company(anchors, today=dt.date(2026, 9, 1))
    first = out["series"][0]
    assert first["date"] > "2022-06-01"                    # 早期空窗没画线
    assert first["hi"] / first["fitted"] <= arr.MAX_BAND_RATIO * 1.01
    # 锚点散点仍然全量保留，历史不丢
    assert len(out["anchors"]) == len(anchors)


def test_stable_exponential_keeps_full_history():
    """形态稳定时不该被裁——整段历史都该画出来。"""
    anchors = synth_exponential(k_per_day=0.008, n=10)
    out = arr.fit_company(anchors, today=dt.date(2027, 1, 1))
    assert out["series"][0]["date"] == anchors[0]["date"]


def test_load_anchors_validates(tmp_path):
    bad = tmp_path / "a.yml"
    bad.write_text(
        "anchors:\n- company: x\n  date: '2025-01-01'\n  value_usd: 1\n"
        "  metric: guessed_rev\n  source_url: https://e.com\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemaError, match="非法口径"):
        arr.load_anchors(bad)


def test_real_anchors_file_loads():
    anchors = arr.load_anchors()
    companies = {a["company"] for a in anchors}
    assert {"anthropic", "openai"} <= companies
