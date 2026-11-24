# 架构

> TL;DR：fetch 只写 data/，人工/agent 只写 data/manual/，build 只读 data/，产物是单文件
> site/index.html；任何一段可独立重跑。
> 何时读我：改跨模块行为、加数据源、动数据层或调度之前。
> 最后核对日期：2026-11-22

## 数据流

```
GitHub Actions daily.yml（22:23 UTC）            本机每日更新任务（Opus 5.5，docs/daily-routine.md）
  └─ make update                                   └─ 核对管道 → 搜新披露 → 改 data/manual/*.yml
       scripts/fetch/<source>.py  每源独立             arr_anchors.yml  ARR 披露锚点
       └─ data/<source>/daily/<YYYY>/<日期>.json        digest.yml       每日速读
       └─ data/<source>/latest.json                     quotes.yml       专家观点
       └─ data/_status.json                           └─ make update-arr && make build → push main
       scripts/derive/arr.py → data/derived/arr.json
  └─ make test && make build → site/index.html → commit `data: 日期` → Pages
push 到 main（deploy.yml）：只 build + 部署，不抓数、不提交
```

## 模块职责

- `scripts/lib/`：`store`（信封 + append-only 写入）、`status`、`schema`（轻量断言）、
  `net`（重试 HTTP）、`registry`（sources.yml）、`runner`（fetcher 公共 main）。
- `scripts/fetch/<source>.py`：只实现 `SOURCE / fetch(cfg) / validate(payload)`，入口走
  `runner.run()`；配置一律来自 `data/sources.yml`。
- `scripts/derive/arr.py`：锚点 → 拟合 → `data/derived/arr.json`（方法见 arr-methodology.md）。
- `scripts/build.py`：读 data/ + 模板渲染单文件 HTML；唯一允许写 site/index.html 的代码。
  另把附属报告 `reports/llm-release-bench/` 里唯一的 .html 原样复制成 `site/llm-release-bench/index.html`
  （不入库，随 Pages 发布；报告自己的构建见该目录 MAINTAIN.md）。deploy.yml 的 paths 含 `reports/**`。
  「较 N 天前」的变化量都在这里由每日快照现算（`series_delta`），不落盘。

## 关键机制

- **信封**：每个快照 `{schema_version, source, snapshot_date, fetched_at, source_meta, payload}`。
- **坏数据不入库**：validate 抛 SchemaError ⇒ 不写文件，latest 保持上次成功值，_status 记错误。
- **单源失败不中断**：Makefile `update` 每行以 `-` 开头；页面用新鲜度徽章让缺数可见。
- **refetch 窗口**：窗口内（`refetch_window_days`，默认 3 天）允许覆盖同名快照回补修订；
  窗口外改写抛 `ImmutableSnapshotError`。回补旧日期不会回滚 latest.json。
- **新鲜度**：build 由 `_status.json` 算 ok / warn(>48h) / stale(>7d)；人工维护源以最近一条
  每日速读的日期为准（>2 天 warn，>7 天 stale）。
- **两条部署通路共用 `pages-deploy` 锁**：daily.yml 的 deploy 失败时自动 dispatch deploy.yml
  兜底（细节与排障见 runbook.md）。两条通路都把上传 Pages artifact 和 deploy-pages 分在两个 job，
  避免同一 job 里部署查不到刚上传的 artifact。

## 运行方式

统一从仓库根 `python -m scripts.fetch.<source>`（Makefile 已封装）。本地与 CI 完全同路径。
