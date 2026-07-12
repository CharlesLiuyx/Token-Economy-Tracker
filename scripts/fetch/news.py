"""AI 数据中心新闻：Google News RSS 定向查询 + 源域名白名单。

仅存 标题/链接/来源/日期；URL 去重；latest 维护滚动窗口（与历史 daily 合并）。
查询与白名单配置在 data/sources.yml。坑见 docs/sources/news.md。
"""

from __future__ import annotations

import email.utils
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema, store

SOURCE = "news"
RSS_URL = "https://news.google.com/rss/search"
MAX_ITEMS = 300


def _parse_feed(xml_text: str) -> list[dict]:
    items = []
    root = ET.fromstring(xml_text)
    for item in root.iter("item"):
        source_el = item.find("source")
        pub = item.findtext("pubDate") or ""
        try:
            published = email.utils.parsedate_to_datetime(pub).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            published = None
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "source_name": (source_el.text or "").strip() if source_el is not None else "",
                "source_url": source_el.get("url", "") if source_el is not None else "",
                "published": published,
            }
        )
    return items


def _domain_ok(item: dict, whitelist: list[str]) -> bool:
    host = item["source_url"].split("//")[-1].split("/")[0].lower()
    return any(host == d or host.endswith("." + d) for d in whitelist)


def fetch(cfg: dict) -> dict:
    fresh: list[dict] = []
    for query in cfg["queries"]:
        xml_text = net.get_text(
            RSS_URL, params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        )
        fresh.extend(_parse_feed(xml_text))

    whitelist = [d.lower() for d in cfg.get("domain_whitelist", [])]
    if whitelist:
        fresh = [i for i in fresh if _domain_ok(i, whitelist)]

    # 与上次 latest 合并成滚动窗口：URL 去重、按时间倒序、截断
    previous = store.read_latest(SOURCE)
    merged: dict[str, dict] = {}
    for item in (previous or {}).get("payload", {}).get("items", []) + fresh:
        if item.get("link") and item.get("title"):
            merged.setdefault(item["link"], item)
    items = sorted(merged.values(), key=lambda i: i.get("published") or "", reverse=True)
    return {"items": items[:MAX_ITEMS], "queries": cfg["queries"]}


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["items"])
    schema.require_nonempty_list(payload["items"], "items")
    for item in payload["items"][:5]:
        schema.require_keys(item, ["title", "link", "source_name", "published"], "items[i]")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
