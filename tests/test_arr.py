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


def synth_exponential(k_per_day=0.01, n=8, v0=1e9, start=dt.date(2025, 1, 1)):
    return [
        _mk((start + dt.timedelta(days=60 * i)).isoformat(), round(v0 * math.exp(k_per_day * 60 * i)))
        for i in range(n)
    ]


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
