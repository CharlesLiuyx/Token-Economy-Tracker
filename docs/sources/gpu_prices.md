# 源：gpu_prices

> TL;DR：Vast.ai 公开市场 API（免鉴权），每卡型 on-demand 报价分位数；是低价市场切片，非全市场指数。
> 何时读我：改 scripts/fetch/gpu_prices.py、面板 3a 口径、加卡型时。
> 最后核对日期：2026-07-12

## Endpoint（kind: official-api）

`GET https://console.vast.ai/api/v0/bundles/?q=<url-encoded JSON>`

query 形如：
```json
{"gpu_name": {"eq": "H100 SXM"}, "rentable": {"eq": true},
 "external": {"eq": false}, "type": "on-demand"}
```
注意：**必须 GET + URL 参数 q**；POST JSON body 会 400。
响应 `offers[]`，每条含 `dph_total`（整机 $/hr）、`num_gpus`、`gpu_name`、`geolocation`。

## 口径（页面 Methodology 必须写明）

- 单价 = `dph_total / num_gpus`（$/GPU-hr），对每卡型取 min/p25/median/p75/max。
- 这是 **Vast.ai 市场（含个人/小机房供给）的报价分布**，系统性低于超算云
  （CoreWeave/Lambda）牌价，更低于参考图的 OCPI（Ornn 指数，跨供应商归一）。
  面板必须标注「Source: Vast.ai marketplace」，勿与 OCPI 数字直接比较。
- 卡片展示用 median；p25–p75 做区间带。
- 卡型映射在 sources.yml `gpus:`（2026-07 实测报价数：H100 SXM 36 / H200 21 /
  B200 11 / A100 SXM4 60 / RTX 5090 64）。

## 坑

- gpu_name 是 Vast 的精确枚举（"H100 SXM" / "A100 SXM4" / "RTX 5090"…），
  拼错静默返回空。validate 要求 ≥3 个卡型有 ≥3 条报价。
- B200 报价少（~11 条），中位数波动大；趋势图建议 7DMA。
- offers 数量与价格随时波动，这是市场实时快照——每天固定时间抓（cron）保证可比性。

## 样本

`docs/sources/samples/gpu_prices.payload.json`。
