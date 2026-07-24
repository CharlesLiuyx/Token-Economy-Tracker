"""data/ -> site/index.html（单文件、离线可开、无外部请求）。

每个面板 = 一个 spec_* 函数（产出图表 spec 或卡片/表格数据）+ 一个
site/template/panels/*.j2 片段。图表 spec 是 Chart.js 原生配置的子集
（line / bar / horizontalBar / scatter），由 app.js 的 renderPanel 统一渲染。

i18n：全部 UI 文案在 site/template/i18n.yml（key -> {zh, en}）。模板用 t(key)
渲染默认语言，spec 用 L(key) 生成 "__i18n:<key>" 占位符，app.js 运行期解析。
约定见 docs/frontend.md。
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from jinja2 import Environment, FileSystemLoader

from scripts.lib import registry, status, store

SITE = store.ROOT / "site"
TEMPLATE_DIR = SITE / "template"

FRESH_WARN_HOURS = 48
FRESH_RED_DAYS = 7

# 与 style.css 一致的系列色（Linear 风格中饱和，light/dark 双主题均可读；
# 0=Anthropic clay、1=OpenAI teal，与 CSS --c-clay/--c-teal 对应）
PALETTE = ["#D97757", "#10A37F", "#5E6AD2", "#EB5757", "#F2C94C",
           "#4EA7FC", "#9E8CFC", "#E56EB3", "#26B5CE", "#4CB782",
           "#95A2B3", "#B08968"]
# 占位符：渲染时由 app.js 按当前主题替换为面板底色（锚点描边/空心点填充）
SURFACE = "__surface"


# ---------- i18n ----------

I18N_PATH = TEMPLATE_DIR / "i18n.yml"
LANGS = ("zh", "en")
DEFAULT_LANG = "zh"


def load_i18n() -> dict:
    """site/template/i18n.yml：全部 UI 文案的唯一出处；缺语言/空文案直接失败。"""
    catalog = yaml.safe_load(I18N_PATH.read_text(encoding="utf-8")) or {}
    bad = [k for k, v in catalog.items()
           if not isinstance(v, dict) or set(v) != set(LANGS)
           or not all(isinstance(s, str) and s.strip() for s in v.values())]
    if bad:
        raise ValueError(f"i18n.yml 条目缺语言或为空: {bad}")
    return catalog


I18N = load_i18n()


def t(key: str, **args) -> str:
    """构建期渲染默认语言（zh）文案；{name} 占位参数与 app.js 同语义。"""
    s = I18N[key][DEFAULT_LANG]
    for k, v in args.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def L(key: str) -> str:
    """图表 spec 占位符 '__i18n:<key>'，app.js 渲染时按当前语言解析（同 __surface）。"""
    if key not in I18N:
        raise KeyError(f"i18n.yml 缺 key: {key}")
    return "__i18n:" + key


# ---------- 基础 ----------

def freshness(last_success: str | None) -> str:
    """ok / warn (>48h) / stale (>7d) / missing"""
    if not last_success:
        return "missing"
    age = store.utc_now() - dt.datetime.fromisoformat(last_success)
    if age > dt.timedelta(days=FRESH_RED_DAYS):
        return "stale"
    if age > dt.timedelta(hours=FRESH_WARN_HOURS):
        return "warn"
    return "ok"


def payload(source: str) -> dict:
    latest = store.read_latest(source) or {}
    return latest.get("payload") or {}


def daily_snapshots(source: str) -> list[dict]:
    """按日期升序读取一个源的全部 daily 快照（用于自累积的历史序列）。"""
    root = store.DATA / source / "daily"
    return [store.read_json(p) for p in sorted(root.rglob("*.json"))]


def short_model_name(permaslug: str) -> str:
    """anthropic/claude-4.7-opus-20260416 -> claude-4.7-opus"""
    name = permaslug.split("/", 1)[-1]
    return re.sub(r"-\d{8}$", "", name)


def color(i: int) -> str:
    return PALETTE[i % len(PALETTE)]


def _line_ds(label: str, data, i: int, **kw) -> dict:
    return {"label": label, "data": data, "borderColor": color(i),
            "backgroundColor": color(i), **kw}


# ---------- ① ARR ----------

def spec_arr(arr: dict) -> dict:
    """双公司：拟合实线 / 外推虚线 / 置信带 / 锚点散点，对数轴，x=天数。"""
    epoch0 = dt.date(2023, 1, 1)

    def day_num(date_str: str) -> int:
        return (dt.date.fromisoformat(date_str) - epoch0).days

    datasets = []
    cards = []
    for i, (company, d) in enumerate(sorted(arr.get("companies", {}).items())):
        c = color(i)
        solid = [{"x": day_num(p["date"]), "y": p["fitted"] / 1e9}
                 for p in d["series"] if not p["extrapolated"]]
        dashed = [{"x": day_num(p["date"]), "y": p["fitted"] / 1e9}
                  for p in d["series"] if p["extrapolated"]]
        if solid and dashed:
            dashed.insert(0, solid[-1])
        band_hi = [{"x": day_num(p["date"]), "y": p["hi"] / 1e9} for p in d["series"]]
        band_lo = [{"x": day_num(p["date"]), "y": p["lo"] / 1e9} for p in d["series"]]
        anchors = [{"x": day_num(str(a["date"])), "y": a["value_usd"] / 1e9}
                   for a in d["anchors"] if a["metric"] == "run_rate_arr"]
        reported = [{"x": day_num(str(a["date"])), "y": a["value_usd"] / 1e9}
                    for a in d["anchors"] if a["metric"] == "reported_rev"]
        datasets += [
            {"label": f"_{company} band hi", "data": band_hi, "borderWidth": 0,
             "backgroundColor": c + "26", "pointRadius": 0, "fill": "+1"},
            {"label": f"_{company} band lo", "data": band_lo, "borderWidth": 0,
             "backgroundColor": c + "26", "pointRadius": 0},
            _line_ds(f"{company} {L('chart.arr.fit')}", solid, i,
                     pointRadius=0, borderWidth=2.5),
            _line_ds(f"_{company} {L('chart.arr.extrapolated')}", dashed, i,
                     pointRadius=0, borderWidth=2.5, borderDash=[6, 5]),
            {"label": f"{company} {L('chart.arr.anchors')}", "data": anchors,
             "type": "scatter",
             "backgroundColor": c, "borderColor": SURFACE, "borderWidth": 2,
             "pointRadius": 4.5, "pointStyle": "circle"},
            {"label": f"_{company} {L('chart.arr.reported')}", "data": reported,
             "type": "scatter",
             "backgroundColor": SURFACE, "borderColor": c, "borderWidth": 2,
             "pointRadius": 4, "pointStyle": "rectRot"},
        ]
        rt = d["realtime"]
        fit = d["fit"]
        cards.append({
            "company": company,
            "display": {"anthropic": "Anthropic", "openai": "OpenAI"}.get(company, company.title()),
            "arr_at_build": rt["arr_at_build"],
            "usd_per_hour": rt["usd_per_hour"],
            "mom": rt["mom_implied"],
            "model": fit.get("model", "exponential"),
            "last_anchor_date": fit["last_anchor_date"],
            "last_anchor_value": fit["last_anchor_value"],
            "color_idx": i,
        })

    chart = {
        "type": "line",
        "data": {"datasets": datasets},
        "options": {
            "scales": {
                "x": {"type": "linear", "ticks": {"__epochDays": epoch0.isoformat()}},
                "y": {"type": "logarithmic",
                      "title": {"display": True, "text": L("chart.arr.y")}},
            },
            "plugins": {"legend": {"labels": {"__filterUnderscore": True}}},
        },
    }
    return {"cards": cards, "chart": chart}


# ---------- ② OpenRouter ----------

def spec_or_weekly_total(p: dict) -> dict:
    weeks = p.get("weekly_chart", [])
    labels = [w["x"] for w in weeks]
    totals = [round(sum(w["ys"].values()) / 1e12, 2) for w in weeks]
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": [
            _line_ds(L("chart.or_weekly.label"), totals, 0, fill=True,
                     backgroundColor=color(0) + "33", pointRadius=0),
        ]},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.or_weekly.y")}}}},
    }


def spec_or_top_models(p: dict, top_n: int = 12) -> dict:
    agg: dict[str, float] = {}
    for r in p.get("models_week", []):
        agg[r["permaslug"]] = agg.get(r["permaslug"], 0) + r["prompt_tokens"] + r["completion_tokens"]
    top = sorted(agg.items(), key=lambda kv: -kv[1])[:top_n]
    return {
        "type": "bar",
        "data": {
            "labels": [short_model_name(s) for s, _ in top],
            "datasets": [{"label": L("chart.or_top.label"),
                          "data": [round(v / 1e12, 3) for _, v in top],
                          "backgroundColor": [color(i) for i in range(len(top))],
                          "borderWidth": 0, "borderRadius": 3}],
        },
        "options": {"indexAxis": "y", "plugins": {"legend": {"display": False}},
                    "scales": {"x": {"title": {"display": True, "text": "T tokens / 7d"}}}},
    }


def spec_or_tracked(cfg: dict) -> dict:
    """重点模型滚动 7 天 Token——由我们的每日快照累积（ADR-002 口径）。"""
    tracked = cfg.get("models_tracked", [])
    by_date: dict[str, dict[str, float]] = {}
    for snap in daily_snapshots("openrouter"):
        day = snap["snapshot_date"]
        agg: dict[str, float] = {}
        for r in snap["payload"].get("models_week", []):
            if r["permaslug"] in tracked:
                agg[r["permaslug"]] = agg.get(r["permaslug"], 0) + r["prompt_tokens"] + r["completion_tokens"]
        by_date[day] = agg
    labels = sorted(by_date)[-90:]
    datasets = [
        _line_ds(short_model_name(slug),
                 [round(by_date[d].get(slug, 0) / 1e9, 1) or None for d in labels],
                 i, spanGaps=True, pointRadius=3)
        for i, slug in enumerate(tracked)
    ]
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.or_tracked.y")}}}},
    }


# ---------- ② Vercel ----------

def _vercel_latest(p: dict, metric: str) -> dict | None:
    rows = [r for r in p.get("series", []) if r["metric"] == metric]
    return rows[-1] if rows else None


def spec_vercel_share_bar(p: dict, metric: str, top_n: int = 10) -> dict:
    row = _vercel_latest(p, metric) or {"shares": [], "day": "?"}
    pairs = row["shares"][:top_n]
    return {
        "type": "bar",
        "data": {
            "labels": [name for name, _ in pairs],
            "datasets": [{"label": f"{metric} {L('chart.share_pct')} ({row['day']})",
                          "data": [round(v, 1) for _, v in pairs],
                          "backgroundColor": [color(i) for i in range(len(pairs))],
                          "borderWidth": 0, "borderRadius": 3}],
        },
        "options": {"indexAxis": "y", "plugins": {"legend": {"display": False}},
                    "scales": {"x": {"title": {"display": True,
                                               "text": L("chart.share_pct")}}}},
    }


def spec_vercel_trend(p: dict, metric: str = "tokens", top_n: int = 5) -> dict:
    rows = [r for r in p.get("series", []) if r["metric"] == metric]
    labels = [r["day"] for r in rows][-90:]
    rows = rows[-90:]
    latest = rows[-1]["shares"] if rows else []
    tops = [name for name, _ in latest[:top_n]]
    datasets = []
    for i, name in enumerate(tops):
        series = []
        for r in rows:
            v = dict(r["shares"]).get(name)
            series.append(round(v, 2) if v is not None else None)
        datasets.append(_line_ds(name, series, i, spanGaps=True, pointRadius=0))
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.vercel_trend.y")}}}},
    }


# ---------- ② SDK / Epoch 表 ----------

def spec_sdk(p: dict) -> dict:
    npm_map = [("openai", "openai"), ("anthropic", "@anthropic-ai/sdk"), ("google-genai", "@google/genai")]
    pypi = p.get("pypi", {})
    npm = p.get("npm", {})
    labels = [lbl for lbl, _ in npm_map]
    npm_vals = [round((npm.get(pkg, {}).get("last-week", {}).get("downloads") or 0) / 1e6, 2)
                for _, pkg in npm_map]
    pypi_vals = [round((pypi.get(lbl, {}).get("last_week") or 0) / 1e6, 2) for lbl in labels]
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": [
            {"label": L("chart.sdk.npm"), "data": npm_vals,
             "backgroundColor": color(0), "borderWidth": 0, "borderRadius": 3},
            {"label": L("chart.sdk.pypi"), "data": pypi_vals,
             "backgroundColor": color(1), "borderWidth": 0, "borderRadius": 3},
        ]},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.sdk.y")}}}},
    }


def table_epoch_sites(p: dict, top_n: int = 10) -> list[dict]:
    sites = sorted(p.get("sites", []), key=lambda s: -(s["power_mw"] or 0))[:top_n]
    return [{
        "name": s["name"],
        "owner": s["owner"] or "—",
        "users": ", ".join(s["users"][:2]) or "—",
        "country": s["country"] or "—",
        "power_mw": round(s["power_mw"] or 0),
        "h100_k": round((s["h100_equivalents"] or 0) / 1e3),
    } for s in sites]


# ---------- ③ GPU ----------

def gpu_cards(p: dict) -> list[dict]:
    return [{"label": label, **q} for label, q in p.get("gpus", {}).items()]


def spec_gpu_trend() -> dict:
    by_date: dict[str, dict[str, float]] = {}
    labels_set: list[str] = []
    for snap in daily_snapshots("gpu_prices"):
        day = snap["snapshot_date"]
        labels_set.append(day)
        for label, q in snap["payload"].get("gpus", {}).items():
            if q.get("median"):
                by_date.setdefault(label, {})[day] = q["median"]
    labels = sorted(set(labels_set))[-90:]
    datasets = [
        _line_ds(label, [series.get(d) for d in labels], i, spanGaps=True, pointRadius=3)
        for i, (label, series) in enumerate(by_date.items())
    ]
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.gpu.y")}}}},
    }


# ---------- ④ 数据中心 ----------

def cumulative_series(timelines: list[dict], max_points: int = 40,
                      as_of: str | None = None) -> dict:
    """按月末聚合：每站取当月最后一条记录的功率/H100-eq，行业求和累计。

    截断到 as_of（默认今天）：timelines 里含未来规划里程碑，不截断会与
    「当前投运」汇总卡片口径打架。
    """
    as_of = as_of or store.utc_today()
    events = sorted((t for t in timelines if t.get("date") and t["date"] <= as_of),
                    key=lambda t: t["date"])
    if not events:
        return {"labels": [], "power_gw": [], "h100_m": []}
    current_power: dict[str, float] = {}
    current_h100: dict[str, float] = {}
    monthly: dict[str, tuple[float, float]] = {}
    for e in events:
        current_power[e["site"]] = e["power_mw"] or current_power.get(e["site"], 0)
        current_h100[e["site"]] = e["h100_equivalents"] or current_h100.get(e["site"], 0)
        month = e["date"][:7]
        monthly[month] = (sum(current_power.values()), sum(current_h100.values()))
    labels = sorted(monthly)[-max_points:]
    return {
        "labels": labels,
        "power_gw": [round(monthly[m][0] / 1e3, 2) for m in labels],
        "h100_m": [round(monthly[m][1] / 1e6, 2) for m in labels],
    }


def spec_dc_growth(p: dict) -> dict:
    s = cumulative_series(p.get("timelines", []))
    return {
        "type": "bar",
        "data": {"labels": s["labels"], "datasets": [
            {"label": L("chart.dc.power"), "data": s["power_gw"],
             "backgroundColor": color(9) + "B3",
             "borderWidth": 0, "borderRadius": 2, "yAxisID": "y"},
            {"label": L("chart.dc.h100"), "data": s["h100_m"], "type": "line",
             "borderColor": color(2), "backgroundColor": color(2), "pointRadius": 0,
             "borderWidth": 2.5, "yAxisID": "y2"},
        ]},
        "options": {"scales": {
            "y": {"title": {"display": True, "text": "GW"}},
            "y2": {"position": "right", "grid": {"drawOnChartArea": False},
                   "title": {"display": True, "text": "M H100-eq"}},
        }},
    }


HIGHLIGHT_RE = re.compile(r"anthropic|openai|xai|x\.ai|nvidia|gigawatt|\bGW\b", re.I)


def news_items(p: dict, top_n: int = 18) -> list[dict]:
    items = p.get("items", [])[:top_n]
    return [{
        "date": (i.get("published") or "")[:10] or "—",
        "title": i["title"],
        "link": i["link"],
        "source": i["source_name"],
        "highlight": bool(HIGHLIGHT_RE.search(i["title"])),
    } for i in items]


# ---------- 汇总 ----------

def collect() -> dict:
    all_status = status.load()
    source_status = {}
    for name, cfg in registry.load().items():
        if not cfg.get("fetcher"):
            continue
        st = all_status.get(name, {})
        latest = store.read_latest(name) or {}
        source_status[name] = {
            "freshness": freshness(st.get("last_success")),
            "snapshot_date": latest.get("snapshot_date"),
            "error": st.get("error"),
        }
    arr_status = all_status.get("arr", {})
    source_status["arr"] = {"freshness": freshness(arr_status.get("last_success")),
                            "snapshot_date": (arr_status.get("last_success") or "")[:10] or None,
                            "error": arr_status.get("error")}

    arr = store.read_json(store.DATA / "derived" / "arr.json") or {"companies": {}}
    or_p = payload("openrouter")
    or_cfg = registry.load().get("openrouter", {})
    vercel_p = payload("vercel_gateway")
    epoch_p = payload("epoch_datacenters")
    gpu_p = payload("gpu_prices")

    quotes_file = store.DATA / "manual" / "quotes.yml"
    quotes = (yaml.safe_load(quotes_file.read_text(encoding="utf-8")) or {}).get("quotes") or []

    arr_spec = spec_arr(arr)
    epoch_agg = epoch_p.get("aggregates", {})
    charts = {
        "arr_chart": arr_spec["chart"],
        "or_tracked": spec_or_tracked(or_cfg),
        "or_weekly_total": spec_or_weekly_total(or_p),
        "or_top_models": spec_or_top_models(or_p),
        "vercel_tokens": spec_vercel_share_bar(vercel_p, "tokens"),
        "vercel_cost": spec_vercel_share_bar(vercel_p, "cost"),
        "vercel_trend": spec_vercel_trend(vercel_p),
        "sdk": spec_sdk(payload("sdk_downloads")),
        "gpu_trend": spec_gpu_trend(),
        "dc_growth": spec_dc_growth(epoch_p),
    }
    return {
        "build_ts": store.utc_now().isoformat(timespec="seconds"),
        "source_status": source_status,
        "arr_cards": arr_spec["cards"],
        "epoch_cards": {
            "sites": epoch_agg.get("site_count", 0),
            "power_gw": round(epoch_agg.get("total_power_mw", 0) / 1e3, 1),
            "h100_m": round(epoch_agg.get("total_h100_equivalents", 0) / 1e6, 1),
            "capex_busd": epoch_agg.get("total_capital_cost_busd", 0),
        },
        "gpu_cards": gpu_cards(gpu_p),
        "epoch_sites": table_epoch_sites(epoch_p),
        "news": news_items(payload("news")),
        "quotes": quotes,
        "charts": charts,
    }


def main() -> int:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    env.globals["t"] = t
    ctx = collect()
    dashboard = {
        "build_ts": ctx["build_ts"],
        "sources": ctx["source_status"],
        "arr_cards": ctx["arr_cards"],
        "charts": ctx["charts"],
    }
    html = env.get_template("index.html.j2").render(
        **ctx,
        dashboard_json=json.dumps(dashboard, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        i18n_json=json.dumps(I18N, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        style=(TEMPLATE_DIR / "style.css").read_text(encoding="utf-8"),
        app_js=(TEMPLATE_DIR / "app.js").read_text(encoding="utf-8"),
        chart_js=(SITE / "vendor" / "chart.umd.min.js").read_text(encoding="utf-8"),
    )
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"build ok -> {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
