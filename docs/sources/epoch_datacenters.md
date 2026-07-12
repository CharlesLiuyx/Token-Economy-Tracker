# 源：epoch_datacenters

> TL;DR：Epoch AI Frontier Data Centers 数据集，官方 CSV 直下（CC-BY），低风险。
> 何时读我：改 scripts/fetch/epoch_datacenters.py 或面板 4a/4b 口径前。
> 最后核对日期：2026-07-12

## Endpoint

- 站点数据：`https://epoch.ai/data/data_centers/data_centers.csv`（2026-07 实测 72 行）
- 建设时间线：`https://epoch.ai/data/data_centers/data_center_timelines.csv`（411 行）
- 数据集主页（找新字段/新文件）：`https://epoch.ai/data/data-centers`
- 许可：CC-BY，页面需注明 “Source: Epoch AI”。源头约每周更新，我们每日拉。

## 字段（进快照的部分）

data_centers.csv → `payload.sites[]`：
`Name / Current H100 equivalents / Current power (MW) / Current total capital cost
(2025 USD billions) / Owner / Users / Current chip types / Country`。

timelines.csv → `payload.timelines[]`（面板 4b 累计增长图的原料）：
`Data center / Date / IT power (MW) / Power (MW) / H100 equivalents`。

`payload.aggregates`：本地聚合 site_count / total_power_mw / total_h100_equivalents /
total_capital_cost_busd（面板 4a 汇总卡片）。

## 坑

- 文本字段带置信度标注（`SpaceXAI #confident`），入库前用 `_strip_tags` 去掉 `#\w+`。
- 数值列有空串，`_num()` 返回 None，聚合按 0 处理。
- timelines 的 `Construction status` 是长文本（含链接），**刻意不入快照**，控制体积。
- CSV 带 BOM，用 `utf-8-sig` 语义处理（fetcher 里 lstrip('﻿')）。
- validate 卡下限 sites≥30：防源头半截 CSV 入库。

## 样本

`docs/sources/samples/epoch_datacenters.payload.json`（截断后的 payload 结构）。
