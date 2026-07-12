# 源：news

> TL;DR：Google News RSS 定向查询 + 域名白名单；只存标题/链接/来源/日期，滚动窗口 300 条。
> 何时读我：改 scripts/fetch/news.py、调查询词或白名单之前。
> 最后核对日期：2026-07-12

## Endpoint

`https://news.google.com/rss/search?q=<query>&hl=en-US&gl=US&ceid=US:en`
查询词与 domain_whitelist 都配置在 `data/sources.yml`。

## 机制

- 每条只存 `title / link / source_name / source_url / published`（PLAN §4 约定）。
- 白名单按 `<source url>` 的 host 匹配（含子域），防内容农场。
- **滚动窗口**：fetch 时与上次 latest 合并、按 link 去重、时间倒序、截 300 条。
  RSS 单次只给 ~100 条且无历史，窗口靠我们每日快照累积。
- v1 直接展示英文原文标题；中文摘要是可选增强（PLAN §11 风险 6，未做）。

## 坑

- link 是 news.google.com 跳转链接，不是原文 URL——去重按跳转链接做，展示时无碍
  （点击可达原文）；如需原文 URL 需另行解析（未做，避免脆弱依赖）。
- pubDate 是 RFC822 格式，用 `email.utils.parsedate_to_datetime` 解析。
- RSS 无承诺 SLA（kind: unofficial-api）；若改版，先对照 samples 里的旧结构。
- 查询词改动会引起条目池突变，改前先在本地单跑对比结果质量。

## 样本

`docs/sources/samples/news.payload.json`。
