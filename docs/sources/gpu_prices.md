# 源：gpu_prices

> TL;DR：Vast.ai 公开市场 API（免鉴权），每卡型 on-demand 报价分位数；是低价市场切片，非全市场指数。
> 何时读我：改 scripts/fetch/gpu_prices.py、面板 3a 口径、加卡型时。
> 最后核对日期：2026-11-22（5 卡型扩到 16）

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
- 表格展示 median、min–max 细线 + p25–p75 盒、报价数、每 GB 显存单价（median ÷ vram_gb）、
  较 1 / 7 / 30 天前变化（由每日快照现算）。

## 卡型名单（`sources.yml` → `gpu_prices.gpus`）

`标签: {name: Vast 精确枚举, vram_gb, tier}`，顺序即表格顺序与走势图配色序。**既有标签不可
改名**（历史快照按标签累积）；旧写法 `标签: 枚举名` 仍被接受。

- 2026-07-12 初版 5 个：H100 / H200 / B200 / A100 / RTX 5090。
- 2026-11-22 扩到 16 个，新增 B300、H200 NVL、H100 PCIe、L40S、L4、RTX PRO 6000、
  RTX 6000 Ada、RTX A6000、RTX 4090、RTX 5080、RTX 3090；新卡型序列自该日起累积。
  当日探测报价数：B300 11 / B200 27 / H200 20 / H200 NVL 39 / H100 SXM 11 / H100 PCIE 10 /
  A100 SXM4 64 / L40S 34 / L4 20 / RTX PRO 6000 S 60 / RTX 6000Ada 25 / RTX A6000 24 /
  RTX 5090 64 / RTX 4090 64 / RTX 5080 64 / RTX 3090 64。
- 探测过但没收：GB300（1 条）、GB200（3 条）、H100 NVL（3 条）、L40（4 条）、A10（5 条）报价太少；
  A100 PCIE、A40、RTX PRO 6000 WS / Max-Q、RTX PRO 5000、RTX 5070 Ti、Tesla V100 / T4 与已收
  卡型定位重叠。增删判据见 daily-routine.md 第 4 步。

## 坑

- gpu_name 是 Vast 的精确枚举（"H100 SXM" / "A100 SXM4" / "RTX 5090"…），
  拼错静默返回空。validate 要求至少一半卡型（下限 3 个）有 ≥3 条报价。
- **单次查询最多返回 64 条报价**（传 limit 也不变）：报价多的卡型（A100、RTX 系列）分位数
  只基于前 64 条，报价数显示 64 即表示已触顶。
- 报价少的卡型（B300、H100 约 10 条）中位数波动大，单日跳变不要过度解读。
- offers 数量与价格随时波动，这是市场实时快照——每天固定时间抓（cron）保证可比性。

## 样本

`docs/sources/samples/gpu_prices.payload.json`。
