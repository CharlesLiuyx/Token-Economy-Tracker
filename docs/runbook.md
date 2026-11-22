# Runbook（运维手册）

> TL;DR：make update && make build && make serve 与 CI 同路径；缺数先看 data/_status.json。
> 何时读我：数据缺失 / 面板发黄发红 / Actions 挂了。
> 最后核对日期：2026-11-22

## 日常命令

```bash
make update              # 逐源抓取 + ARR 拟合（单源失败不中断，看 stderr）
make update-arr          # 只重跑 ARR 拟合（改了 arr_anchors.yml 之后）
make build               # data/ -> site/index.html
make serve               # http://localhost:8000 本地预览（或直接双击 site/index.html）
make test                # pytest
make fetch-news          # 单跑一个源调试（fetch-<source>）
```

## 排查数据缺失

1. 看 `data/_status.json`：哪个源 `error` 非空、`last_success` 多久之前。
2. 单跑该源 `make fetch-<source>`，读 stderr 的完整 traceback。
3. 对照 `docs/sources/<source>.md` 的「坑」小节与 `docs/sources/samples/` 判断
   是源头改结构（改解析+更新样本）还是临时故障（等下一轮 cron）。
4. SchemaError = 源头返回了结构异常的数据，属于**设计内行为**：坏数据没入库，
   latest 还是上次成功值，页面显示旧数据 + stale 徽章。

## 回补历史数据

```bash
.venv/bin/python -m scripts.fetch.sdk_downloads --date 2026-07-10
```

- 受 `refetch_window_days`（默认 3）约束：窗口外改写既有快照会抛 ImmutableSnapshotError。
- 回补旧日期不会回滚 latest.json（store 保证）。
- 注意：多数源只能取到「当前」数据，--date 回补适用于「补昨天没跑」而非「重建上月」。

## Actions 挂了

- update job 任一步失败（测试红、构建失败、push 失败）就会开 / 更新带 `pipeline-failure`
  标签的 Issue。**单源抓取失败不算**——它被容忍、不让 workflow 变红，只能从
  `data/_status.json` 和页面徽章看到；每日更新任务每天会检查并回补。
- cron 被 GitHub 调度器延迟数小时属常态（多次观察到 5 小时以上）：`gh workflow run daily.yml` 手动触发即可。
- 本地救场：`make update && make build`，人工 commit `data: YYYY-MM-DD` 推上去即可，
  与 CI 产物完全等价。
- **Pages 部署失败但数据已提交**（update job 绿、deploy-pages 红，常见报错
  `Found 0 artifact(s)`）：**不要 `gh run rerun --failed`**——重跑会再传一份同名
  artifact，deploy-pages 转报 `Multiple artifacts named github-pages`。daily.yml 已在
  deploy 失败时自动 dispatch `deploy.yml` 兜底；若兜底也没跑，手动 `gh workflow run deploy.yml`。

## 每日更新任务（内容侧）

本机定时任务 `token-tracker-daily-patrol`（Opus 5.5）每天按 [daily-routine.md](daily-routine.md)
跑一遍：核对管道、回补缺口、搜两家最新收入披露、写每日速读。任务提示本身只有一句
「读 docs/daily-routine.md 并照做」，改流程只改那篇文档。页面上 `manual` 徽章发黄
（>2 天没有新速读）说明任务没跑或没找到增量，先看任务的运行记录。
