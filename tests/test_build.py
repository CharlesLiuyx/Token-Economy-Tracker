from scripts import build


def test_short_model_name():
    assert build.short_model_name("anthropic/claude-4.7-opus-20260416") == "claude-4.7-opus"
    assert build.short_model_name("openai/gpt-oss-120b") == "gpt-oss-120b"
    assert build.short_model_name("mistral/mistral-large") == "mistral-large"


def test_cumulative_series_cuts_future_and_accumulates():
    timelines = [
        {"site": "a", "date": "2025-01-10", "power_mw": 100, "h100_equivalents": 1e5},
        {"site": "b", "date": "2025-02-05", "power_mw": 200, "h100_equivalents": 2e5},
        {"site": "a", "date": "2025-02-20", "power_mw": 300, "h100_equivalents": 3e5},
        {"site": "a", "date": "2099-01-01", "power_mw": 9999, "h100_equivalents": 9e9},
    ]
    s = build.cumulative_series(timelines, as_of="2025-12-31")
    assert s["labels"] == ["2025-01", "2025-02"]
    assert s["power_gw"] == [0.1, 0.5]          # a=300 覆盖旧值 + b=200
    assert s["h100_m"][-1] == 0.5


def test_cumulative_series_keeps_last_value_on_zero():
    timelines = [
        {"site": "a", "date": "2025-01-10", "power_mw": 100, "h100_equivalents": 1e5},
        {"site": "a", "date": "2025-03-01", "power_mw": None, "h100_equivalents": None},
    ]
    s = build.cumulative_series(timelines, as_of="2025-12-31")
    assert s["power_gw"][-1] == 0.1  # None 不清零，沿用上一次已知值


def test_series_delta_uses_nearest_prior_snapshot():
    series = {"2026-01-01": 100.0, "2026-01-07": 110.0, "2026-01-08": 121.0}
    assert round(build.series_delta(series, 1), 4) == 0.1
    assert round(build.series_delta(series, 7), 4) == 0.21
    assert build.series_delta(series, 30) is None            # 30 天前无可比快照
    assert build.series_delta({}, 7) is None


def test_fmt_delta_and_class():
    assert build.fmt_delta(0.0321) == "+3.2%"
    assert build.fmt_delta(-1.44, "pp") == "−1.4pp"
    assert build.fmt_delta(None) == "—"
    assert build.delta_class(None) == "flat"
    assert build.delta_class(-0.2) == "down"


def test_vendor_colors_are_consistent_across_naming_styles():
    assert build.vendor_of("anthropic/claude-opus-5-20260723")[0] == "anthropic"
    assert build.vendor_of("Claude Sonnet 5") == build.vendor_of("anthropic/claude-sonnet-5")
    assert build.vendor_of("GPT-5.6 Luna")[0] == "openai"
    assert build.vendor_of("some-unknown-model") == (None, build.NEUTRAL)
    styles = build.vendor_line_styles(["claude-a", "claude-b", "gpt-x"])
    assert styles[0]["borderColor"] == styles[1]["borderColor"] != styles[2]["borderColor"]
    assert "borderDash" not in styles[0] and "borderDash" in styles[1]   # 同厂商靠线型区分


def test_gpu_meta_accepts_legacy_string_and_dict():
    meta = build._gpu_meta({"gpus": {"H100": "H100 SXM",
                                     "B300": {"name": "B300", "vram_gb": 270, "tier": "frontier"}}})
    assert meta["H100"] == {"name": "H100 SXM"}
    assert meta["B300"]["vram_gb"] == 270
