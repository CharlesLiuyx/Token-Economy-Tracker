# 架构

> TL;DR：fetch 只写 data/，build 只读 data/，产物是单文件 site/index.html；任何一半可独立重跑。
> 何时读我：改跨模块行为、加数据源、动数据层之前。
> 最后核对日期：2026-07-12

## 数据流

```
GitHub Actions (每日 cron)
  └─ make update    scripts/fetch/<source>.py  每源独立、单源失败不中断（Makefile 行首 -）
       └─ data/<source>/daily/<YYYY>/<YYYY-MM-DD>.json   append-only 快照
       └─ data/<source>/latest.json                       最近一次成功结果
       └─ data/_status.json                               每源 last_success/last_attempt/error
  └─ make build     scripts/build.py
       └─ site/index.html   模板 + 内联 CSS/JS/数据，离线可开
```

## 模块职责

- `scripts/lib/`：共享层。`store`（信封+append-only 写入）、`status`、`schema`（轻量断言）、
  `net`（重试 HTTP）、`registry`（sources.yml）、`runner`（fetcher 公共 main）。
- `scripts/fetch/<source>.py`：每源一个，只实现 `SOURCE / fetch(cfg) / validate(payload)`，
  入口统一走 `runner.run()`。配置一律来自 `data/sources.yml`，不硬编码。
- `scripts/derive/arr.py`（M3）：锚点拟合，独立于 fetch。
- `scripts/build.py`：读 data/ + 模板，渲染单文件 HTML；唯一允许写 site/index.html 的代码。

## 关键机制

- **信封**：每个快照 `{schema_version, source, snapshot_date, fetched_at, source_meta, payload}`。
- **坏数据不入库**：validate 抛 SchemaError ⇒ 不写文件，latest 保持上次成功值，_status 记错误。
- **refetch 窗口**：窗口内（默认 3 天）允许覆盖同名快照回补修订；窗口外改写抛
  `ImmutableSnapshotError`（见 `scripts/lib/store.py`）。
- **latest 不回滚**：回补旧日期不会把 latest.json 覆盖成旧数据。
- **新鲜度**：build 由 `_status.json` 算 ok / warn(>48h) / stale(>7d)，渲染面板徽章。

## 运行方式

统一从仓库根 `python -m scripts.fetch.<source>`（Makefile 已封装）；模块内部有 sys.path
兜底，直接 `python scripts/fetch/x.py` 也可。本地与 CI 完全同路径。
