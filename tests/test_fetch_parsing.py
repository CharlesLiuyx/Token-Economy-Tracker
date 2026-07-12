"""fetcher 的离线解析单测（不打网络）。真实响应样本见 docs/sources/samples/。"""

import pytest

from scripts.fetch import epoch_datacenters, news
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
