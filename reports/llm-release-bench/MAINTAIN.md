# 大模型发布和 Bench 跟进：维护说明书

给以后每天自动维护这份报告的 Claude 看。先读完这一页再动手。

## 1. 文件在哪

以 Info 库的 `04 行业与宏观数据/大模型发布跟进和算力/` 为根（2026-11-22 从 `05 信息输入和知识类/` 移来）。
以后正式版本会搬到 GitHub 仓库 `CharlesLiuyx/Token-Economy-Tracker` 的子目录：所有脚本都只用「相对脚本所在目录」的路径，约定是**报告文件和构建目录放在同一层**（构建目录的上一级就是报告）。换位置时保持这个相对关系即可，不用改脚本。

| 路径 | 是什么 |
|---|---|
| `大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html` | 正式报告（单文件） |
| `大模型发布和Bench跟进-构建/data/models.json` | 模型、Bench 列、分数、价格、发布日、时间轴节点、表 2-2、图 3-x 配置、快照日期 |
| `大模型发布和Bench跟进-构建/data/vendors.json` | 厂商表：顺序、颜色、泳道顺序、分组（前沿 / 大厂 / 开源） |
| `大模型发布和Bench跟进-构建/build_tables.py` | 读 data/，重写报告里 `<!--data:…-->` 标记之间的内容 |
| `大模型发布和Bench跟进-构建/compute/` | 算力到卡模型（model.py → model.json → build.py），管 `<!--compute:…-->` 标记。另有说明 `compute/decisions.md` |
| `大模型发布和Bench跟进-构建/qa/` | 回归比对、演练、浏览器检查、配色校验 |
| `大模型发布和Bench跟进-构建/qa/oneoff/` | 2026-11-22 从手写 HTML 反抽数据的一次性脚本，留档，不要再跑 |
| `大模型发布和Bench跟进-构建/backup/` | 历史版本，只留最近 10 份 |

两套构建互不覆盖：

- `build_tables.py` 只改 `<!--data:NAME:start-->…<!--data:NAME:end-->`。这些块是：`vcss`（新厂商配色）、`topbar`（顶栏快照日期）、`meta`（首屏「快照｜N 个已发布模型」）、`t21hints`、`t21`、`f21lanes`（图 2-1 模型泳道）、`f21axis`（图 2-1 底部刻度和「快照」标签）、`t22hints`、`t22`、`f31`、`f32`、`f33`、`appendix`（附录「核对方式」）。
- `compute/build.py` 只改 `<!--compute:…-->`：图 2-1 的顶部刻度、三条算力泳道、2.3 节、图 2-2 / 2-3、表 2-3、算力来源和术语。
- 其余内容是手写的：第 1 章结论、第 4 章「怎么读这些数」、附录来源列表、各节标题和正文。**手写部分要人工改。**

## 2. 每次改完必须跑的命令

在 device_bash 里（路径带空格和 &，整段加引号）：

```bash
cd "$HOME/mnt/Info Input & Process/04 行业与宏观数据/大模型发布跟进和算力/大模型发布和Bench跟进-构建"
R="../大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html"
cp -p "$R" "backup/v-$(date +%F)-$(date +%H%M).html"     # 1 先备份
python3 build_tables.py                                  # 2 数据 → 表 / 图（看「提示：」行）
python3 compute/build.py                                 # 3 算力块（没改算力数据时应输出 unchanged）
python3 build_tables.py && python3 compute/build.py      # 4 再跑一遍，两个都必须输出 unchanged（幂等）
python3 qa/diff_check.py "backup/<刚才的备份>.html" "$R" # 5 列出这次改动，逐条确认都是你想改的
```

然后做浏览器检查（VM 里没有 Chromium）：用 device_stage_files 把报告和 `qa/browser_check.py` 拿到容器里，跑
`python3 browser_check.py 报告.html 截图目录 /usr/bin/google-chrome`，要求 `errors` 为空、`sticky_align_maxdx` 为 0、表 2-1 行列数符合预期，并亲眼看 t21 / f21 / f31 截图。

改了厂商颜色时，还要在容器里跑 `python3 qa/palette_check.py <dataviz 的 scripts 目录>`，结果写在 `qa/palette_report.txt`。

依赖：`build_tables.py`、`qa/diff_check.py`、`qa/rehearsal.py` 只用 Python 3 标准库（VM 里是 3.10，已实测）。`qa/browser_check.py` 需要 playwright＋Chromium，`qa/palette_check.py` 需要 Skill dataviz 的 `validate_palette.py`，`qa/oneoff/` 需要 beautifulsoup4，见 `qa/requirements.txt`。

`build_tables.py --check` 只校验不写盘；`--data 目录` 可以指向一份副本数据（演练用）。

## 3. 数据字段

所有面向读者的文字都是 `{"zh": "…", "en": "…"}`（见第 9 节）。数字、日期、价格、品牌名、模型名是普通值。

### models.json

| 字段 | 说明 |
|---|---|
| `meta.snapshot` | 快照日期 `YYYY-MM-DD`。顶栏、首屏、图 3-1 来源提示、附录「核对方式」、图 2-1 模型泳道的快照竖线和底部「M/D 快照」都从这里来 |
| `meta.title` / `meta_prefix` / `appendix_hints` | 顶栏标题、首屏前缀、附录提示（`{snapshot}` 会被替换） |
| `timeline.t0` / `span_days` | 图 2-1 横轴起点与天数。**必须和 compute/build.py 的 `T0, SPAN` 一致** |
| `layout.t21` / `layout.t22` | 列宽（em）。原值是浏览器实测的；新列沿用同组宽度。脚本估算放不下时会打印提示，这时调大这里的值 |
| `t21.groups` | 表 2-1 的分组表头：`key`（basic / indep / general / cyber / life）、`label`、`short`（「怎么读」提示里用）、`tip` |
| `t21.basic` | 发布 / 输入 / 输出三列的表头文字与提示（`{max}`＝公开模型最高价） |
| `t21.hints` | 表上方的提示。可用占位：`{n_bench}` `{n_groups_zh}` `{group_names}` `{price_in_max}` `{price_out_max}` |
| `benches[]` | 每个 Bench 一列，顺序＝列序。`key`（英文短键，全表唯一）、`label`（表头短名）、`name`（格子提示开头用的全名）、`unit`（`%`、` 个`、空）、`group`、`direction`（`higher` 越高越好 / `lower`）、`bar`（`auto` / `zero` / `minmax`，见 build_tables.py 开头的规则）、`desc`（表头提示；脚本会自动接上「有分数的模型：N 个。」） |
| `models[]` | 每个模型一行。`id`、`name`（全名，图 3-1/3-2 用）、`short`（图 3-3 用的短名）、`vendor`（vendors.json 的 key）、`status`（`public` / `restricted` / `internal`）、`tag`（受限或内部代号小标：`text`、`tip`）、`release`（对外可用日）、`release_star` + `release_tip`（先宣布后开放时）、`trained`（内部代号模型：`label`、`tip`、`end`）、`price`（`in`、`out`、可选 `in_next` / `out_next` 调价后价格、`tip`）、`scores`、`blank` |
| `models[].scores.<bench>` | `d` 显示文本（照来源写，保留来源的小数位）、`v` 数值（排名和色条用；可以比 `d` 更精确，如 VCT 0.618）、`note`（格子提示里「名次」之后的全部文字：出处＋测试条件）、`src`（出处类型）、`cf`（可信度 高 / 中 / 低） |
| `models[].blank.<bench>` | 没有分数但要写说明的格子：`d`（如「同上」「—」）、`tip` |
| `timeline_events[]` | 图 2-1 模型泳道的节点：`lane`、`date`、可选 `end`（区间节点，如内部代号训练期）、`hollow`（空心＝只是宣布）、`label`、`tag`（受限）、`tip`（脚本自动在前面加「YYYY-MM-DD：」，区间节点不加） |
| `t22` | 表 2-2：`columns[]`（`id`、`label`、`vendor`、`tip`）、`sections[].rows[]`（`name`、`tip`、`unit`、`cells.{列 id}`：`d`、`v`、`note`、`dagger`）、`hints`（占位 `{n_rows}` `{n_cmp}` `{n_cmp_scores}`） |
| `figures.f31/f32/f33` | 图 3-1 / 3-2 / 3-3：`bench`、`axis`（min / max / step，数据超出时自动外扩并提示）、`head`、`caption`、`source_tip`、`panels[]`（图 3-3：`bench`、`title`、`sub`） |
| `ui` | 脚本拼句用的固定字词（「本列第 {n} 名。」等），英文版时一起翻 |

`src` 的取值：`artificial_analysis`、`vals_ai`、`system_card`、`model_card`、`release_table`（官方发布博客里的分数表）、`leaderboard`（测试方官方榜）、`vendor_self_report`、`lmarena`、`other`。

### vendors.json

`vendors[]` 顺序＝表 2-1 分组顺序＝图 3-x 图例顺序。字段：`key`、`name`（显示名）、`product`、`group`（前沿 / 大厂 / 开源）、`css_var`、`light` / `dark`（色值）、`legend_tip`、`t22_class`（表 2-2 格子类名）、`builtin_css`（true＝颜色写在报告原 CSS 里，只有 google / anthropic / openai）。
`timeline_lanes[]`：图 2-1 模型泳道顺序（`lane`、`vendor`、可选 `label` 和 `hollow_swatch`，内部代号泳道就是这样）。没有事件的泳道不画，没有模型的厂商不出组标题行。
`reference_colors`：compute 管的三条算力泳道颜色，只用于配色校验。

## 4. 加一个新模型

1. **先找出处，按优先级**：
   - 发布日、价格：官方发布博客 + 官方 API 定价页，至少两个来源一致才写；受限模型可以单来源，但 `price.tip` 末尾标〔低〕。
   - 厂商自报分数：官方发布博客里的分数表、System Card、模型卡（Model Card）。写清是哪一家的表（同一模型在别家表里分数可能不同，两个都写进 note）。
   - 独立分数：Artificial Analysis 模型页（AA 指数，取最高推理强度，写版本号 v5.0.1）、Vals AI 榜单（Vals Index、Terminal-Bench 4.0 独立测，写每题成本）、LMArena（如果以后加列）。
   - 转录站（BenchLM、explainx、LLM Stats）只能做核对或在一手来源打不开时用，note 里写「经 X 转录」。
2. **每个分数都要写 note**：出处（哪份表 / 哪一节）＋测试条件（推理强度、限时、是否关防护、试验次数、工具）。格子提示＝「{name}：{d}{unit}。本列第 N 名。{note}」，名次由脚本加，不要写进 note。Vals 两列的 note 必须含「每题成本 $X」（图 3-2 从这里取）。
3. 在 `models.json → models` 里加一条（位置随意，表里按发布日自动排）。`status` 选对；受限模型加 `tag`：`{"text": {"zh": "受限", "en": "…"}, "tip": {"zh": "只对通过审核的机构开放，普通开发者不能直接调用。", "en": "…"}}`。
4. 在 `timeline_events` 里加节点：先宣布后开放的，加一个 `hollow: true` 的宣布节点和一个开放节点，模型的 `release` 写开放日，`release_star: true`，`release_tip` 写两个日期。同一天同一家发多个模型，合成一个节点（label 用「A · B」）。
5. 有 System Card 专项分数的，在 `t22` 里加列或补格子。
6. 跑第 2 节的命令。看提示行：列宽、轴外扩、快照日不一致都会提示。
7. **人工判断**：第 1 章结论要不要改（新模型是否改变了「综合第一 / 各价位最优 / 最低价」等判断）；第 4 章的说法是否还成立；附录来源列表加上新来源链接（手写在 `<section id="s5">` 的 `ol.src` 里）。

## 5. 加一个新 Bench 列

1. 在 `benches` 里按想要的列位置插入一条（列序＝数组顺序，同组要挨着）。`key` 用英文短键；`desc` 写清：全名、单位、测什么、谁测的、能不能横向比，结尾加可信度〔高 / 中 / 低〕。
2. 新组：在 `t21.groups` 里加 `{key, label, short, tip}`，`benches` 的 `group` 指向它。
3. 越低越好的指标设 `direction: "lower"`。
4. 给已有模型补 `scores.<key>`。没有分数的格子不用写，自动显示「—」。
5. 如果它也该进图 3-3，在 `figures.f33.panels` 加 `{bench, title, sub}`；图 3-3 标题里「六项」是手写的，要一起改。
6. 跑命令。表头太长会提示列宽不够，调 `layout.t21.bench`（所有 Bench 列同宽）。

## 6. 新厂商第一次出现

xAI（Grok）、Meta（Muse）、DeepSeek、Moonshot（Kimi）、智谱（GLM）已经在 vendors.json 里预留了颜色和泳道，第一次给它加模型或时间轴节点时：

1. 只需在 models.json 里加模型和节点；表 2-1 组标题行、图 2-1 泳道、图 3-x 图例、配色 CSS（`<style id="data-css">`）都会自动出现。
2. 检查 `legend_tip` 和 `name` 写法对不对（例如智谱显示名要不要改成「智谱」）。
3. 浏览器检查时确认该厂商的色块在深浅两种主题下都显示、悬停图例能聚光。
4. 真正的新厂商（不在预留名单里）：在 `vendors` 加一条（`builtin_css: false`，`css_var` 取两个字母、不和已有变量重名，`t22_class` 取 `v` + 一个字母），在 `timeline_lanes` 加泳道，然后跑 `qa/palette_check.py`：A、B 两组相邻对必须全过；C 组两两对会有不过的，见 `qa/palette_report.txt` 里的说明。颜色优先从 dataviz 参考色板里没用过的槽位取。

## 7. 快照日期

1. 改 `models.json → meta.snapshot`。
2. **compute/build.py 里还有两处写死了 2026-11-19**：第 89 行算力泳道的快照竖线 `left:93.956%`，以及页面 JS 里 `'2026-11-19：本报告的快照日期。'`。build_tables.py 发现不一致会打印提示，去 compute/build.py 改掉再跑。
3. 时间轴只覆盖 `t0` 起 `span_days` 天（现在是 2026-06-01 到 11-30）。12 月以后的节点会提示「超出时间轴」：这时要同时改 models.json 的 `timeline` 和 compute/build.py 的 `T0, SPAN` 与写死的月线位置，属于较大改动，先问 Charles。
4. 正文里还有手写的日期（第 1 章、Vals「2026-11-16」、Epoch「2026-11-19 版」等），不是快照日期，不要批量替换。

## 8. 版本备份

每次改之前把正式报告复制到 `backup/v-YYYY-MM-DD-HHMM.html`。`backup/` 只留最近 10 份（按修改时间）。VM 里默认没有删除权限：先用 device_request_delete_permission 申请构建目录的删除权限；用户没同意时，把多出来的旧版本移到 `backup/_to_delete/`，在回复里告诉用户。`backup/v-2026-11-22-pre-data.html` 是数据化之前的最后一个手写版，删到它时先问。

## 9. 双语（占位，下一轮补全）

报告以后要有中文 / English 切换。现在：

- data/ 里所有面向读者的文字字段都已是 `{"zh": "…", "en": ""}`，`en` 暂时为空；build_tables.py 用 `t(field, lang)` 取文字，目前只输出 `zh`。
- **从现在起，每条新内容必须同时填 `zh` 和 `en`，`en` 不能留空**（模型名、品牌名、数字、日期除外）。
- 英文翻译和页面上的语言切换由另一轮来做，届时补充本节：翻译口径、术语表、切换方式、回归要求。

## 10. 规则在哪、已知限制

- 前三名、色条、排序、计数、列宽、时间轴位置等全部规则写在 `build_tables.py` 开头的注释里（从手写版反推，并已逐字节回归）。
- 名次是「密集名次」：并列同名次（Terminal-Bench 独立测两个 65.15 都是第 1）。
- 图 3-1 提示里的价格写法沿用原文：输入「$2 →$4」、输出「$10 → $20」（空格不一致是原文如此）。
- 列宽来自浏览器实测值，脚本只能估算新内容是否放得下；加长名字的模型或长表头后，务必看截图有没有折行。
- `qa/oneoff/` 里的反抽脚本依赖 2026-11-22 前的 HTML 结构，以后不要再跑。
