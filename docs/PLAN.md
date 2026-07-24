# AI Monetization Tracker — 实施方案

> TL;DR：静态单文件 HTML 仪表盘 + Python 数据管道 + GitHub Actions 每日定时抓取。
> 数据按源分目录、append-only 存 JSON；构建时把展示数据内联进 `site/index.html`。
> 全仓库按「渐进式披露」组织文档，供 Cursor / Claude Code / Codex 多 harness 接力迭代。
>
> 状态：方案已定稿（含 Review），尚未实施。从里程碑 M0 开始。
> 本文档是实施期间的最高上下文，实施完成后其内容将拆解进 docs/ 并瘦身为历史记录。

---

## 1. 目标

复刻并每日自动更新参考图中的「AI MONETIZATION TRACKER」仪表盘，四大板块：

1. **Frontier Lab ARR 实时估算** — Anthropic / OpenAI 的 ARR 估算大数字（页面上实时跳动）、
   历史披露锚点 + 拟合曲线 + 外推虚线 + 置信带走势图。
2. **Token 需求与采用度** — OpenRouter 模型 token 用量（单模型、重点模型对比、全网总量、
   Top Models 周榜）、Vercel AI Gateway 份额（Token / $ Spend Top 10 + 走势）、
   SDK 下载量（npm/pypi）、专家观点摘录、Epoch Top Sites 表格。
3. **GPU 租赁价格** — H100/H200/B200/A100/RTX 5090 的 $/GPU-hr 卡片 + 价格趋势图。
4. **AI 数据中心建设** — Epoch AI 数据集汇总卡片（站点数 / IT Power GW / H100-eq）、
   行业累计增长图、每日新闻流（含高亮条目）。

非目标（明确不做）：用户系统 / 登录、后端服务、实时（分钟级）数据、付费数据源。

## 2. 总体架构

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐
│ GitHub       │   │ scripts/fetch │   │ data/          │   │ scripts/      │
│ Actions cron │──▶│ 每源一个脚本   │──▶│ append-only    │──▶│ build.py      │
│ (每日 1 次)  │   │ 互相独立、可单跑│   │ JSON + YAML    │   │ 渲染单文件 HTML│
└─────────────┘   └──────────────┘   └───────────────┘   └──────┬───────┘
                                                                 ▼
                                              site/index.html（GitHub Pages / 本地双击）
```

核心原则：

- **数据与展示分离**：fetch 只写 `data/`，build 只读 `data/`。任何一半都能独立重跑。
- **每个数据源独立失败**：单源挂掉不影响整次运行；页面显示各面板的数据新鲜度徽章。
- **历史全量入库**：每日快照 append-only，永不改写历史文件 → 任何时候可全量重绘。
- **零服务器**：产物是纯静态单文件，GitHub Pages 托管，也可本地直接打开。

技术栈：Python 3.12（`requests` + `pyyaml` + `numpy`(拟合) + `jinja2`(模板)，刻意保持最小）；
前端 vanilla JS + 构建时内联的 Chart.js（vendored，无 CDN）。
选 Python + Chart.js 的一个显式理由是 **AI 友好**：所有主流模型对这两者的 API 掌握最深，
跨 harness 迭代时幻觉率最低。

## 3. 仓库结构

```
Token-Tracker/
├── AGENTS.md                  # L0 入口（Codex / Cursor 原生读取），≤80 行，含任务路由表
├── CLAUDE.md                  # 仅一行 @AGENTS.md（Claude Code 读取）
├── PLAN.md                    # 本文档
├── Makefile                   # update / build / serve / test / fetch-<source>
├── requirements.txt
├── .github/workflows/daily.yml
├── scripts/
│   ├── fetch/
│   │   ├── openrouter.py      # 模型 token 用量 + rankings
│   │   ├── vercel_gateway.py  # AI Gateway 排行榜
│   │   ├── sdk_downloads.py   # npm + pypi 下载量
│   │   ├── epoch_datacenters.py  # Epoch AI 数据中心数据集
│   │   ├── gpu_prices.py      # GPU 租赁价格指数
│   │   └── news.py            # 数据中心新闻 RSS
│   ├── derive/
│   │   └── arr.py             # 锚点拟合 → ARR 曲线 + 实时外推参数
│   ├── build.py               # data/ → site/index.html
│   └── lib/                   # 共享：http 重试、schema 校验、status 记录
├── data/
│   ├── sources.yml            # ★ 机器可读源注册表（见 §5）
│   ├── _status.json           # 每次运行写：各源 last_success / last_error
│   ├── openrouter/
│   │   ├── daily/2026/2026-07-09.json
│   │   └── latest.json
│   ├── vercel_gateway/…       # 同构
│   ├── sdk_downloads/…
│   ├── epoch/…
│   ├── gpu_prices/…
│   ├── news/…
│   └── manual/                # 手工维护的数据（git 即编辑界面）
│       ├── arr_anchors.yml    # ARR 披露锚点
│       └── quotes.yml         # 专家观点面板
├── site/
│   ├── index.html             # 构建产物（提交入库，Pages 直接服务）
│   ├── template/
│   │   ├── index.html.j2      # 页面骨架
│   │   ├── panels/*.j2        # 每个面板一个模板片段
│   │   ├── style.css          # Linear 风格主题（dark/light 双主题 token）
│   │   └── app.js             # 图表渲染 wrapper + ARR 跳动计数器
│   └── vendor/chart.umd.min.js
└── docs/
    ├── INDEX.md               # L1 索引：一句话 + 何时读
    ├── architecture.md
    ├── conventions.md         # 硬约束（含文档维护规则）
    ├── runbook.md             # 运维：如何手跑、如何补数据、如何救 Actions
    ├── arr-methodology.md
    ├── frontend.md
    ├── worklog.md             # 跨 harness 接力日志（append-only）
    ├── decisions/             # ADR-001-chartjs.md 等
    └── sources/
        ├── openrouter.md      # 每源一篇：endpoint、字段、口径、坑
        ├── …
        └── samples/*.json     # 截断后的真实响应样本（L2）
```

## 4. 面板 → 数据源映射（含风险评级）

| # | 面板 | 数据源 | 获取方式 | 更新频率 | 风险 |
|---|------|--------|---------|---------|------|
| 1a | Anthropic / OpenAI ARR 大数字（实时跳动） | `data/manual/arr_anchors.yml`（手工锚点）+ 拟合 | derive/arr.py，前端 JS 按小时速率外推 | 锚点：有新披露时手工加；拟合：每日 | 低（自有模型） |
| 1b | ARR 走势图（锚点/拟合/外推/置信带） | 同上 | build 时预算好序列 | 每日 | 低 |
| 2a | Claude Fable 5 每日 Token | OpenRouter | 非官方 rankings/stats 端点（M2 探测确认） | 每日 | **高** |
| 2b | 重点模型发布对比（fable 5 / sonnet / gpt-5 / gemini 3 / deepseek / grok） | OpenRouter | 同上，按模型 slug 列表（配置在 sources.yml） | 每日 | **高** |
| 2c | OpenRouter 全网 Token 总量（daily + 7DMA） | OpenRouter | 同上 | 每日 | **高** |
| 2d | Top Models 最新一周合计（横条） | OpenRouter rankings | 同上 | 每日 | **高** |
| 2e | Vercel Gateway Token 份额 Top 10 (7d) | vercel.com/ai-gateway 排行榜 | 非官方（页面内嵌 JSON / __NEXT_DATA__，M2 探测） | 每日 | **高** |
| 2f | Vercel Gateway $ Spend 份额 Top 10 (7d) | 同上 | 同上 | 每日 | **高** |
| 2g | Vercel Gateway 全模型走势（Token vs $） | 同上（历史靠我们自己每日快照累积） | 同上 | 每日 | **高** |
| 2h | 专家观点 / Podcast 摘录 | `data/manual/quotes.yml` | 手工维护（AI 辅助整理） | 不定期 | 低 |
| 2i | SDK 下载量（openai / anthropic / google-genai × npm+pypi） | api.npmjs.org + pypistats.org | **官方 API** | 每日 | 低 |
| 2j | Top Sites by IT Power 表格 | Epoch AI Frontier Data Centers 数据集（CSV，CC-BY） | **官方下载** | 每日拉，源头约每周更 | 低 |
| 3a | GPU 价格卡片 ×5 + 趋势图 | 图中标注 “OCPI” 指数，待确认；候选：United Compute GPU Price Index / Vast.ai API / Shadeform | M2 做 source discovery，选 1 主 1 备 | 每日 | 中 |
| 4a | 数据中心汇总卡片（67 sites / 10.8 GW / 10.2M H100-eq） | Epoch 数据集聚合 | 本地聚合计算 | 每日 | 低 |
| 4b | 行业累计增长图（MW + 站点数） | Epoch 数据集（按投运时间累计） | 本地聚合计算 | 每日 | 低 |
| 4c | 相关动态新闻流 | Google News RSS 定向查询 + 源域名白名单 | RSS 解析，仅存 标题/链接/来源/日期，URL 去重 | 每日 | 中 |

口径警示（必须在页面 Methodology 区写明）：OpenRouter / Vercel Gateway 只是全市场的
**切片**（聚合路由平台，不含各 lab 直连 API 流量），面板标题保留来源后缀（如图中做法），
不得暗示为全市场数据。

## 5. 数据层设计

### sources.yml（单一事实来源）

每个源一条记录，fetcher、文档、状态页都从这里读元数据：

```yaml
openrouter:
  fetcher: scripts/fetch/openrouter.py
  doc: docs/sources/openrouter.md
  schedule: daily
  kind: unofficial-api        # official-api | unofficial-api | scrape | manual
  refetch_window_days: 3      # 每次回补最近 N 天（源头数字会修订）
  models_tracked: [anthropic/claude-fable-5, openai/gpt-5, google/gemini-3, …]
```

### 存储约定

- `data/<source>/daily/<YYYY>/<YYYY-MM-DD>.json`：当日快照，**写后不改**
  （在 refetch_window 内允许覆盖同名文件回补修订，窗口外禁改）。
- `data/<source>/latest.json`：最近一次成功结果 + `fetched_at`，build 的主要输入。
- 每个快照顶层带信封：`{schema_version, fetched_at, source_meta, payload}`。
- fetcher 内置轻量 schema 断言（关键字段存在性 + 类型），校验失败视为抓取失败，
  **不写入**坏数据，保留上次 latest。
- `data/_status.json`：每次运行重写，`{source: {last_success, last_attempt, error}}`，
  build 读它生成页面上每个面板的「数据截至 xx-xx」徽章与 stale 警告（>48h 变黄，>7d 变红）。

## 6. ARR 估算模型（docs/arr-methodology.md 的骨架）

1. **锚点**（`arr_anchors.yml`）：每条记录 `company / date / value_usd / metric
   (run_rate_arr | projected_rev | reported_rev) / source_url / note`。
   口径字段**必填**——媒体报道混用 run-rate 与年度预测，混拟合会出鬼图。
2. **拟合**：对每家公司，取 run_rate_arr 锚点在对数空间做加权最小二乘
   （近期锚点权重高）。曲线形态不预设：`linear` / `exponential` / `log_quadratic`
   三种候选各拟合一次，用滚动起点回测（前 i 个点预测第 i+1 个）挑预测最准的。
3. **外推**：延伸至今日 + 未来 N 月（虚线区），沿用最后锚点处的瞬时增速做直线延伸，
   曲率不外推；置信带为预测区间，随外推距离张开，早期无支撑段不画。
4. **实时跳动**：build 输出 `{arr_at_build, build_ts, usd_per_hour, mom_implied}`；
   前端 `setInterval` 每秒累加 `usd_per_hour/3600`。纯展示效果，刷新页面即回到 build 基准。
5. 卡片角标：implied MoM %、每小时增量、**选中形态**、最近披露日期。

## 7. 前端设计

- **单文件产物**：CSS、app.js、Chart.js（vendored min）、当日数据 JSON 全部内联，
  `<script id="dashboard-data" type="application/json">`。无任何外部请求，离线可开。
- **体积控制**：页面只内联展示所需数据——日频序列保留近 90 天，更早自动降采样为周频；
  全量历史留在 `data/`，不进 HTML。目标 gzip 后 < 600KB。
- **图表**：统一走 `renderPanel(id, spec)` 薄封装（约束 Chart.js 用法的子集：line / bar /
  horizontalBar / area + tooltip），方便日后整体换库。样式统一注入 Linear 风格主题
  （中性色 / 1px 细边框 / mono 数字，dark/light 双主题切换，详见 docs/frontend.md）。
- **面板模板化**：每个面板一个 `panels/*.j2` 片段 + 一个 spec 生成函数，加减面板不动骨架。
- **交互**：Chart.js 自带 hover tooltip 与 legend 开关即可满足参考图的交互；不做缩放/刷选。

## 8. 调度与运维

- **GitHub Actions**（`daily.yml`）：cron 每日 00:30 UTC（北京 08:30 前出数）。
  步骤：checkout → `make update`（逐源 fetch，单源失败不中断）→ `make build` →
  commit `data: YYYY-MM-DD` → push → Pages 部署。
- **push 即部署**（`deploy.yml`）：push 到 main 且改动了 `site/**` / `scripts/**` /
  `data/**` / `requirements.txt` 时，单独跑 `make build` → Pages 部署。**只构建不提交、
  不抓数**，因此不会被 daily.yml 的 bot push 触发成循环。两个 workflow 共用
  `pages-deploy` concurrency 锁，避免同时部署冲突。
- **失败可见**：任一源连续失败 ≥2 天时，workflow 自动开/更新一个 GitHub Issue（带错误摘要）。
- **本地等价**：`make update && make build && make serve`，与 CI 完全同路径；
  `make fetch-openrouter` 可单跑一源调试。
- **补数据**：runbook 写明如何用 `--date` 参数回补历史（受 refetch_window 约束）。

## 9. AI 友好工程 & 渐进式披露

目标：任何 harness（Cursor / Claude Code / Codex）冷启动时，用最少 token 拿到刚好够用的
上下文，需要更深时**按路标自取**。

### 三层披露

- **L0 — `AGENTS.md`（≤80 行，永远被加载）**：项目一句话、目录地图（一行一条）、
  任务路由表、硬约束清单。CLAUDE.md 内容仅为 `@AGENTS.md`（Claude Code 的 import 语法），
  Codex 与 Cursor 直接读 AGENTS.md ——**一份内容，三个 harness**。
  路由表形如：

  | 你要做的事 | 先读 |
  |---|---|
  | 改某个数据源抓取 | `docs/sources/<source>.md` + 其 samples |
  | 加/改面板 | `docs/frontend.md` + `site/template/panels/` |
  | 改 ARR 模型 | `docs/arr-methodology.md` |
  | 排查数据缺失 | `docs/runbook.md` + `data/_status.json` |
  | 理解某个历史决策 | `docs/decisions/` |

- **L1 — `docs/*.md`（按需读）**：每篇开头固定三行头注：`TL;DR`（一句话）、
  `何时读我`、`最后核对日期`。超过 ~150 行必须拆分。
- **L2 — 样本与注册表（按需读，机器可读优先）**：`data/sources.yml`、
  `docs/sources/samples/*.json`（截断的真实响应）、schema 断言代码本身。

### 硬约束（写入 conventions.md，同时列在 AGENTS.md）

1. 历史快照文件不可改写（refetch 窗口除外）。
2. `site/index.html` 是构建产物，只能由 `make build` 生成，禁止手改。
3. 不引入外部 CDN / 运行时网络请求。
4. 改了行为必须同 PR 更新对应 docs；AGENTS.md 超 80 行必须先精简再合并。
5. 新数据源必须齐三件套：sources.yml 条目 + docs/sources/*.md + samples。

### 跨 harness 接力

- `docs/worklog.md`：append-only，每次工作会话结束追加一行
  `日期 | harness | 做了什么 | 下一步/坑`。这是不同工具间唯一的「会话记忆」通道。
- ADR：凡是「换库/换源/换口径」级别的决定写一篇 `docs/decisions/ADR-NNN-*.md`
  （背景/决定/后果，各 ≤5 行），避免后续 harness 反复重议。

## 10. 里程碑

| 阶段 | 内容 | 验收标准 | 预估 |
|---|---|---|---|
| M0 | 脚手架：目录、Makefile、AGENTS.md/CLAUDE.md、docs 骨架、conventions | `make test` 可跑；三个 harness 冷启动均能自述项目 | 0.5d |
| M1 | 低风险官方源：Epoch 数据中心、SDK 下载、新闻 RSS + 数据层/status 机制 | 三源 latest.json 落盘、_status 正确、样本入库 | 1d |
| M2 | 高风险源探测：OpenRouter、Vercel Gateway、GPU 价格 source discovery（各写 ADR） | 每源要么打通、要么记录结论与备选；坑写进 docs/sources | 1–1.5d |
| M3 | ARR：anchors 收集（近两年公开披露）、拟合与外推、单测 | 拟合曲线过锚点、MoM 合理、异常口径被拒绝 | 0.5d |
| M4 | 前端：模板、主题、全部面板、实时计数器、新鲜度徽章 | 本地双击打开与参考图布局对齐、离线可用 | 1d |
| M5 | 上线：Actions、Pages、失败告警 Issue、runbook 完稿 | 连续 3 天自动更新成功 | 0.5d |

依赖关系：M1 与 M3 可并行；M4 依赖 M1–M3 的数据形状定型；M2 的结论可能回改 §4 映射表。

---

## 11. Review（自评）

### 风险与缓解

1. **非官方端点脆弱（最大风险）**：OpenRouter rankings 与 Vercel Gateway 排行榜都没有
   公开承诺的 API，随时可能改结构或加反爬。
   缓解：fetcher 强 schema 校验，坏数据不入库；页面 stale 徽章让腐烂可见；每源保留
   「页面内嵌 JSON 解析」与「无头浏览器」两级 fallback 的探测记录（ADR）；②区面板设计上
   允许任一子面板独立降级为「显示最后成功数据 + 警告」。**接受残余风险**：这两个源
   断供时该区数据会冻结，但不会拖垮整页。
2. **ARR 伪精度**：$66,457,473,442 精确到个位纯属演出效果，本质是拟合外推。
   缓解：卡片常驻「估算」徽章 + methodology 锚链接；走势图必须画置信带与锚点散点，
   让读者看到估算的地基；anchors 口径字段必填并在拟合时按口径过滤。
3. **口径偏差被误读**：OpenRouter/Vercel 是路由平台切片，Claude/GPT 的主力流量走直连，
   不在其中；SDK 下载量也只是 proxy。
   缓解：每个面板标题保留来源后缀；Methodology 区逐面板写清「这测的是什么、不是什么」。
4. **GPU 价格源不明**：图中 “OCPI” 无法直接确认对应哪家。
   缓解：M2 专项 discovery（候选 United Compute / Vast.ai / Shadeform），选定后写 ADR；
   在此之前 ③ 区排最后实现。
5. **仓库随时间膨胀**：每日 JSON 提交，两年 ≈ 数千个小文件。
   量级评估后可接受（每源每天几 KB～几十 KB）；按年份分目录；若将来超 500MB 再考虑
   合并为按月文件（预留 ADR 决策点，现在不过度设计）。
6. **新闻面板的翻译问题**：参考图中新闻标题是中文摘要，而 RSS 原文多为英文。
   决定：v1 直接展示原文标题（零依赖、零成本）；「LLM 每日中文摘要」列为可选增强
   （需要引入 API key 与额度管理，成本与收益在实施时再评估）。
7. **Actions 静默失败**：cron 任务坏掉常常没人发现。
   缓解：连续失败自动开 Issue + 页面 stale 徽章双保险；runbook 写清手动救场步骤。
8. **文档漂移（渐进式披露的维护成本）**：docs 不更新比没有 docs 更毒。
   缓解：conventions 硬约束「行为改动同 PR 改 docs」+ 每篇 docs 带「最后核对日期」头注；
   worklog 只追加不整理，降低维护摩擦。
9. **数据修订**：OpenRouter 当日数字次日常被修正。
   缓解：refetch_window_days=3，每次运行回补近 3 天，图表以回补后为准。

### 定稿的关键取舍（已决策，后续 harness 勿重议，详见未来 ADR）

- **Python 而非 Node** 做管道：数据处理生态 + 无 node_modules 噪音。
- **Chart.js 内联而非自绘 SVG**：换取 tooltip/legend 交互与 AI 熟悉度，代价 ~200KB。
- **单文件 HTML 而非多页应用**：分发与托管最简，代价是体积上限 → 用降采样守住。
- **锚点手工维护而非自动爬**：ARR 披露是低频高价值信息，人工录入质量远高于爬虫。
- **构建产物入库**：违背常规工程洁癖，但让 Pages 零配置、且任何历史时刻的页面可考古。

### 开放问题（不阻塞 M0–M1）

- ~~“OCPI” 究竟对应哪个指数~~ M2 已解决：Ornn Compute Price Index，无公开 API，
  改用 Vast.ai 市场 API（ADR-004）。
- ~~OpenRouter 历史 token 数据能否一次性回填~~ M2 已解决：周频主图有 52 周历史；
  每模型日频不存在，从快照之日起以滚动 7 天口径累积（ADR-002）。
- 新闻中文摘要是否值得引入 LLM 步骤（v1 不做）。
- 专家观点面板的收录标准（先手工少量高质量，形成手感后再定标准）。
