# Token-Tracker — AI Monetization Tracker

每日自动更新的 AI 货币化仪表盘：Frontier Lab ARR 估算、Token 用量（OpenRouter / Vercel
Gateway / SDK 下载）、GPU 租赁价格、AI 数据中心建设。产物为纯静态单文件 HTML。

**当前状态：M0–M5 全部完成。线上：<https://charlesliuyx.github.io/Token-Economy-Tracker/>
（GitHub Actions 每日 00:30 UTC 自动更新；M5 验收=连续 3 天成功，观察至 2026-07-15）。
动手前先读 [docs/PLAN.md](docs/PLAN.md)，进度看 [docs/worklog.md](docs/worklog.md)。**

## 架构一句话

`scripts/fetch/*`（每源独立）→ `data/`（append-only JSON）→ `scripts/build.py`
→ `site/index.html`（单文件，Chart.js 内联）。GitHub Actions 每日跑一次。

## 任务路由表（先读对应文档再动手）

| 你要做的事 | 先读 |
|---|---|
| 实施 / 了解整体方案 | `docs/PLAN.md` |
| 改某个数据源抓取 | `docs/sources/<source>.md` + `docs/sources/samples/` |
| 加 / 改面板 | `docs/frontend.md` + `site/template/panels/` |
| 改 ARR 估算模型 | `docs/arr-methodology.md` |
| 排查数据缺失 / 运维 | `docs/runbook.md` + `data/_status.json` |
| 理解历史决策 | `docs/decisions/` |
| 接续上次会话 | `docs/worklog.md`（结束时也要追加一行） |

常用命令：`make update`（逐源抓取）/ `make build` / `make serve` / `make test` /
`make fetch-<source>`（单源调试）。docs/ 总索引见 `docs/INDEX.md`。

## 硬约束

1. `data/**/daily/` 历史快照不可改写（refetch 窗口内回补除外）。
2. `site/index.html` 是构建产物，只能由 `make build` 生成，禁止手改。
3. 不引入外部 CDN 或运行时网络请求；页面必须离线可开。
4. 行为改动必须同 PR 更新对应 docs；本文件超过 80 行必须先精简。
5. 新数据源三件套缺一不可：`data/sources.yml` 条目 + `docs/sources/*.md` + 响应样本。
6. 每次工作会话结束，在 `docs/worklog.md` 追加一行：`日期 | harness | 做了什么 | 下一步`。
