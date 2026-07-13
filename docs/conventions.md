# 约定与硬约束

> TL;DR：append-only 数据、单文件产物、禁 CDN、docs 与行为同 PR 更新、新源三件套。
> 何时读我：动手写代码前；Review 别人（或 AI）的 PR 时。
> 最后核对日期：2026-07-13

## 硬约束（违反即打回）

1. `data/**/daily/` 历史快照不可改写；仅 refetch 窗口（sources.yml `refetch_window_days`）
   内允许覆盖回补。窗口外新建缺失日期文件允许（数据修复），改写既有文件禁止。
2. `site/index.html` 是构建产物，只能由 `make build` 生成，禁止手改。
3. 不引入外部 CDN 或运行时网络请求；页面必须离线可开（Chart.js vendored 到 site/vendor/）。
4. 行为改动必须同 PR 更新对应 docs；AGENTS.md 超 80 行必须先精简再合并。
5. 新数据源三件套缺一不可：`data/sources.yml` 条目 + `docs/sources/<source>.md` +
   `docs/sources/samples/` 响应样本（tests/test_registry.py 会检查前两件）。
6. 每次工作会话结束在 `docs/worklog.md` 追加一行。

## 代码约定

- fetcher 只实现 `SOURCE / fetch(cfg) / validate(payload)`；入口、--date、状态上报走
  `scripts/lib/runner.py`。配置（endpoint/包列表/查询词）放 sources.yml，不硬编码。
- HTTP 一律走 `scripts/lib/net.py`（UA/超时/重试统一）。
- validate 宁严勿松：关键字段缺失、数量异常（如行数骤减）都应抛 SchemaError——
  坏数据不入库比面板缺数更重要。
- 依赖保持最小：requests / pyyaml / numpy / jinja2 / pytest，加新依赖先写 ADR。

## Commit message 规范

- 格式 `<type>: <summary>`，英文祈使句，≤72 字符，句尾不加句号；type 枚举
  （feat/fix/data/docs/build/ci/refactor/test/chore）与示例以根目录 README
  的 "Commit message convention" 一节为唯一口径。
- CI 每日自动提交固定为 `data: YYYY-MM-DD`。

## 文档约定（渐进式披露）

- L0 `AGENTS.md` ≤80 行；L1 `docs/*.md` 每篇开头三行头注（TL;DR / 何时读我 / 最后核对日期），
  超 ~150 行必须拆分；L2 是 samples 与 sources.yml，机器可读优先。
- 「换库/换源/换口径」级决策写 `docs/decisions/ADR-NNN-*.md`（背景/决定/后果，各 ≤5 行）。
- worklog 只追加不整理。
