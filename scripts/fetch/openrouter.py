"""OpenRouter 模型 token 用量与榜单（非官方 frontend API，高风险源）。

三个端点：model-rankings-chart（52 周主图）、models（每模型滚动 7 天）、
apps（Top Apps）。口径与坑见 docs/sources/openrouter.md 与 ADR-002。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "openrouter"
BASE = "https://openrouter.ai/api/frontend/v1/rankings"
UA_BROWSER = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def fetch(cfg: dict) -> dict:
    chart = net.get_json(f"{BASE}/model-rankings-chart", headers=UA_BROWSER)
    models = net.get_json(f"{BASE}/models", headers=UA_BROWSER)
    apps = net.get_json(f"{BASE}/apps", headers=UA_BROWSER)

    weekly_chart = chart["data"]["data"]  # [{x: 周一日期, ys: {slug: tokens, Others}}]

    models_week = [
        {
            "date": r["date"][:10],
            "permaslug": r["model_permaslug"],
            "variant": r.get("variant", "standard"),
            "prompt_tokens": r["total_prompt_tokens"],
            "completion_tokens": r["total_completion_tokens"],
            "reasoning_tokens": r.get("total_native_tokens_reasoning", 0),
            "requests": r.get("count", 0),
            "change": r.get("change"),
        }
        for r in models["data"]
    ]

    top_apps = {}
    for window in ("day", "week"):
        top_apps[window] = [
            {
                "title": (a.get("app") or {}).get("title") or "unknown",
                "total_tokens": int(a["total_tokens"]),
                "rank": a.get("rank"),
            }
            for a in apps["data"].get(window, [])[:20]
        ]

    return {"weekly_chart": weekly_chart, "models_week": models_week, "top_apps": top_apps}


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["weekly_chart", "models_week", "top_apps"])
    schema.require_nonempty_list(payload["weekly_chart"], "weekly_chart")
    if len(payload["weekly_chart"]) < 40:
        raise schema.SchemaError(f"weekly_chart 仅 {len(payload['weekly_chart'])} 周，疑似截断")
    last = payload["weekly_chart"][-1]
    schema.require_keys(last, ["x", "ys"], "weekly_chart[-1]")
    schema.require_positive_number(sum(last["ys"].values()), "weekly_chart[-1] 周 token 总量")
    if len(payload["models_week"]) < 100:
        raise schema.SchemaError(f"models_week 仅 {len(payload['models_week'])} 行，疑似截断")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
