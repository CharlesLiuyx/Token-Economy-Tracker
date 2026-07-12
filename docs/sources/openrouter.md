# 源：openrouter

> TL;DR：非官方 frontend API，三个 rankings 端点；「日频」靠我们每日快照滚动 7 天数据累积。
> 何时读我：改 scripts/fetch/openrouter.py、面板 2a–2d 口径、或端点疑似改版时。
> 最后核对日期：2026-07-12

## Endpoint（无公开承诺，UA 需带浏览器标识）

Base：`https://openrouter.ai/api/frontend/v1/rankings/`

- `model-rankings-chart` → `{data:{data:[{x:"周一日期", ys:{slug: tokens, Others}}]}}`，
  52 周历史，每周 top9 + Others（面板 2c 全网总量、长期趋势）。
- `models` → 每模型**滚动 7 天**合计（约 400+ 行）：`date`（该模型最近活跃日）、
  `model_permaslug / variant / total_prompt_tokens / total_completion_tokens / count / change`
  （面板 2b/2d；`change` 是周环比）。
- `apps` → `{data:{day:[...], week:[...]}}` Top Apps 按 tokens（附赠面板素材）。

发现过程：页面 RSC 无数据 → 从 `_next/static/chunks/*.js` grep `api/frontend` 得到端点族。
其余可用：`benchmarks / context-length / modality-chart / natural-language /
performance / programming-language / task-spend`（未入库，需要时再加）。

## 口径（页面 Methodology 必须写明）

- OpenRouter 只是聚合路由平台的**切片**，不含各 lab 直连 API 流量。
- **没有公开的每模型日频端点**。面板 2a 的「日频」曲线 = 我们每日快照 `models`
  的滚动 7 天值连成的序列（本质是 7 日滚动和，天然平滑）；历史从首次快照日累积。
- `models` 的 date 字段是「该模型最近活跃日」，同一响应里日期不齐——按 permaslug 用，
  别按 date 聚合全网总量（会漏）。全网总量用 weekly_chart 的 ys 求和。

## 坑

- 端点随时可能改结构/加反爬（kind: unofficial-api）。validate 卡：≥40 周、
  models ≥100 行、周总量 >0。失败时坏数据不入库。
- `:free` 变体是独立行；对比面板按 permaslug 前缀聚合时注意去重 variant。
- 若 404/结构变化：重走发现流程（下载 rankings 页 chunks grep 端点），改版记 ADR。

## 样本

`docs/sources/samples/openrouter.payload.json`。
