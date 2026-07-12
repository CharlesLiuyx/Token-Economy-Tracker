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
