"""fetcher 的离线解析单测（不打网络）。真实响应样本见 docs/sources/samples/。"""

from datetime import date, timedelta

import pytest

from scripts.fetch import epoch_datacenters, news, sdk_downloads
from scripts.lib.schema import SchemaError

RSS_FIXTURE = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>q</title>
<item>
  <title>New 1 GW AI data center announced</title>
  <link>https://news.google.com/rss/articles/abc123</link>
  <pubDate>Fri, 10 Jul 2026 08:00:00 GMT</pubDate>
  <source url="https://www.reuters.com">Reuters</source>
</item>
</channel></rss>"""


def test_news_parse_feed():
    items = news._parse_feed(RSS_FIXTURE)
    assert len(items) == 1
    assert items[0]["source_name"] == "Reuters"
    assert items[0]["published"].startswith("2026-07-10")


def test_news_domain_whitelist():
    item = {"source_url": "https://www.reuters.com"}
    assert news._domain_ok(item, ["reuters.com"])
    assert not news._domain_ok(item, ["bloomberg.com"])
    assert not news._domain_ok({"source_url": "https://fakereuters.com"}, ["reuters.com"])


def test_epoch_strip_tags_and_num():
    assert epoch_datacenters._strip_tags("SpaceXAI #confident") == "SpaceXAI"
    assert epoch_datacenters._num("946") == 946.0
    assert epoch_datacenters._num("") is None


def test_epoch_validate_rejects_truncated():
    payload = {
        "sites": [{"name": "x"}] * 5,
        "timelines": [{"site": "x"}],
        "aggregates": {"total_power_mw": 1, "total_h100_equivalents": 1},
    }
    with pytest.raises(SchemaError, match="疑似源头截断"):
        epoch_datacenters.validate(payload)


def _sdk_payload(npm_end: str):
    """构造最小 sdk_downloads payload；npm last-day.end 可控以测新鲜度守卫。"""
    return {
        "npm": {
            "openai": {
                "last-day": {"downloads": 1, "start": npm_end, "end": npm_end},
                "last-week": {"downloads": 7},
            }
        },
        "pypi": {"openai": {"last_week": 7}},
    }


def test_sdk_validate_accepts_fresh_npm():
    fresh = (date.today() - timedelta(days=2)).isoformat()
    sdk_downloads.validate(_sdk_payload(fresh))  # 正常 1–2 日滞后应通过


def test_sdk_validate_rejects_frozen_npm():
    stale = (date.today() - timedelta(days=sdk_downloads.NPM_STALE_MAX_DAYS + 3)).isoformat()
    with pytest.raises(SchemaError, match="疑似上游冻结"):
        sdk_downloads.validate(_sdk_payload(stale))


def test_sdk_validate_skips_guard_when_end_missing():
    payload = _sdk_payload("2020-01-01")
    del payload["npm"]["openai"]["last-day"]["end"]
    sdk_downloads.validate(payload)  # 无 end 字段时跳过守卫、不新增失败面


def test_sdk_npm_entry_from_range(monkeypatch):
    """range 通路：取最后非零日作 last-day，前 7 日求和作 last-week（尾部未出数的 0 跳过）。"""
    rows = [{"day": f"2026-10-{d:02d}", "downloads": 0 if d in (19, 26, 27) else d} for d in range(13, 28)]
    monkeypatch.setattr(sdk_downloads.net, "get_json", lambda url: {"downloads": rows})
    entry = sdk_downloads._npm_entry("openai", date(2026, 10, 27))
    assert entry["last-day"] == {"downloads": 25, "start": "2026-10-25", "end": "2026-10-25"}
    assert entry["last-week"] == {
        "downloads": 20 + 21 + 22 + 23 + 24 + 25,
        "start": "2026-10-19",
        "end": "2026-10-25",
    }


def test_sdk_npm_entry_all_zero_fails_validate(monkeypatch):
    rows = [{"day": "2026-10-26", "downloads": 0}]
    monkeypatch.setattr(sdk_downloads.net, "get_json", lambda url: {"downloads": rows})
    payload = {"npm": {"openai": sdk_downloads._npm_entry("openai", date(2026, 10, 27))},
               "pypi": {"openai": {"last_week": 7}}}
    with pytest.raises(SchemaError):
        sdk_downloads.validate(payload)
