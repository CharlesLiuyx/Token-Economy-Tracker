# ADR-002：OpenRouter 用 frontend rankings API，日频靠快照累积

> 状态：已决策 2026-07-12

## 背景

OpenRouter 无官方用量 API。探测发现 `api/frontend/v1/rankings/{model-rankings-chart,
models,apps}` 可免鉴权取数，但**不存在每模型日频端点**（模型页 flight 载荷与
stats/* 端点均无日频序列）。

## 决定

用上述三端点（周图 52 周 / 每模型滚动 7 天 / Top Apps）。面板 2a 的「日频」曲线
定义为：每日快照 `models` 端点滚动 7 天值构成的序列（7 日滚动和口径，页面标注）。

## 后果

+ 零逆向成本、数据即刻可用、52 周历史开箱即得。
− 口径是滚动 7 天非自然日；历史明细从首次快照日累积；端点无 SLA，改版需重探
  （发现流程已写入 docs/sources/openrouter.md）。备选：无头浏览器抓页面图表（未实现）。
