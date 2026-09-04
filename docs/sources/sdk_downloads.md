# 源：sdk_downloads

> TL;DR：npm 官方下载量 API + pypistats.org，低风险；注意这只是采用度 proxy，不是用量。
> 何时读我：改 scripts/fetch/sdk_downloads.py 或加跟踪包之前。
> 最后核对日期：2026-09-04

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
  就会撞 429（2026-08-05、08-09、08-13、08-15 各丢过一天）。现已在 `sdk_downloads.py` 里对
  pypi 请求间留 10s 间隔（`PYPI_REQUEST_SPACING_S`），并靠 `net.get` 的 429 退避重试
  （8s→16s→24s）兜底。加包越多，本源整体耗时越长，注意别让单源跑太久。
- **429 有两种形态，都要兜住**（`_pypi_recent()`）：
  1. **429 带数据**（老形态，限流走 CDN 缓存、数据照发）：net 层退避重试后仍 429 时，
     只要 body 能解析出 `data` 就采用它——08-16 的 durable fix，专治「间隔+退避都躲不掉」
     的持续限流（尤其 CI 共享出口 IP 被邻居 job 耗尽突发桶，见 08-13/08-15 复发）。
  2. **429 无数据**（新形态，返回 53b 的 HTML 限流页、无 `data`）：net 层 ~48s 退避不够，
     故再加**包级耐心重试**（`PYPI_NODATA_429_RETRIES`/`PYPI_NODATA_429_SLEEP_S`，默认再补
     7 轮 ×20s）。端点约 30–60s/包即恢复，多等几轮长间隔通常就能拿到 200——09-02、09-03、
     09-04 连续三天都是这形态把 daily run 打挂、靠巡检回补，故加此兜底把「丢一天」概率压到最低。
     每次耐心尝试真正贡献的是「多一个 `net.get_json` 周期（约 48s 退避）＝多给 CI 共享 IP 一个
     恢复窗口」，故加大**尝试次数**比单纯拉长单次 sleep 更有效；09-04 复盘：4×18s（约 5.5min）
     仍被 CI IP 持续限流击穿（anthropic 包 5.5min 内没等到窗口清空，同刻本地异 IP 首拉即成），
     故 08-16→09-03 的 4×18s 于 09-04 升到 7×20s（总耐心窗口 ~5.5min→~9min）。
     **注**：真正与「CI 共享出口 IP」解耦的通路是 BigQuery `bigquery-public-data.pypi.file_downloads`，
     但需人类提供 GCP 凭据（非无人值守巡检可自助），故先做可自助的重试加固；若本预算仍被击穿，
     再评估引入凭据走 BigQuery 作替代通路。

  只有两种形态都失败（多轮无数据 429）才真正判失败。
- npm API 对不存在的包返回 404 → net.get 直接抛错 → 该源本轮失败（合意行为）。
- validate 用 last-week > 0 兜底（last-day 在 UTC 清晨可能为 0 或未出数）。

## 样本

`docs/sources/samples/sdk_downloads.payload.json`。
