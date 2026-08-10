# 源：sdk_downloads

> TL;DR：npm 官方下载量 API + pypistats.org，低风险；注意这只是采用度 proxy，不是用量。
> 何时读我：改 scripts/fetch/sdk_downloads.py 或加跟踪包之前。
> 最后核对日期：2026-08-10

## Endpoint

- npm：`https://api.npmjs.org/downloads/point/{last-day|last-week}/{package}`
  （scoped 包如 `@anthropic-ai/sdk` 直接放路径里即可）。
- pypi：`https://pypistats.org/api/packages/{package}/recent`
  → `{data: {last_day, last_week, last_month}}`。
- 包列表配置在 `data/sources.yml`（npm_packages / pypi_packages），加包只改注册表。

## 口径

- npm last-day 是 UTC 日；当天早间拉取时通常是**前一天**的数（响应里 start/end 有标注）。
- pypistats 排除已知镜像流量，但 CI 重复安装仍会灌水——页面 Methodology 必须写明
  「下载量 ≈ 开发者关注度 proxy，不等于 API 用量」。
- 周末 npm/pypi 下载量规律性下跌，画图建议同时给 7DMA。

## 坑

- pypistats 是**按 IP 的突发限流**（约每几秒 1 次，无 `Retry-After` 头）；连续拉 3 个包
  就会撞 429（2026-08-05、08-09 各丢过一天）。现已在 `sdk_downloads.py` 里对 pypi 请求间
  留 6s 间隔（`PYPI_REQUEST_SPACING_S`），并靠 `net.get` 的 429 退避重试（8s→16s→24s）兜底。
  加包越多，本源整体耗时越长，注意别让单源跑太久。
- npm API 对不存在的包返回 404 → net.get 直接抛错 → 该源本轮失败（合意行为）。
- validate 用 last-week > 0 兜底（last-day 在 UTC 清晨可能为 0 或未出数）。

## 样本

`docs/sources/samples/sdk_downloads.payload.json`。
