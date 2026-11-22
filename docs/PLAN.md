# AI Monetization Tracker — 立项方案（历史记录）

> TL;DR：2026-07 立项时的目标、面板→数据源映射与关键取舍。M0–M5 已全部完成并上线。
> 何时读我：想知道「当初为什么这么定」。**现行规则不在这里**——架构见 architecture.md，
> 约束见 conventions.md，前端见 frontend.md，ARR 方法见 arr-methodology.md，运维见 runbook.md。
> 最后核对日期：2026-11-22（由 310 行瘦身：与上述文档重复或已过时的章节全部删除，只留不重复的部分）

## 目标

每日自动更新的「AI 货币化」仪表盘，五个板块：

0. **今日要点**（2026-11 新增）—— 每日速读 + 关键指标变化雷达。
1. **Frontier Lab ARR** —— Anthropic / OpenAI 的 ARR 估算、披露锚点、拟合与外推。
2. **Token 需求与采用度** —— OpenRouter、Vercel AI Gateway、SDK 下载量、专家观点。
3. **GPU 租赁价格** —— Vast.ai 16 个卡型的报价分布与走势。
4. **AI 数据中心建设** —— Epoch AI 数据集汇总、累计增长、站点表、新闻流。

非目标：用户系统、后端服务、分钟级实时数据、付费数据源。

## 面板 → 数据源

| 板块 | 面板 | 数据源 | 源文档 | 风险 |
|---|---|---|---|---|
| 00 | 每日速读 | `data/manual/digest.yml`（每日更新任务写） | daily-routine.md | 低 |
| 00 | 变化雷达 | 各源每日快照现算 | frontend.md | 低 |
| 01 | ARR 卡片 / 轨迹图 / 披露一览 | `data/manual/arr_anchors.yml` + derive/arr.py | arr-methodology.md | 低（自有模型） |
| 02 | 重点模型 / Top Models / 周总量 | OpenRouter 非官方 frontend API | sources/openrouter.md | **高** |
| 02 | Vercel 份额条形 ×2 + 走势 | Vercel 排行榜页面 RSC 载荷 | sources/vercel_gateway.md | **高** |
| 02 | SDK 周下载 | npm + pypistats 官方 API | sources/sdk_downloads.md | 低 |
| 02 | 专家观点 | `data/manual/quotes.yml` | daily-routine.md | 低 |
| 03 | GPU 报价表 + 走势 | Vast.ai 公开市场 API | sources/gpu_prices.md | 中 |
| 04 | 汇总卡片 / 累计增长 / 站点表 | Epoch AI 数据集（CSV，CC-BY） | sources/epoch_datacenters.md | 低 |
| 04 | 新闻流 | Google News RSS + 域名白名单 | sources/news.md | 中 |

## 定稿的关键取舍（勿重议；后续变更见 decisions/）

- **Python 而非 Node** 做管道：数据处理生态 + 无 node_modules 噪音（ADR-001）。
- **Chart.js 内联**负责时序图；条形图与表格 2026-11 改为原生 DOM（ADR-006）。
- **单文件 HTML**：分发与托管最简，代价是体积上限 → 日频序列只内联近 90 天。
- **ARR 锚点人工 / agent 维护而非爬虫**：披露是低频高价值信息，逐条核对来源的质量远高于爬虫。
- **构建产物入库**：让 Pages 零配置、任何历史时刻的页面可考古。
- **数据每日提交**：两年约数千个小文件，可接受；超 500MB 再考虑按月合并。

## 已接受的残余风险

1. OpenRouter / Vercel 是非官方端点，随时可能改结构：强校验保证坏数据不入库，断供时面板冻结并标红。
2. 这两个源只是路由平台切片，不含各 lab 直连流量：面板标题保留来源后缀，Methodology 区写明。
3. ARR 大数字是拟合外推，精确到个位是展示效果：常驻「估算」徽章、可信度标注、距最近披露天数。
4. GPU 价格是 Vast.ai 低价市场切片，不等于 OCPI 或大云牌价（ADR-004）。

## 里程碑（全部完成）

M0 脚手架 → M1 官方源与数据层 → M2 高风险源探测（ADR-002/003/004）→ M3 ARR 模型 →
M4 前端 → M5 上线（2026-07）。之后的演进逐条记在 worklog.md。
