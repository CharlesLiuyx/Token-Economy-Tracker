"""data/ -> site/index.html（单文件、离线可开、无外部请求）。

每个面板 = 一个生成函数 + 一个 site/template/panels/*.j2 片段。两类产出：
- spec_*：时序图的 Chart.js 配置子集（line / scatter / 叠加 bar），app.js renderPanel 渲染；
- bars_* / table_* / *_rows：条形图、表格、卡片的纯数据，模板用原生 DOM 画（ADR-006）。
「较 N 天前」的变化量一律由 data/**/daily 快照现算（series_delta），不落盘。

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
# 附属报告：reports/<name>/ 下唯一的报告 .html 复制到 site/<name>/index.html，随 Pages 一起发布。
# 报告由它自己的构建脚本生成（见 reports/llm-release-bench/MAINTAIN.md），这里只搬运、不改内容。
COMPANION_REPORTS = {"llm-release-bench": store.ROOT / "reports" / "llm-release-bench"}

FRESH_WARN_HOURS = 48
FRESH_RED_DAYS = 7

# 与 style.css 一致的系列色（Linear 风格中饱和，light/dark 双主题均可读；
# 0=Anthropic clay、1=OpenAI teal，与 CSS --c-clay/--c-teal 对应）
PALETTE = ["#D97757", "#10A37F", "#5E6AD2", "#EB5757", "#F2C94C",
           "#4EA7FC", "#9E8CFC", "#E56EB3", "#26B5CE", "#4CB782",
           "#95A2B3", "#B08968", "#F2994A", "#2F80ED", "#BB6BD9", "#6B8E23"]
NEUTRAL = "#95A2B3"
# 同一厂商在全页所有图里同色（模型名/显示名按关键字归属）；未识别 -> 中性色 + 空心
VENDORS = [
    ("anthropic", r"anthropic|claude", "#D97757"),
    ("openai", r"openai|gpt|codex|\bo[134]\b", "#10A37F"),
    ("google", r"google|gemini|gemma", "#5E6AD2"),
    ("xai", r"x-ai|xai|grok", "#EB5757"),
    ("deepseek", r"deepseek", "#4EA7FC"),
    ("moonshot", r"moonshot|kimi", "#9E8CFC"),
    ("zhipu", r"z-ai|zhipu|glm", "#E56EB3"),
    ("alibaba", r"qwen|alibaba", "#F2994A"),
    ("meta", r"meta|llama|muse", "#2F80ED"),
    ("mistral", r"mistral", "#B08968"),
    ("tencent", r"tencent|hunyuan|\bhy\d", "#26B5CE"),
    ("minimax", r"minimax", "#4CB782"),
]
DASHES = [None, [6, 4], [2, 3], [10, 3, 2, 3]]   # 同厂商多条线靠线型区分
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


def vendor_of(name: str) -> tuple[str | None, str]:
    """模型 slug / 显示名 -> (厂商, 颜色)；未识别返回 (None, 中性色)。"""
    for vendor, pattern, c in VENDORS:
        if re.search(pattern, name, re.I):
            return vendor, c
    return None, NEUTRAL


def vendor_line_styles(names: list[str]) -> list[dict]:
    """多条线：颜色跟厂商走，同厂商第 2/3 条换线型。"""
    seen: dict[str, int] = {}
    out = []
    for n in names:
        vendor, c = vendor_of(n)
        k = seen.get(vendor or n, 0)
        seen[vendor or n] = k + 1
        style = {"borderColor": c, "backgroundColor": c}
        if DASHES[k % len(DASHES)]:
            style["borderDash"] = DASHES[k % len(DASHES)]
        out.append(style)
    return out


# ---------- 快照序列与变化量 ----------

_SNAP_CACHE: dict[str, list[dict]] = {}


def snapshots(source: str) -> list[dict]:
    if source not in _SNAP_CACHE:
        _SNAP_CACHE[source] = daily_snapshots(source)
    return _SNAP_CACHE[source]


def value_on_or_before(series: dict[str, float], day: str, tolerance: int = 3) -> float | None:
    """取 day 当天或之前最近一天的值；回看超过 tolerance 天视为无可比值。"""
    d = dt.date.fromisoformat(day)
    for back in range(tolerance + 1):
        v = series.get((d - dt.timedelta(days=back)).isoformat())
        if v:
            return v
    return None


def series_delta(series: dict[str, float], days: int) -> float | None:
    """最新值相对 days 天前的变化率（小数）；任一端缺值返回 None。"""
    if not series:
        return None
    last = max(series)
    then = value_on_or_before(series, (dt.date.fromisoformat(last) - dt.timedelta(days=days)).isoformat())
    now = series[last]
    if not then or not now:
        return None
    return now / then - 1


def deltas(series: dict[str, float]) -> dict:
    return {"d1": series_delta(series, 1), "d7": series_delta(series, 7),
            "d30": series_delta(series, 30)}


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
        band_hi = [{"x": day_num(p["date"]), "y": p["hi"] / 1e9} for p in d["series"]]
        band_lo = [{"x": day_num(p["date"]), "y": p["lo"] / 1e9} for p in d["series"]]
        anchors = [{"x": day_num(str(a["date"])), "y": a["value_usd"] / 1e9}
                   for a in d["anchors"] if a["metric"] == "run_rate_arr"]
        reported = [{"x": day_num(str(a["date"])), "y": a["value_usd"] / 1e9}
                    for a in d["anchors"] if a["metric"] == "reported_rev"]
        # 第三方面板估算：只画散点、不入拟合（口径与公司披露不同，见 arr-methodology.md）
        third_party = [{"x": day_num(str(a["date"])), "y": a["value_usd"] / 1e9}
                       for a in d["anchors"] if a["metric"] == "third_party_est"]
        company_sets = [
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
            {"label": f"_{company} {L('chart.arr.third_party')}", "data": third_party,
             "type": "scatter",
             "backgroundColor": SURFACE, "borderColor": c, "borderWidth": 2,
             "pointRadius": 5, "pointStyle": "triangle"},
        ]
        # __group：hover 图例时同公司的置信带/外推段/锚点随拟合线一起高亮（app.js）
        for ds in company_sets:
            ds["__group"] = company
        datasets += company_sets
        rt = d["realtime"]
        fit = d["fit"]
        today = store.utc_today()
        near = min(d["series"], key=lambda p: abs(day_num(p["date"]) - day_num(today)))
        ratio = rt["arr_at_build"] / near["fitted"] if near["fitted"] else 1
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(fit["last_anchor_date"])).days
        cards.append({
            "lo": near["lo"] * ratio, "hi": near["hi"] * ratio,
            "anchor_age_days": age,
            "age_class": "ok" if age <= ANCHOR_FRESH_DAYS else "warn" if age <= ANCHOR_STALE_DAYS else "stale",
            "multiple": rt["arr_at_build"] / fit["last_anchor_value"],
            "n_anchors": fit.get("n_anchors"),
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


ANCHOR_FRESH_DAYS = 45    # 最近披露距今：≤45 天正常，≤90 天提示，更久标红（外推已不可靠）
ANCHOR_STALE_DAYS = 90


def anchor_rows(arr: dict, top_n: int = 14) -> list[dict]:
    """最近披露一览（全部口径，新→旧）：估算的地基直接摆在卡片下面。"""
    from scripts.derive import arr as arr_mod
    rows = []
    for company in arr.get("companies", {}):
        for a in (x for x in arr_mod.load_anchors() if x["company"] == company):
            url = str(a["source_url"]).strip()
            host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", url))
            rows.append({"company": company, "date": str(a["date"]), "value_b": a["value_usd"] / 1e9,
                         "metric": a["metric"], "confidence": a.get("confidence") or "likely",
                         "url": url, "host": host, "note": a.get("note") or "",
                         "note_en": a.get("note_en") or a.get("note") or ""})
    rows.sort(key=lambda r: (r["date"], r["value_b"]), reverse=True)
    return rows[:top_n]


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


def _or_totals(snap_payload: dict) -> dict[str, float]:
    agg: dict[str, float] = {}
    for r in snap_payload.get("models_week", []):
        agg[r["permaslug"]] = agg.get(r["permaslug"], 0) + r["prompt_tokens"] + r["completion_tokens"]
    return agg


def or_history() -> dict[str, dict[str, float]]:
    """{permaslug: {快照日: 滚动 7 天 token}} + "__total"（全部模型合计）。"""
    hist: dict[str, dict[str, float]] = {"__total": {}}
    for snap in snapshots("openrouter"):
        day = snap["snapshot_date"]
        agg = _or_totals(snap["payload"])
        hist["__total"][day] = sum(agg.values())
        for slug, v in agg.items():
            hist.setdefault(slug, {})[day] = v
    return hist


def bars_or_top_models(p: dict, top_n: int = 15) -> list[dict]:
    """Top Models 周合计：条形 + 占平台份额 + 较 7 天前变化（快照现算）。"""
    agg = _or_totals(p)
    total = sum(agg.values()) or 1
    hist = or_history()
    top = sorted(agg.items(), key=lambda kv: -kv[1])[:top_n]
    peak = top[0][1] if top else 1
    rows = []
    for slug, v in top:
        vendor, c = vendor_of(slug)
        rows.append({"label": short_model_name(slug), "slug": slug, "value": v / 1e12,
                     "pct": v / peak * 100, "share": v / total * 100,
                     "d7": series_delta(hist.get(slug, {}), 7),
                     "color": c, "neutral": vendor is None, "vendor": vendor or "other"})
    return rows


def spec_or_tracked(cfg: dict) -> dict:
    """重点模型滚动 7 天 Token——由我们的每日快照累积（ADR-002 口径）。对数轴：
    T 级与百 B 级模型同图，线性轴会把后者压成贴地线。"""
    tracked = cfg.get("models_tracked", [])
    hist = or_history()
    labels = sorted(hist["__total"])[-90:]
    styles = vendor_line_styles(tracked)
    datasets = [
        {"label": short_model_name(slug),
         "data": [round(hist.get(slug, {}).get(d, 0) / 1e9, 1) or None for d in labels],
         "spanGaps": True, "pointRadius": 0, "borderWidth": 2, **styles[i]}
        for i, slug in enumerate(tracked)
    ]
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"type": "logarithmic",
                                     "title": {"display": True, "text": L("chart.or_tracked.y")}}}},
    }


# ---------- ② Vercel ----------

def _vercel_latest(p: dict, metric: str) -> dict | None:
    rows = [r for r in p.get("series", []) if r["metric"] == metric]
    return rows[-1] if rows else None


def bars_vercel_share(p: dict, metric: str, top_n: int = 10) -> dict:
    """份额 Top N：条形 + 较 7 天前的百分点变化（源页面自带历史，无需快照）。"""
    rows_all = [r for r in p.get("series", []) if r["metric"] == metric and r["shares"]]
    if not rows_all:
        return {"day": "—", "rows": []}
    row = rows_all[-1]
    prev = dict(rows_all[-8]["shares"]) if len(rows_all) >= 8 else {}
    pairs = row["shares"][:top_n]
    peak = pairs[0][1] if pairs else 1
    rows = []
    for name, v in pairs:
        vendor, c = vendor_of(name)
        rows.append({"label": name, "value": v, "pct": v / peak * 100,
                     "d7pp": (v - prev[name]) if name in prev else None,
                     "color": c, "neutral": vendor is None, "vendor": vendor or "other"})
    return {"day": row["day"], "rows": rows}


def spec_vercel_trend(p: dict, metric: str = "tokens", top_n: int = 8) -> dict:
    rows = [r for r in p.get("series", []) if r["metric"] == metric]
    labels = [r["day"] for r in rows][-90:]
    rows = rows[-90:]
    latest = rows[-1]["shares"] if rows else []
    tops = [name for name, _ in latest[:top_n]]
    datasets = []
    styles = vendor_line_styles(tops)
    for i, name in enumerate(tops):
        series = []
        for r in rows:
            v = dict(r["shares"]).get(name)
            series.append(round(v, 2) if v is not None else None)
        datasets.append({"label": name, "data": series, "spanGaps": True,
                         "pointRadius": 0, "borderWidth": 2, **styles[i]})
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"title": {"display": True,
                                               "text": L("chart.vercel_trend.y")}}}},
    }


# ---------- ② SDK / Epoch 表 ----------

SDK_PACKAGES = [("openai", "openai", "openai"), ("anthropic", "@anthropic-ai/sdk", "anthropic"),
                ("google-genai", "@google/genai", "google")]


def sdk_history() -> dict[str, dict[str, float]]:
    hist: dict[str, dict[str, float]] = {}
    for snap in snapshots("sdk_downloads"):
        day, p = snap["snapshot_date"], snap["payload"]
        for label, npm_pkg, _ in SDK_PACKAGES:
            hist.setdefault("pypi:" + label, {})[day] = (p.get("pypi", {}).get(label, {}) or {}).get("last_week") or 0
            hist.setdefault("npm:" + label, {})[day] = ((p.get("npm", {}).get(npm_pkg, {}) or {})
                                                        .get("last-week", {}) or {}).get("downloads") or 0
    return hist


def bars_sdk(p: dict) -> list[dict]:
    """每包两条（npm / PyPI 周下载，百万）+ 较 7 天前变化。"""
    hist = sdk_history()
    rows = []
    for label, npm_pkg, vendor in SDK_PACKAGES:
        c = vendor_of(vendor)[1]
        npm = (p.get("npm", {}).get(npm_pkg, {}).get("last-week", {}) or {}).get("downloads") or 0
        pypi = (p.get("pypi", {}).get(label, {}) or {}).get("last_week") or 0
        rows.append({"label": label, "registry": "npm", "value": npm / 1e6, "color": c, "hollow": True,
                     "d7": series_delta(hist.get("npm:" + label, {}), 7)})
        rows.append({"label": label, "registry": "PyPI", "value": pypi / 1e6, "color": c, "hollow": False,
                     "d7": series_delta(hist.get("pypi:" + label, {}), 7)})
    peak = max((r["value"] for r in rows), default=1) or 1
    for r in rows:
        r["pct"] = r["value"] / peak * 100
    return rows


def table_epoch_sites(p: dict, top_n: int = 15) -> list[dict]:
    sites = sorted(p.get("sites", []), key=lambda s: -(s["power_mw"] or 0))[:top_n]
    peak = (sites[0]["power_mw"] or 1) if sites else 1
    return [{
        "name": s["name"],
        "owner": s["owner"] or "—",
        "users": ", ".join(s["users"][:2]) or "—",
        "country": s["country"] or "—",
        "power_mw": round(s["power_mw"] or 0),
        "power_pct": (s["power_mw"] or 0) / peak * 100,
        "h100_k": round((s["h100_equivalents"] or 0) / 1e3),
        "capex_b": s.get("capital_cost_busd") or 0,
    } for s in sites]


# ---------- ③ GPU ----------

def gpu_history() -> dict[str, dict[str, float]]:
    hist: dict[str, dict[str, float]] = {}
    for snap in snapshots("gpu_prices"):
        for label, q in snap["payload"].get("gpus", {}).items():
            if q.get("median"):
                hist.setdefault(label, {})[snap["snapshot_date"]] = q["median"]
    return hist


def _gpu_meta(cfg: dict) -> dict[str, dict]:
    return {label: (spec if isinstance(spec, dict) else {"name": spec})
            for label, spec in (cfg.get("gpus") or {}).items()}


def gpu_rows(p: dict, cfg: dict, spark_days: int = 30) -> list[dict]:
    """GPU 表：当日分位数 + 档位/显存 + 每 GB 显存单价 + 7/30 天变化 + 近 30 天迷你柱。
    顺序 = sources.yml gpus 顺序（与趋势图配色一致）。"""
    hist = gpu_history()
    meta = _gpu_meta(cfg)
    rows = []
    for i, label in enumerate(meta or p.get("gpus", {})):
        q = p.get("gpus", {}).get(label) or {"offers": 0}
        m = meta.get(label, {})
        series = hist.get(label, {})
        days = sorted(series)[-spark_days:]
        vals = [series[d] for d in days]
        lo, hi = (min(vals), max(vals)) if vals else (0, 0)
        row = {"label": label, "name": m.get("name", label), "tier": m.get("tier", "datacenter"),
               "vram_gb": m.get("vram_gb"), "offers": q.get("offers", 0), "color": color(i),
               "days_tracked": len(series), "first_day": min(series) if series else None,
               "spark": [{"day": d, "v": v, "h": 20 + (v - lo) / (hi - lo) * 80 if hi > lo else 60}
                         for d, v in zip(days, vals)],
               **deltas(series)}
        if q.get("offers"):
            span = (q["max"] - q["min"]) or 1
            row.update(median=q["median"], p25=q["p25"], p75=q["p75"], min=q["min"], max=q["max"],
                       box_left=(q["p25"] - q["min"]) / span * 100,
                       box_width=max((q["p75"] - q["p25"]) / span * 100, 1.5),
                       med_left=(q["median"] - q["min"]) / span * 100,
                       per_gb=q["median"] / m["vram_gb"] if m.get("vram_gb") else None)
        rows.append(row)
    return rows


def spec_gpu_trend(cfg: dict) -> dict:
    """16 卡型从 $0.2 到 $10 跨两个数量级 -> 对数轴；配色序 = sources.yml 顺序，
    第二轮颜色改虚线；只有 1 个点的新卡型显示数据点，否则不画点。"""
    hist = gpu_history()
    order = [l for l in _gpu_meta(cfg) if l in hist] + [l for l in hist if l not in _gpu_meta(cfg)]
    labels = sorted({d for series in hist.values() for d in series})[-90:]
    datasets = []
    for i, label in enumerate(order):
        data = [hist[label].get(d) for d in labels]
        ds = _line_ds(label, data, i, spanGaps=True, borderWidth=2,
                      pointRadius=3 if sum(v is not None for v in data) < 2 else 0)
        if i >= 8:
            ds["borderDash"] = [6, 4]
        datasets.append(ds)
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {"scales": {"y": {"type": "logarithmic",
                                     "title": {"display": True, "text": L("chart.gpu.y")}}}},
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


def news_items(p: dict, top_n: int = 24) -> list[dict]:
    """最新 N 条；is_new = 标题未出现在上一份快照里（今日新增）。"""
    snaps = snapshots("news")
    prev = {i["title"] for i in snaps[-2]["payload"].get("items", [])} if len(snaps) >= 2 else set()
    items = p.get("items", [])[:top_n]
    return [{
        "date": (i.get("published") or "")[:10] or "—",
        "title": i["title"],
        "link": i["link"],
        "source": i["source_name"],
        "highlight": bool(HIGHLIGHT_RE.search(i["title"])),
        "is_new": bool(prev) and i["title"] not in prev,
    } for i in items]


# ---------- ⓪ 今日要点 ----------

def load_digest(limit_days: int = 7) -> list[dict]:
    """data/manual/digest.yml：每日 agent 手写的「今天值得知道什么」，新→旧取最近 N 天。"""
    path = store.DATA / "manual" / "digest.yml"
    if not path.exists():
        return []
    days = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("digest") or []
    out = []
    for d in sorted(days, key=lambda d: str(d["date"]), reverse=True)[:limit_days]:
        items = []
        for it in d.get("items") or []:
            text = it.get("text") or {}
            if not it.get("tag") or not isinstance(text, dict) or not text.get("zh") or not text.get("en"):
                raise ValueError(f"digest.yml {d['date']}: 条目需要 tag 与 text.zh / text.en: {it}")
            if not it.get("source_url"):
                raise ValueError(f"digest.yml {d['date']}: 条目缺 source_url: {it}")
            items.append({"tag": it["tag"], "zh": text["zh"], "en": text["en"], "url": it["source_url"]})
        out.append({"date": str(d["date"]), "items": items})
    return out


def radar_rows(or_cfg: dict, gpu_cfg: dict, vercel_p: dict) -> list[dict]:
    """变化雷达：各源关键指标的最新值 + 较 1/7/30 天前变化，全部由每日快照现算。
    kind 决定模板里的指标名（i18n），subject 是不翻译的数据名（模型 / 卡型 / 包名）。"""
    rows = []

    def add(kind, subject, series, fmt, href, scale=1.0):
        if not series:
            return
        last = max(series)
        rows.append({"kind": kind, "subject": subject, "value": fmt.format(series[last] * scale),
                     "asof": last, "href": href, **deltas(series)})

    orh = or_history()
    add("or_total", "", orh["__total"], "{:.1f} T", "#p-or_weekly_total", 1e-12)
    for slug in or_cfg.get("models_tracked", [])[:5]:
        add("or_model", short_model_name(slug), orh.get(slug, {}), "{:.0f} B", "#p-or_tracked", 1e-9)
    tok = [r for r in vercel_p.get("series", []) if r["metric"] == "tokens" and r["shares"]]
    if tok:
        name = tok[-1]["shares"][0][0]
        add("vercel_share", name, {r["day"]: dict(r["shares"]).get(name) or 0 for r in tok},
            "{:.1f}%", "#p-vercel_tokens")
    sdk = sdk_history()
    for label, _, _ in SDK_PACKAGES[:2]:
        add("sdk_pypi", label, sdk.get("pypi:" + label, {}), "{:.1f} M", "#p-sdk", 1e-6)
    gh = gpu_history()
    for label in [l for l in ("B200", "H200", "H100", "A100", "RTX 5090") if l in gh]:
        add("gpu", label, gh[label], "${:.2f}", "#p-gpu_table")
    dc_power, dc_sites = {}, {}
    for snap in snapshots("epoch_datacenters"):
        agg = snap["payload"].get("aggregates", {})
        dc_power[snap["snapshot_date"]] = agg.get("total_power_mw", 0) / 1e3
        dc_sites[snap["snapshot_date"]] = agg.get("site_count", 0)
    add("dc_power", "", dc_power, "{:.1f} GW", "#p-dc_growth")
    add("dc_sites", "", dc_sites, "{:.0f}", "#p-epoch_sites")
    return rows


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

    # 人工维护源：以最近一条每日速读的日期为准（>2 天提示、>7 天标红——速读断更要看得见）
    digest = load_digest()
    last_manual = digest[0]["date"] if digest else None
    manual_age = (dt.date.fromisoformat(store.utc_today()) - dt.date.fromisoformat(last_manual)).days \
        if last_manual else None
    source_status["manual"] = {
        "freshness": "missing" if manual_age is None else "ok" if manual_age <= 2
        else "warn" if manual_age <= 7 else "stale",
        "snapshot_date": last_manual, "error": None}

    arr = store.read_json(store.DATA / "derived" / "arr.json") or {"companies": {}}
    or_p = payload("openrouter")
    or_cfg = registry.load().get("openrouter", {})
    vercel_p = payload("vercel_gateway")
    epoch_p = payload("epoch_datacenters")
    gpu_p = payload("gpu_prices")

    quotes_file = store.DATA / "manual" / "quotes.yml"
    quotes = (yaml.safe_load(quotes_file.read_text(encoding="utf-8")) or {}).get("quotes") or []

    gpu_cfg = registry.load().get("gpu_prices", {})
    arr_spec = spec_arr(arr)
    epoch_agg = epoch_p.get("aggregates", {})
    news = news_items(payload("news"))
    charts = {
        "arr_chart": arr_spec["chart"],
        "or_tracked": spec_or_tracked(or_cfg),
        "or_weekly_total": spec_or_weekly_total(or_p),
        "vercel_trend": spec_vercel_trend(vercel_p),
        "gpu_trend": spec_gpu_trend(gpu_cfg),
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
        "today": store.utc_today(),
        "vendor_legend": [(v, c) for v, _, c in VENDORS],
        "neutral_color": NEUTRAL,
        "digest": digest,
        "radar": radar_rows(or_cfg, gpu_cfg, vercel_p),
        "anchor_rows": anchor_rows(arr),
        "or_top": bars_or_top_models(or_p),
        "vercel_tokens": bars_vercel_share(vercel_p, "tokens"),
        "vercel_cost": bars_vercel_share(vercel_p, "cost"),
        "sdk_rows": bars_sdk(payload("sdk_downloads")),
        "gpu_rows": gpu_rows(gpu_p, gpu_cfg),
        "epoch_sites": table_epoch_sites(epoch_p),
        "news": news,
        "news_new": sum(1 for n in news if n["is_new"]),
        "quotes": sorted(quotes, key=lambda q: str(q.get("date")), reverse=True),
        "charts": charts,
    }


def fmt_delta(v: float | None, unit: str = "%", digits: int = 1) -> str:
    """变化量：+3.2% / −1.4pp / —（无可比值）。unit='%' 时入参是小数。"""
    if v is None:
        return "—"
    x = v * 100 if unit == "%" else v
    if abs(x) < 0.05:
        return "0" + unit
    return f"{'+' if x > 0 else '−'}{abs(x):.{digits}f}{unit}"


def delta_class(v: float | None) -> str:
    return "flat" if v is None or abs(v) < 0.0005 else "up" if v > 0 else "down"


def copy_companion_reports(site: Path = SITE, reports: dict[str, Path] | None = None) -> list[Path]:
    """把每个附属报告复制成 site/<name>/index.html。目录或报告缺失时跳过并提示，不让主站构建失败。"""
    written = []
    for name, src_dir in (COMPANION_REPORTS if reports is None else reports).items():
        htmls = sorted(src_dir.glob("*.html")) if src_dir.is_dir() else []
        if len(htmls) != 1:
            print(f"warn: companion report {name}: expected 1 .html in {src_dir}, found {len(htmls)}; skipped")
            continue
        dst = site / name / "index.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(htmls[0].read_bytes())
        written.append(dst)
    return written


def main() -> int:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    env.globals["t"] = t
    env.filters["delta"] = fmt_delta
    env.filters["dcls"] = delta_class
    ctx = collect()
    terms = yaml.safe_load((TEMPLATE_DIR / "terms.yml").read_text(encoding="utf-8"))
    dashboard = {
        "build_ts": ctx["build_ts"],
        "sources": ctx["source_status"],
        "arr_cards": ctx["arr_cards"],
        "charts": ctx["charts"],
    }
    html = env.get_template("index.html.j2").render(
        **ctx,
        dashboard_json=json.dumps(dashboard, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        terms_json=json.dumps(terms, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        i18n_json=json.dumps(I18N, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        style=(TEMPLATE_DIR / "style.css").read_text(encoding="utf-8"),
        app_js=(TEMPLATE_DIR / "app.js").read_text(encoding="utf-8"),
        chart_js=(SITE / "vendor" / "chart.umd.min.js").read_text(encoding="utf-8"),
    )
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"build ok -> {out} ({out.stat().st_size / 1024:.0f} KB)")
    for dst in copy_companion_reports():
        print(f"companion report -> {dst} ({dst.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
