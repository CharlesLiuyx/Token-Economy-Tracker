# docs/ 索引（L1）

> TL;DR：一句话导航到正确文档。每个主题只有一篇是唯一出处，其余文档只链接不复述。
> 何时读我：不确定该读哪篇时。
> 最后核对日期：2026-11-22

| 文档 | 唯一出处：什么 | 何时读 |
|---|---|---|
| [architecture.md](architecture.md) | 数据流、模块职责、存储机制、调度 | 改跨模块行为前 |
| [conventions.md](conventions.md) | 硬约束、代码 / 提交 / 文档规则、发布规则 | 动手写代码前 |
| [frontend.md](frontend.md) | 页面外壳、面板与图表约定、i18n、术语、性能 | 加/改面板前 |
| [arr-methodology.md](arr-methodology.md) | ARR 锚点口径→拟合→外推的方法 | 改 ARR 模型、加锚点前 |
| [daily-routine.md](daily-routine.md) | 每日更新任务做什么、收录门槛 | 改定时任务、手动跑一次更新时 |
| [runbook.md](runbook.md) | 手跑、回补数据、救 Actions | 排查数据缺失时 |
| [sources/](sources/) | 每个数据源一篇：endpoint / 字段 / 口径 / 坑 | 改任何 fetcher 前 |
| sources/samples/ | 截断的真实响应样本（L2） | 写解析 / 调 schema 时 |
| [decisions/](decisions/) | ADR：已定决策，勿重议 | 想换库 / 换源 / 换口径时 |
| [worklog.md](worklog.md) | 跨 harness 接力日志（append-only） | 每次会话开始 / 结束 |
| [PLAN.md](PLAN.md) | 立项方案的历史记录（目标、面板映射、取舍） | 想知道「当初为什么这么定」时 |
| [../reports/llm-release-bench/MAINTAIN.md](../reports/llm-release-bench/MAINTAIN.md) | 独立子目录：「大模型发布和 Bench 跟进」中英双语报告与它的构建脚本（不参与 make build / test / daily.yml） | 改这份报告前 |
