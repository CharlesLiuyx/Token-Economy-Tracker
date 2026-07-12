# ADR-004：GPU 价格用 Vast.ai 市场 API；OCPI 不可得

> 状态：已决策 2026-07-12

## 背景

参考图的 "OCPI" 经查证为 **Ornn Compute Price Index**（Ornn AI，2026-04 上
Bloomberg Terminal，ICE 拟发期货）——无公开 API，官网是 Framer 营销页。
候选比较：United Compute（JS 壳、无数据端点）、Shadeform（需 API key）、
Vast.ai（公开免鉴权 API，五个目标卡型均有报价）。

## 决定

主源 Vast.ai bundles API（official-api），每卡型取报价分位数（$/GPU-hr）。
备源 getdeploying.com（48 家供应商聚合页，kind: scrape）——**记录但不实现**，
主源断供时再上。

## 后果

+ 官方 API、稳定、免鉴权；分位数比单点价格更诚实。
− 口径是低价市场切片（≠OCPI 跨供应商指数），面板必须标注来源且不与 OCPI 数字
  对比；B200 样本少（~11 条）波动大，用 7DMA 展示。
