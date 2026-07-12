# 源：vercel_gateway

> TL;DR：解析 /ai-gateway/leaderboards 页 RSC flight 载荷里的 rawData；份额百分比、61 天窗口。
> 何时读我：改 scripts/fetch/vercel_gateway.py、面板 2e–2g 口径、或页面改版时。
> 最后核对日期：2026-07-12

## 获取方式（kind: scrape）

页面：`https://vercel.com/ai-gateway/leaderboards`（无 `__NEXT_DATA__`，是 App Router RSC）。

1. 收集所有 `self.__next_f.push([1,"..."])` 字符串块，按序拼接成 flight blob；
2. 定位 `"rawData":` 后第一个 `[`，做括号配平截取 JSON 数组；
3. 数组元素：`{day: ISO 时间, metric, chef_values: [[模型显示名, 份额%], ...]}`，
   metric ∈ {tokens, cost, requests, imageCount, videoCount}，约 61 天窗口。

我们保留 tokens / cost / requests 三个指标，每天每指标 top20 + others_share。

## 口径（页面 Methodology 必须写明）

- **份额（%），不是绝对量**——Vercel 不公开绝对 token 数。面板 2e/2f 直接用份额，
  2g 走势图纵轴是份额%。
- 模型名是**显示名**（如 "Claude Sonnet 4.6"），不是 slug；与 OpenRouter 的
  permaslug 无法直接 join，跨源对比面板需手工映射表（M4 时若需要再建）。
- 只是 Vercel AI Gateway 客户的切片，标题保留来源后缀。
- 页面只给 ~61 天；更长历史靠我们每日快照累积（每天快照含完整 61 天窗口，
  故有大量重叠——这是刻意的，源头会修订近几天数据）。

## 坑

- flight 载荷格式是 Next.js 内部实现，改版风险高。validate 卡：≥30 天、
  含 tokens 指标、份额 0–100。找不到 rawData 直接失败（保留上次 latest）。
- `initialTimeRange` 是 2M；若 Vercel 改成更短窗口，validate 的 30 天下限会报警。
- 需要浏览器 UA，否则可能被 WAF 拦。

## 样本

`docs/sources/samples/vercel_gateway.payload.json`。
