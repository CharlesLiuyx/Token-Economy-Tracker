# 每日更新任务

> TL;DR：每天一轮——先保证管道健康，再给页面带来「今天才知道的」增量：新的收入披露、
> 每日速读、观点、模型名单换代。做完直接发布。
> 何时读我：你是每日定时任务（`token-tracker-daily-patrol`，Opus 5.5）；或要手动跑一次内容更新；
> 或要改这个流程（改这里，任务提示只是一句「读本文并照做」）。
> 最后核对日期：2026-11-22

目标只有一个：**读者每天打开页面都能看到新东西，而且每个数字都经得起核对。**
宁可少写一条，不写一条核对不了的。

## 第 1 步：管道健康（没问题就不产生提交）

1. `git checkout main && git pull`。
2. `gh run list --workflow=daily.yml --limit 5`；最新一次失败就 `gh run view <id> --log-failed`。
3. 读 `data/_status.json`：哪个源 `error` 非空或 `last_success` 落后今天。
4. `gh issue list --label pipeline-failure`。

发现问题按 [runbook.md](runbook.md) 处理，逐级升级直到修好：单源重跑回补 → 对照
`docs/sources/<source>.md` 与样本适配上游变化 → 探测替代通路（新通路要补三件套）→ 修
workflow。只有上游关停、强制付费或需要人类凭据时才停手，并在 Issue 里写清已试过什么。

## 第 2 步：ARR 披露（每天都搜）

页面上 ARR 卡片的「距最近披露 N 天」超过 45 天就是在提醒这一步没做好。

1. 用 WebSearch 搜两家公司最近 14 天的收入披露：`Anthropic run-rate revenue`、
   `OpenAI annualized revenue`，加上 Bloomberg / The Information / Reuters / FT / CNBC / WSJ
   与 SEC 文件（Anthropic 已上市，10-Q / 8-K / 财报新闻稿是一手来源）。
2. 找到新数字就追加到 `data/manual/arr_anchors.yml`。口径四选一，**不能混**：
   `run_rate_arr`（年化运行率，唯一进入拟合的口径）/ `third_party_est` / `projected_rev` /
   `reported_rev`。`date` 写数字对应的时点而不是报道日期；`note` 写清口径细节与推导，含中文时同时给 `note_en`；
   `confidence`：公司一手 `confident`，媒体引述知情人士 `likely`。
3. 打不开原文、只有二手转述、或口径说不清的，不收为锚点（可以写进速读并注明）。
4. `make update-arr`，看输出里 `fitted_at_last_anchor` 与披露值的差距、MoM 是否合理；
   异常就读 [arr-methodology.md](arr-methodology.md)，不要手调参数。

## 第 3 步：每日速读（`data/manual/digest.yml`）

追加当天条目，3–6 条，每条 `tag`（ARR / Token / GPU / DC / Quote / Model）+ `text.zh` 与
`text.en`（各一两句，带具体数字和时点，**两种语言都必填**，英文里不得夹中文）+ `source_url`（必填）。素材来源：

- 第 2 步找到的新披露；两家公司与大厂的财报、招股文件、官方公告。
- 页面自己的数据在动什么：看构建后「变化雷达」里 7 天 / 30 天变化最大的几行（某模型用量
  翻倍、某卡型租价跳涨、Epoch 新增站点），写成一句人话，`source_url` 用站内锚点如
  `"#p-gpu_table"`。
- 新发布的旗舰模型及其定价；有分量的算力 / 数据中心交易。

没有任何增量的日子可以只写 1–2 条数据观察，不要凑数。不改历史条目。

## 第 4 步：按需维护

- **专家观点**（`data/manual/quotes.yml`）：只收能在一手来源逐字核对的原话（财报电话会官方稿、
  官方新闻稿、有完整文字稿的访谈）；`role` 含中文时同时给 `role_en`。财报季（1 / 4 / 7 / 10 月下旬到次月）重点看。
- **重点模型名单**（`data/sources.yml` → `openrouter.models_tracked`）：同厂商出了新旗舰且旧款
  用量被反超时换代，判据与记录见 `docs/sources/openrouter.md`。
- **GPU 卡型**（`gpu_prices.gpus`）：某卡型连续多日 0 报价、或出现有 ≥10 条报价的新一代卡型时
  增删，记录见 `docs/sources/gpu_prices.md`。既有标签不可改名。

## 第 5 步：发布

有任何文件改动：`make test` 全绿 → `make build` → 按 `.claude/skills/ship/SKILL.md` 提交并
推送 main、确认部署。数据与内容分开提交（`data: YYYY-MM-DD` / `feat:` / `fix:`）。
在 `docs/worklog.md` 追加一行（`日期 | routine | 做了什么 | 下一步`，三句话以内）。

## 输出

最后给一段简短中文报告：管道状态、今天新增了哪些信息（附来源）、ARR 两家当前估算与
最近披露、遗留问题。

## 不得违反

[conventions.md](conventions.md) 的全部硬约束，尤其：历史快照不可改写；`site/index.html`
只能由 `make build` 生成；数字必须能在来源里核对到，绝不编造数字或链接。
