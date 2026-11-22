# Token-Tracker — AI Monetization Tracker

每日自动更新的 AI 货币化仪表盘：Frontier Lab ARR 估算、Token 用量（OpenRouter / Vercel
Gateway / SDK 下载）、GPU 租赁价格、AI 数据中心建设。产物为纯静态单文件 HTML。

线上：<https://charlesliuyx.github.io/Token-Economy-Tracker/>。两条每日流水线：
GitHub Actions（22:23 UTC，抓数 + 构建 + 部署）与本机每日更新任务（Opus 5.5，
核对管道 + 更新 ARR 锚点 / 每日速读 / 观点 / 模型名单，见 `docs/daily-routine.md`）。
接续上次会话先看 [docs/worklog.md](docs/worklog.md) 末尾几行。

## 架构一句话

`scripts/fetch/*`（每源独立）→ `data/`（append-only JSON）+ `data/manual/`（人工/agent 维护）
→ `scripts/derive/arr.py` → `scripts/build.py` → `site/index.html`（单文件，Chart.js 内联）。

## 任务路由表（先读对应文档再动手）

| 你要做的事 | 先读 |
|---|---|
| 了解数据流与模块职责 | `docs/architecture.md` |
| 改某个数据源抓取 | `docs/sources/<source>.md` + `docs/sources/samples/` |
| 加 / 改面板、样式、交互 | `docs/frontend.md` + `site/template/panels/` |
| 改 ARR 估算模型、加锚点 | `docs/arr-methodology.md` |
| 每日内容更新（锚点 / 速读 / 观点 / 模型名单） | `docs/daily-routine.md` |
| 排查数据缺失 / 运维 | `docs/runbook.md` + `data/_status.json` |
| 做完一件事后发布 | `.claude/skills/ship/SKILL.md` |
| 理解历史决策 | `docs/decisions/`；立项时的方案见 `docs/PLAN.md`（历史记录） |

常用命令：`make update`（逐源抓取 + ARR 拟合）/ `make build` / `make serve` / `make test` /
`make fetch-<source>`（单源调试）。docs/ 总索引见 `docs/INDEX.md`。

## 硬约束（唯一出处：`docs/conventions.md`，此处为摘要）

1. `data/**/daily/` 历史快照不可改写（refetch 窗口内回补除外）。
2. `site/index.html` 是构建产物，只能由 `make build` 生成，禁止手改。
3. 不引入外部 CDN 或运行时网络请求；页面必须离线可开。
4. 行为改动必须同一次提交更新对应 docs；本文件超过 80 行必须先精简。
5. 新数据源三件套缺一不可：`data/sources.yml` 条目 + `docs/sources/*.md` + 响应样本。
6. 每次工作会话结束，在 `docs/worklog.md` 追加一行：`日期 | harness | 做了什么 | 下一步`。
7. 做完一件事就发布（测试绿 → 构建 → 推 main → 确认部署），只有影响很大的破坏性改动才先问人。
