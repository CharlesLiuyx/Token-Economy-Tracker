# Runbook（运维手册）

> TL;DR：make update && make build && make serve 与 CI 同路径；缺数先看 data/_status.json。
> 何时读我：数据缺失 / 面板发黄发红 / Actions 挂了。
> 最后核对日期：2026-07-12

## 日常命令

```bash
make update              # 逐源抓取（单源失败不中断，看 stderr）
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

## Actions 挂了（M5 上线后）

- workflow 连续失败 ≥2 天会自动开/更新 GitHub Issue。
- 本地救场：`make update && make build`，人工 commit `data: YYYY-MM-DD` 推上去即可，
  与 CI 产物完全等价。
