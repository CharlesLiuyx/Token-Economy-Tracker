# 大模型发布和 Bench 跟进：维护说明书

给以后维护这份报告的 Claude 看。先读完这一页再动手。

## 0. 仓库是唯一正式版本

- 正式版本在 GitHub 仓库 `CharlesLiuyx/Token-Economy-Tracker` 的 `reports/llm-release-bench/`（2026-11-22 从 Info 库 `04 行业与宏观数据/大模型发布跟进和算力/` 迁来）。**只在仓库里改**，改完 commit。
- 备份靠 git 历史，不再存 `backup/`。要看旧版：`git log -- "reports/llm-release-bench/<报告文件名>"`，`git show <commit>:"reports/llm-release-bench/<报告文件名>" > /tmp/old.html`。
- 用户电脑上还有一份只读副本（见第 11 节），不在那里改。
- 本目录和仓库主体（`scripts/`、`data/`、`site/`）互不相干：`make build` / `make test` / `daily.yml` 都不碰这里，这里的脚本也不碰它们。

## 1. 文件在哪

以本目录 `reports/llm-release-bench/` 为根。所有脚本只用「相对脚本所在目录」的路径，报告文件和构建脚本在同一层。

| 路径 | 是什么 |
|---|---|
| `大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html` | 正式报告（单文件，中英双语） |
| `data/models.json` | 模型、Bench 列、分数、价格、许可证、参数、发布日、时间轴节点、表 2-2、表 3-1 列配置、图 3-2 与图 4-x 配置、快照日期（含第 3 章快照）、第 3 章来源 |
| `data/vendors.json` | 厂商表：顺序、颜色、泳道顺序、分组（groups：前沿 / 大厂 / 开源，及每组进哪一章） |
| `i18n/static.json` | 不属于上面两个文件的全部固定文字：顶栏控件、目录头、各章标题、第 1 章结论、第 5 章、附录手写来源、图 2-1 图注图例、术语表 TERMS、页面 JS 的界面字 |
| `research/` | 加模型前的调研底稿（每份 JSON 带分数、价格、出处与 caveats）、官方品牌色调研 `2026-11-22-brand-colors.json` 和改章裁定 `decisions-ch3.md`。构建不读它；第 3 章数据由 `qa/oneoff/ch3_import.py` 从这里一次性导入 |
| `bilingual.py` | 两个构建脚本共用：双语输出规则、图 2-1 横轴推导 |
| `build_tables.py` | 读 data/ 和 i18n/，重写报告里 `<!--data:…-->` 标记之间的内容 |
| `compute/` | 算力到卡模型（`model.py` → `model.json` → `build.py`），管 `<!--compute:…-->`。口径说明 `compute/decisions.md` |
| `compute/web/` | Epoch AI 公开数据（两份 CSV）与由它生成的 `findings.json`，见第 1.1 节 |
| `qa/` | 双语检查、中文等价检查、第 2 章一致性检查、浏览器检查、换快照日演练、加模型 / 加厂商演练、配色校验 |
| `qa/oneoff/` | 一次性脚本留档（2026-11-22 数据化、双语迁移、第 3 章导入 `ch3_import.py`、改章骨架 `ch34_skeleton.py`），不要再跑 |
| `requirements.txt` | 可选检查脚本的依赖（构建本身只用标准库） |

### 1.1 不进仓库的东西（公开仓库）

本目录 `.gitignore` 写明了：`compute/local/`（SemiAnalysis 等付费研报的原始摘录 `findings.json` 和截图 `_imgs/`，只留在维护者本机）、所有 `*.png` 截图、`qa/` 下的检查产物、`backup/`。
构建不需要 `compute/local/`：`compute/model.py` 只用它自己里面写的数字（＝`compute/decisions.md` 已裁定的数），`compute/web/` 的 Epoch CSV 只用于自检核对。2026-11-22 已实测：没有 `compute/local/` 时 `model.py` 生成的 `model.json` 去掉英文后与迁移前逐字节一致。

`compute/web/epoch_ai_chip_sales_*.csv` 来自 Epoch AI 的 AI Chip Sales 数据集（<https://epoch.ai/data/ai-chip-sales>，2026-11-19 版），按 **CC BY 4.0** 协议提交，署名 Epoch AI；报告附录来源里也列了它。`compute/web/findings.json` 是 `build_findings.py` 从这两份 CSV 和公开网页整理的，不含付费内容。

## 2. 两套构建，各管各的标记

- `build_tables.py` 只改 `<!--data:NAME:start-->…<!--data:NAME:end-->`（JS 里写成 `/*<!--…-->*/`）：
  - 数据块：`vcss`（新厂商配色）、`c34css`（第 3、4 章的样式：表 3-1 组标题、图 3-2 泳道小字、分组图例、散点）、`topbar`、`h1`、`meta`、
    第 2 章 `t21hints`、`t21`、`f21hl`（图 2-1 的 `<div class="hl">`，带横轴起点和天数）、`f21lanes`、`f21axis`、`t22hints`、`t22`；
    第 3 章 `ch3meta`（章首快照行）、`t31hints`、`t31`、`f32`（整张时间轴）；第 4 章 `f41`…`f45`；附录 `appendix`、`src3`（第 3 章来源）；
    页面脚本 `c34js`（JS 里写成 `/*<!--data:c34js:…-->*/`：散点标签避让 fitScatter，接在 relayout 后面）。
  - 固定文字块（来自 `i18n/static.json`，名字带 `s-` 前缀）：`s-chrome`（顶栏按钮、语言切换、更多菜单、目录头）、`s-hd-*`（各章标题：h1–h6、h21/h22、h31/h32、h41–h45）、`s-ch1`、`s-ch5`、`s-src`、`s-f21cap` / `s-f21leg1` / `s-f21leg2`（图 2-1 图注与图例）、`s-css`（随语言变的 CSS 文字）、`s-terms`（TERMS / ALIAS / ALIAS_EN）、`s-ui`（I18N 界面字）。
  - 章节：1 结论｜2 前沿模型（2.1 表 2-1 / 图 2-1、2.2 表 2-2、2.3 算力）｜3 大厂与开源模型（3.1 表 3-1、3.2 图 3-2）｜4 全部模型对比（4.1 AA、4.2 Vals、4.3 TB 4.0 Vals、4.4 价格与得分散点、4.5 厂商自报六项）｜5 怎么读这些数｜附录 来源。
- `compute/build.py` 只改 `<!--compute:…-->`：图 2-1 顶部刻度、三条算力泳道、图 2-1 的算力图例和「怎么读」、2.3 节（含图 2-2 / 2-3、表 2-3）、算力来源、算力术语、相关 JS（其中时间轴指示线 / 磁吸和底部快照标签避让 fitSnap 对页面里所有 `.hl` 生效，图 3-2 直接复用）。
- 标记之外剩下的是页面骨架：`<head>` 里的 CSS 和 `<script>` 主体（目录、提示框、吸顶表头、语言切换等交互代码）。这些是代码不是文字，改它们直接改 HTML，改完同样跑第 3 节。**任何面向读者的文字都不要直接写进 HTML**，写进数据文件，否则下次构建不会出英文。

## 3. 每次改完必须跑的命令

在仓库根目录：

```bash
cd reports/llm-release-bench
R="大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html"
git show HEAD:"reports/llm-release-bench/$R" > /tmp/prev.html   # 1 改前版本（备份就是 git）
python3 build_tables.py                                         # 2 数据 → 表 / 图（看「提示：」行）
python3 compute/build.py                                        # 3 算力块（没改算力数据时输出 unchanged）
python3 build_tables.py && python3 compute/build.py             # 4 再跑一遍，两个都必须输出 unchanged（幂等）
python3 qa/i18n_check.py                                        # 5 双语检查（静态，标准库），必须「通过」
python3 qa/diff_check.py /tmp/prev.html "$R"                    # 6 列出这次改动，逐条确认都是你想改的
python3 qa/ch2_equiv.py /tmp/prev.html "$R"                     # 7 没打算动第 2 章时：第 2 章除章名外必须逐字节一致（颜色值默认忽略，--strict-color 连颜色也比；加 --browser 再比运行后的 DOM 与可见文本）
```

然后做浏览器检查（需要 playwright + Chromium；云端容器一般有 `/usr/bin/google-chrome`）：

```bash
python3 qa/i18n_check.py --browser --chrome /usr/bin/google-chrome        # 英文模式全页无汉字、提示框与术语逐个核对
python3 qa/browser_check.py "$R" /tmp/qa-shots /usr/bin/google-chrome     # 3 宽 × 深浅 × 中英，断言 + 截图（含表 3-1 吸顶克隆、图 3-2 节点、图 4-4 散点标签）
python3 qa/ch2_equiv.py /tmp/prev.html "$R" --browser --chrome /usr/bin/google-chrome   # 第 2 章运行后 DOM 与可见文本（中英 × 1440 / 800）
python3 qa/contrast_check.py "$R" /usr/bin/google-chrome                 # 色条上的文字对比度：深浅 × 中英，所有压在色条上的文字 ≥ 4.5:1
python3 qa/rehearsal.py                                                  # 加 Bench / 加大厂模型 / 加新厂商演练（副本，结果 qa/rehearsal/result.json）
python3 compute/qa_browser.py "$R" /tmp/qa-c /usr/bin/google-chrome --lang zh   # 算力图：布局、磁吸、吸顶、数值
python3 compute/qa_browser.py "$R" /tmp/qa-c /usr/bin/google-chrome --lang en
```

要求：全部「通过 / OK」，并亲眼看 `/tmp/qa-shots` 里中英各一张 `f21`、`t21`、`t31`、`f32`、`f44` 截图。截图不要提交（`.gitignore` 已排除 png）。
改了厂商颜色时，还要跑 `python3 qa/palette_check.py <Skill dataviz 的 scripts 目录>`，结果写进 `qa/palette_report.txt`（要提交）。配色规则见第 13.5 节（官方品牌色优先）。

`build_tables.py --check` 只校验不写盘；`--data 目录` 可以指向一份副本数据（演练用）。`compute/build.py` 也接受 `--data 目录`（它从 `models.json` 读快照日）。

## 4. 数据字段

所有面向读者的文字都是 `{"zh": "…", "en": "…"}`，两个都要填（第 9 节）。数字、日期、价格、品牌名、模型名是普通值。

### models.json

| 字段 | 说明 |
|---|---|
| `meta.snapshot` | 快照日期 `YYYY-MM-DD`。顶栏、首屏、图 4-x 来源提示、附录「核对方式」、**图 2-1 的整个横轴**（第 7 节）都从这里来 |
| `meta.chapters.ch3` | 第 3 章：`snapshot`（章首快照行、**图 3-2 的横轴**、图 4-x 来源提示里的 `{snapshot3}`）、`label`（章首那一行，占位 `{snapshot}` `{n}`） |
| `meta.title` / `meta_prefix` / `appendix_hints` | 报告标题（h1、顶栏、`<title>` 同源）、首屏前缀、附录提示（`{snapshot}` 会被替换） |
| `layout.t21` / `layout.t22` / `layout.t31` | 列宽（em），中英共用一套。t31 另有 `license`、`params` 两列的宽度。原值是浏览器实测的；新列沿用同组宽度。脚本按中英两种文字估算放不下时会打印提示，这时调大这里的值或把英文写短 |
| `t21.groups` | 表 2-1 的分组表头：`key`（basic / indep / general / cyber / life）、`label`、`short`（「怎么读」提示里用）、`tip` |
| `t21.basic` | 发布 / 输入 / 输出三列的表头文字与提示（`{max}`＝公开模型最高价） |
| `t21.hints` | 表上方的提示。可用占位：`{n_bench}` `{n_groups_zh}`（中文「四」/ 英文 four，取自 `ui.groups_zh_digits`）`{group_names}` `{price_in_max}` `{price_out_max}` |
| `t31` | 表 3-1 的列配置，见第 13 节：`toc`、`c0`、`groups[]`（`key`、`label`、`short`、`tip`、**`cols`**）、`basic`（release / price_in / price_out / license / params 的表头文字与提示）、`hints`（占位 `{n_models}` `{n_bench}` `{n_groups_zh}` `{group_names}` `{price_in_max}` `{price_out_max}`） |
| `benches[]` | 每个 Bench 一列，顺序＝表 2-1 的列序；`group` 不在 `t21.groups` 里的（现在是 `ext`）只出现在表 3-1。`key`、`label`、`name`、`unit`（`%`、` 个` / ` hijacks`、空）、`group`、`direction`（`higher` / `lower`）、`bar`（`auto` / `zero` / `minmax`，见 build_tables.py 开头）、`desc`（表头提示；脚本会自动接上「有分数的模型：N 个。」） |
| `models[]` | 每个模型一行。`id`、`name`、`short`、`vendor`、`status`（`public` / `restricted` / `internal`）、`tag`（`text`、`tip`）、`release`、`release_star` + `release_tip`、`trained`（`label`、`tip`、`end`）、`price`（`in`、`out`、可选 `in_next` / `out_next`、`tip`）、`scores`、`blank` |
| `models[].scores.<bench>` | `d` 显示文本（照来源写；可带角标 `<sup>AA</sup>`）、`v` 数值、`note`（格子提示里「名次」之后的全部文字：出处＋测试条件＋可信度〔高/中/低〕）、`src`、`cf`（可信度 高 / 中 / 低） |
| `models[].open_weights` | **新模型必须填**（内部代号模型不填）：true＝开源（开放权重），false＝闭源。决定模型名后的「开源 / 闭源」小标签（表 2-1、3-1、图 4-1…4-5）、图 4-4 的空心 / 实心说明和悬停文字。缺了构建会提示并按闭源处理，`qa/rehearsal.py` 断言演练模型都填了。时间轴节点（`timeline_events[].open_weights`）和表 2-2 列（`t22.columns[].open_weights`）放不下标签，只在悬停末尾补一句 |
| `models[]` 第 3 章另有 | `license`（`{d, tip}`，d＝MIT / Modified MIT / 自定义 / 否，tip 写许可证要点）、`params`（`{d, tip}`，d＝「总 / 激活」，tip 写出处与可信度）、`row_tip`（模型名悬停：一句简介＋没填进表的分数和原因）、`blank.price_in/price_out`（没有 API 价时的说明） |
| `models[].blank.<bench>` | 没有分数但要写说明的格子：`d`（如「同上」/ ditto、「—」）、`tip` |
| `timeline_events[]` | 图 2-1 模型泳道的节点：`lane`、`date`、可选 `end`、`hollow`、`label`、`tag`、`tip`（脚本自动在前面加「YYYY-MM-DD：」/「YYYY-MM-DD: 」，区间节点不加） |
| `t22` | 表 2-2：`columns[]`、`sections[].rows[]`、`hints`（占位 `{n_rows}` `{n_cmp}` `{n_cmp_scores}`） |
| `figures.f41/f42/f43` | 图 4-1 / 4-2 / 4-3：`bench`、`mark`（bar / dot）、`xcol`（price / cost）、`axis`、`head`、`caption`、`source_tip`（占位 `{snapshot}` `{snapshot3}` `{min}` `{max}`）、`toc` |
| `figures.f44` | 图 4-4 散点：`x`（price_out）、`y`（aa）、`xaxis`（`min` / `max` / `ticks`，对数刻度）、`yaxis`、轴名、图例、`missing`（没有价格未画的图注）、`tip` / `ow_yes` / `ow_no`（悬停文字） |
| `figures.f45` | 图 4-5：`panels[]`（`bench`、`title`、`sub`），轴 0–100 |
| `f32` | 图 3-2：`toc`、`caption`、图例三项、`hints`（占位 `{snapshot}`） |
| `sources_ch3` | 附录里第 3 章的来源：`groups[]`（`group`、`label`、`items[]`：`title`（可为 `{zh,en}`）、`url`、`date`、`accessed`） |
| `ui` | 脚本拼句用的固定字词。`count_groups`（首屏分组计数）、`snap3_tip` / `snap3_short_tip`（图 3-2 底部快照标签）。`month`（中文 `{m} 月`，英文 `{mon}`＝Jan…Dec）、`snap_label` / `snap_short` / `snap_short_tip`（图 2-1 底部快照标签：全称 / 放不下时的短称 / 短称时的提示）、`cost_re`（从 note 里抓「每题成本 $X」的正则，中英各一条，抓到的 $X 必须一致） |

`src` 的取值：`artificial_analysis`、`vals_ai`、`system_card`、`model_card`、`release_table`、`leaderboard`、`vendor_self_report`、`lmarena`、`other`。

### vendors.json

`groups[]`：`key`（frontier / bigtech / open）、`label`、`tip`、**`chapter`**（2 或 3：这一组厂商的模型进哪一章）。顺序＝图 4-x 图例里分组的顺序。
`vendors[]` 顺序＝表 2-1 / 表 3-1 分组顺序＝图 4-x 组内图例顺序。字段：`key`、`name`、`product`、`group`（取 `groups[].key`）、`css_var`、`light` / `dark`、`legend_tip`、`t22_class`、`builtin_css`（true＝颜色写在报告原 CSS 里，只有 google / anthropic / openai）。
`timeline_lanes[]`：图 2-1 模型泳道顺序（`lane`、`vendor`、可选 `label` 和 `hollow_swatch`）。没有事件的泳道不画，没有模型的厂商不出组标题行。
`reference_colors`：compute 管的三条算力泳道颜色，只用于配色校验。

### i18n/static.json

| 键 | 说明 |
|---|---|
| `strings` | 短文字（菜单、标题、图注、图例）。模板里用 `{{t:键}}` 输出文字，`{{a:属性:键}}` 输出属性 |
| `templates` | 带占位的 HTML 片段（顶栏、各章标题、图 2-1 图注图例）。结构改动改这里；`{{lang}}` 是语言切换按钮 |
| `blocks` | 整段 HTML，中英各一份（`ch1` 第 1 章结论、`ch5` 第 5 章「怎么读」、`src` 附录手写来源）。两份结构要对应（同样的条目、同样的链接） |
| `terms` | 术语表：`n` 名称、`d` 释义，各 `{zh, en}`。算力相关术语在 `compute/build.py` 的 `C_TERMS` |
| `alias` | 正文里自动加术语下划线的词：`zh` 管中文和两种语言共用的文字，`en` 管英文文字。长词优先、英文按词边界 |
| `js_ui` | 页面 JS 用的界面字（返回按钮等）；标题自动取 `models.json` 的 `meta.title` |

## 5. 加一个新模型

1. **先找出处，按优先级**：
   - 发布日、价格：官方发布博客 + 官方 API 定价页，至少两个来源一致才写；受限模型可以单来源，但 `price.tip` 末尾标〔低〕/ [low]。
   - 厂商自报分数：官方发布博客里的分数表、System Card、模型卡。写清是哪一家的表。
   - 独立分数：Artificial Analysis 模型页（取最高推理强度，写版本号 v5.0.1）、Vals AI 榜单（写每题成本）、LMArena（如果以后加列）。
   - 转录站（BenchLM、explainx、LLM Stats）只能做核对或在一手来源打不开时用，note 里写「经 X 转录」/ "via X's transcription"。
2. **每个分数都要写 note**，中英两份：出处＋测试条件。格子提示＝「{name}：{d}{unit}。本列第 N 名。{note}」，名次由脚本加。Vals 两列的 note 必须中文含「每题成本 $X」、英文含「Cost per task $X」（图 3-2 从这里取，两边的 $X 必须一样）。
3. 在 `models.json → models` 里加一条。`status` 选对；受限模型加 `tag`：`{"text": {"zh": "受限", "en": "Gated"}, "tip": {"zh": "只对通过审核的机构开放，普通开发者不能直接调用。", "en": "Available only to vetted organizations; general developers cannot call it directly."}}`。
4. 在 `timeline_events` 里加节点：先宣布后开放的，加一个 `hollow: true` 的宣布节点和一个开放节点，模型的 `release` 写开放日，`release_star: true`，`release_tip` 写两个日期。同一天同一家发多个模型，合成一个节点（label 用「A · B」）。
5. 有 System Card 专项分数的，在 `t22` 里加列或补格子。
6. 跑第 3 节的命令。看提示行：列宽、轴外扩、节点在横轴外、英文缺失都会提示。
7. **人工判断**：第 1 章结论要不要改（`i18n/static.json → blocks.ch1`，中英两份一起改；后 3 条由 `check_ch1()` 核对，数据一变构建就失败并告诉你缺哪句）；第 5 章（`blocks.ch5`）是否还成立；附录来源（`blocks.src`，中英两份都加新链接；第 3 章的来源加到 `models.json → sources_ch3`）。
8. **第 3 章的模型**（厂商的 group 是大厂或开源）另外要写 `license`、`params`、`row_tip`。厂商自报分数只填版本、单位、子集都和那一列一致的；不一致的不填，写进 `row_tip`（「没填进表的：…」）。同一个数各家表里不一样时，先用模型自家的表，再用别家表里口径一致的，note 里写清是谁报的、别家是多少。先整理成 `research/` 下的 JSON（出处、条件、caveats），再进 `models.json`。

## 6. 加一个新 Bench 列

1. 在 `benches` 里按想要的列位置插入一条。`key` 用英文短键；`desc` 中英都写清：全名、单位、测什么、谁测的、能不能横向比，结尾加可信度〔高 / 中 / 低〕/ [high / medium / low]。
2. 新组：在 `t21.groups` 里加 `{key, label, short, tip}`。
3. 越低越好的指标设 `direction: "lower"`。
4. 给已有模型补 `scores.<key>`。没有分数的格子不用写，自动显示「—」。
5. 如果它也该进图 4-5，在 `figures.f45.panels` 加 `{bench, title, sub}`；图 4-5 标题里的「六项」/ "Six" 是写在 `figures.f45.caption` 和 `hd_h45` 里的，要一起改。
6. 如果它该进表 3-1：在 `t31.groups[].cols` 里点名（第 13 节）。只给表 3-1 用的列，`group` 写 `ext`（或任何不在 `t21.groups` 里的组名），表 2-1 不会出这一列。
7. 跑命令。表头太长会提示列宽不够，调 `layout.t21.bench`（所有 Bench 列同宽）。演练：`python3 qa/rehearsal.py`（副本里加虚构的列、大厂模型和新开源厂商，结果在 `qa/rehearsal/`，不进 git）。

## 7. 快照日期与图 2-1 横轴

1. 只改 `models.json → meta.snapshot`，然后按第 3 节跑：先 `build_tables.py`（这时会提示「算力泳道的快照竖线…不一致」，正常），再 `compute/build.py`，再各跑一遍确认 unchanged。
2. **横轴全部由快照日推导**（`bilingual.axis`，两个构建脚本共用）：起点＝快照日所在月往前 5 个月的月初，终点＝快照月最后一天（落在 100%）。例：快照 2026-11-19 → 2026-06-01 起 182 天；快照 2026-12-05 → 2026-07-01 起 183 天。快照竖线、月线、顶部和底部刻度、算力泳道的 6 根月柱、泳道标签里的「6–11 月 ≈ …」、2.3 节第一条结论的月份范围、JS 里的快照提示都跟着变，不用改代码。
3. 落在横轴外的点节点不画，区间节点裁到横轴内（构建时打印提示）；算力泳道上的事件节点（`compute/build.py` 的 `PIN_EVENTS`）同理。
4. 算力月柱需要 `compute/model.json` 覆盖横轴的 6 个月（现在到 2027-06）。快照日超过 2027-06 前要先扩 `model.py` 的季度表，否则 `compute/build.py` 会断言失败。
5. 换月前先演练：`python3 qa/rehearse_snapshot.py 2027-01-10 /tmp/rehearse /usr/bin/google-chrome`（在临时副本里改快照日、构建两遍、检查横轴首月 / 末柱 / 竖线位置 / 越界 / 重叠并截图，不碰正式文件）。
6. 2.3 节的结论文字（Rubin 过半的月份等）有断言保护：数据变了会构建失败，届时要人工改结论再改断言。
7. 正文里还有手写的日期（第 1 章、Vals「2026-11-16」、Epoch「2026-11-19 版」等），不是快照日期，不要批量替换。

8. 第 3 章快照（`meta.chapters.ch3.snapshot`）单独改：它只管章首快照行和图 3-2 的横轴，横轴算法同上。`qa/rehearse_snapshot.py` 把两个快照日一起换来演练。

## 8. 版本与备份

备份就是 git：每次改完 commit，提交信息写清改了什么。不再维护 `backup/` 目录。线上 html-review 的版本见第 10 节。

## 9. 双语
- 英文字体：英文模式下正文用 Adobe Clean（用户 2026-11-22 指定），写在报告 <style> 静态部分的 `:root[data-lang=en] body{font-family:…}`；页面不内嵌字体文件（Adobe Clean 是 Adobe 授权字体，且页面要离线可开），没装这款字体的机器按后备字体（系统无衬线体）显示。改英文排版时不要删掉这一条。

页面右上角「中文 / EN」切换，选择存在 `localStorage` 的 `mdl-lang`，默认中文；`<html lang>`、`<title>`、`aria-label` 跟着变。

**怎么实现的**：每段面向读者的文字都输出两份——`<span class="lz">中文</span><span class="le" lang="en">English</span>`（大段用同名 `div`），CSS 按 `:root[data-lang]` 只显示一份；属性输出 `data-tip` + `data-tip-en`（`data-tiph`、`data-toc`、`data-short*` 同理，`aria-label` 的英文放 `data-aria-en`），单例提示框按当前语言取。两种语言相同的文字（模型名、数字、日期）只输出一份。术语：TERMS 每条有 `n / d`（中文）和 `ne / de`（英文），英文正文按 `ALIAS_EN` 加下划线。规则写在 `bilingual.py` 开头。

**规矩**：

1. 新增任何面向读者的文字，**zh、en 必须同时填**，en 不能留空、不能有汉字。数据里写 `{"zh": "…", "en": "…"}`；`compute/build.py` 里写 `L('中文', 'English')`；`compute/model.py` 里写 `Z('中文', 'English')`；固定文字写进 `i18n/static.json`。不要把文字直接写进 HTML。
2. en 缺失时构建会退回中文并打印「英文缺失」，`qa/i18n_check.py` 判失败。
3. 英文写法：地道、像英文研究简报，不逐字对译。数字用英文习惯：`$20B`、`4.3M units`、`523K`、`H100-equivalents`（表内简写 `H100e`）、日期 `Nov 17` 或 ISO `2026-11-17`；可信度写 `[high] / [medium] / [low]`；不用全角标点和全角空格（图号后的空隙用 ` `）。固定译法：发布表＝launch table、推理强度＝reasoning effort、档＝setting、防护＝safeguards、受限＝Gated（表内小标）/ restricted（正文）、内部代号＝internal codename、到卡＝arrivals、每题成本＝Cost per task。
4. 英文一般比中文长：表头、小标、图内标签要短（列宽中英共用）。改完看英文截图有没有折行、溢出。
5. 检查：`python3 qa/i18n_check.py`（数据：每个 `{zh,en}` 的 en 非空且无汉字；HTML：每个 `.lz` 后紧跟 `.le`、两种语言共用的文本无汉字、含汉字的属性都有英文版）和 `--browser`（英文模式全页 innerText、所有提示、每种术语无汉字；中文模式 `.lz` 全可见、`.le` 全隐藏）。确实需要在英文模式保留的汉字（模型原名、来源原题）登记在 `qa/i18n_whitelist.json`；语言按钮「中文」用 `data-i18n-skip` 豁免。
6. 想确认中文模式没被改坏：`python3 qa/zh_equiv.py 改前.html 改后.html --allow qa/zh_equiv_allow.txt`（去掉英文节点和标记后逐事件比较中文模式的内容；有意的改动登记在 allow 文件里）。

## 10. 同步到 html-review（线上评审页）

报告的 review id 是 `-ql-69iE_Lz3`（写在报告 `<head>` 的注释和 meta 里，沿用，不新建）。每次 commit 并推送之后同步（本机会话用已登录的 CLI 凭证，云端会话用下面第 2 步的 HTML_REVIEW_TOKEN）：

1. 安装 CLI（来自私有仓库 `one2x-ai/html-review`，需要用户授权该仓库的访问；已装过就跳过，`command -v html-review`）：
   ```bash
   git clone https://github.com/one2x-ai/html-review ~/.html-review-install && cd ~/.html-review-install/cli && (pnpm install && pnpm build || (npm install && npm run build)) && npm install -g .
   ```
2. 认证：用环境变量 `HTML_REVIEW_TOKEN`（作为会话密钥提供；不要打印、不要写进文件或日志）。过期时请用户更新密钥，不要在无界面环境里交互登录。
3. 上传新版本：
   ```bash
   html-review upload "reports/llm-release-bench/大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html" --id -ql-69iE_Lz3
   ```
4. 线上只留最近 10 个版本：运行时先看 `html-review --help`（和各子命令的 `--help`）有没有删除旧版本的命令；有就删到只剩 10 个；没有就在汇报里写「CLI 不支持清理」。

## 10b. 线上地址与入口
- 报告随 Token-Economy-Tracker 的 GitHub Pages 一起发布：`make build` 会把本目录唯一的报告 .html 复制成 `site/llm-release-bench/index.html`（scripts/build.py 的 COMPANION_REPORTS，只搬运不改内容），线上地址 https://charlesliuyx.github.io/Token-Economy-Tracker/llm-release-bench/ 。改了这里的报告、推到 main 后 deploy.yml 会自动重新部署（paths 含 reports/**）。
- 主看板顶栏有入口「模型发布 & Bench →」，链接带 `?lang=zh|en`。本页 head 里的首帧脚本按 URL ?lang= > 本页记忆 mdl-lang > 主看板的 lang > 中文 决定语言。改 head 脚本时保留这个顺序。
- 本目录只能有一个报告 .html（否则复制会被跳过并打印 warn）。
- 顶栏左上角「← TET 主页」：由 build_tables.py 的 topbar() 输出（HOME_URL 为绝对地址，本地打开或 html-review 上也能用），文字在 data/models.json 的 ui.home_label / ui.home_tip；页面 JS 在语言切换时把链接改成 `?lang=zh|en`，主看板按它定语言。

## 11. 本地副本

用户电脑上另有一个定时任务，每天把仓库里的报告 HTML 拉到 Info 库的 `04 行业与宏观数据/大模型发布跟进和算力/`。那份文件只读：**不在本地改**，改了也会被下一次拉取覆盖。本地原来的构建目录 `大模型发布和Bench跟进-构建/` 已停用（顶部写了迁移说明），不要再在那里跑脚本。

## 12. 规则在哪、已知限制

- 前三名、色条、排序、计数、列宽、时间轴位置等全部规则写在 `build_tables.py` 开头的注释里。
- 名次是「密集名次」：并列同名次（Terminal-Bench 独立测两个 65.15 都是第 1）。
- 图 3-1 提示里的价格写法沿用原文：输入「$2 →$4」、输出「$10 → $20」（空格不一致是原文如此）。
- 列宽来自浏览器实测值，中英共用一套，脚本只能估算；加长名字或长表头后，务必看中英两种截图有没有折行。
- 每段文字都存两份，报告从约 0.29 M 字符增到约 0.52 M 字符，属正常。
- `qa/oneoff/` 里的脚本依赖历史版本的 HTML 结构，以后不要再跑。

## 13. 分组决定章节、表 3-1 列配置、散点图、加新厂商（2026-11-22）

### 13.1 分组决定章节
- `vendors.json → groups[].chapter`：前沿＝2，大厂、开源＝3。模型跟着厂商走：第 2 章的表 2-1、图 2-1、首屏「前沿 N 个」只取 chapter 2 的厂商；第 3 章的表 3-1、图 3-2、「大厂与开源 M 个」只取 chapter 3；第 4 章（图 4-1…4-5）取全部。
- 第 2 章内容不随第 3 章变：改第 3 章数据后跑 `qa/ch2_equiv.py`，第 2 章源码和运行后 DOM 都必须和改前逐字节一致（只有章名在这次改章时变过）。

### 13.2 表 3-1 的列配置怎么写
`models.json → t31.groups[]` 每组一个 `cols` 列表，列名两种：
- 基本列：`release`、`price_in`、`price_out`、`license`、`params`（表头文字与提示在 `t31.basic`）。
- Bench 列：`benches[].key`。和表 2-1 共用同一个 key（同一个测试、同一版本、同一单位和子集）才能放进「与前沿同列」组；口径不同就新建一个 bench。
- 本章一个分数都没有的 bench 列自动不出（构建时打印「不出」），以后有了分数自动出现——现在 OSWorld 2.1 和 Chartography 就是这样（Chartography 第 3 章报的都是带工具 / Python 沙箱的分数，从严不填，写进各模型的 `row_tip`）。
- 图 4-x 和表里一律用完整模型名（`name`），不自造缩写；名字长的在窄屏折两行，`qa/browser_check.py` 断言第 4 章模型名不被截断。
- 组的分组线、前三名、色条与表 2-1 同规则；名次只在表 3-1 的模型里排。

### 13.3 第 3 章新增列的含义（`group: ext`）
| 列 | 测什么 | 只收哪种口径 |
|---|---|---|
| DeepSWE | 真实代码仓库里修 bug（Datacurve） | v1.1；v1.0 的不填 |
| ProgB（ProgramBench） | 从零写完整程序 | 「几乎做对」：一题测试通过 ≥95% 才算 1；按测试通过率的部分分不填 |
| Marathon（SWE-Marathon） | 要做几个小时的长程编码 | v1.1；更早或没写版本的不填 |
| HLE | Humanity's Last Exam | 全集、带工具；不带工具、纯文本子集不填 |
| GDPval（GDPval-AA） | AA 的职业任务两两比较 | v2，单位 Elo；取数时间不同会漂，note 里写 AA 现值 |
| CyberGym | 按描述复现真实漏洞 | 多为关掉防护；单位 % |
FrontierCode 2.0 列里带 `<sup>AA</sup>` 角标的是 Artificial Analysis 自己测的 FrontierCode-AA 2.0（132 题私有集），不是厂商自报。

### 13.4 散点图（图 4-4）规则
- 横轴输出价（对数），纵轴 AA v5.0.1。只画同时有 AA 和 API 价的模型；有 AA 没价格的进图注（现在是 Muse Wonder Full）。
- 点色＝厂商色；实心＝不开放权重，空心＝开放权重（`license.d` 不是「否」）。完全重合的点左右错开 12px。
- 标签：页面 JS `fitScatter` 按 AA 从高到低依次在 12 个候选位置里找不压点、不压别的标签、不出绘图区的位置；找不到就隐藏标签（悬停仍有完整提示）。`qa/browser_check.py` 断言可见标签互不重叠、不压点，并打印被隐藏的标签。
- 横轴刻度在 `figures.f44.xaxis.ticks`；有模型的输出价超出 `min` / `max` 时构建打印提示，去改范围。

### 13.5 配色规则与以后加新厂商（2026-11-22 第三版：官方品牌色系）
**规则：官方色优先，撞了取官方辅色，最后才派生。**
- 每家只从自己的官方色里选：`research/2026-11-22-brand-colors.json` 里的公司主色、公司辅色、产品主色、产品辅色（每个颜色带出处与可信度）。新厂商先按同样格式把官方色调研进 `research/`，只取官方站点 CSS、品牌手册这类一手来源。
- 固定：Anthropic #D97757；Google #4285F4；OpenAI 浅色主题 #000000、深色主题官方辅色 #FFFFFF（旧 ChatGPT 绿 #10A37F 已不是现行品牌色，不用）。图 2-1 的 TPU 算力泳道跟着 Google 的蓝走（`compute/ramps.json` 的 tpu 色阶是 #4285F4 同色相）。
- 在候选里做组合搜索，让 8 家两两最差的一对尽量大（正常视力 ΔE 与 CVD ΔE，深浅两种主题都算）；平手时公司主色 > 产品主色 > 辅色。深色底上看不清的颜色，取同一家官方色里更亮的；没有更亮的，才在同色相上提亮，记为派生。
- 官方色实在拉不开（只有黑白或和别家同一种蓝）的厂商，用派生色（中性灰等），最多 1–2 家；现在是 xAI（浅灰 / 中灰）和智谱（官方近黑 #141618 提亮的石墨灰）。派生灰要和 OpenAI 黑白、Nvidia 算力灰拉开（正常视力 ΔE ≥10）。
- 仍然撞色的对（现在是 Google↔Meta、Google↔DeepSeek，浅色还有 xAI↔DeepSeek）不再靠颜色区分，靠统一的厂商标识：「品牌色小方块 + 名字」——第 4 章每行模型名前（散点图除外：点本身就是品牌色方块，标签只留文字）、表 2-1 / 3-1 的行首、图例（按前沿 / 大厂 / 开源分组）都有。只用色块和文字，不画、不下载、不内嵌任何 Logo 或字标。

**色条上的文字必须可读**：表 2-1 / 2-2 / 3-1 的格内色条是厂商色按透明度叠在底色上，数字照常用正文色。`build_tables.py` 的 `bar_alpha_max` 对每家、每个主题二分求出色条最深允许的透明度（叠上行悬停后与正文色对比度仍 ≥ 6.0），名次分档（r1 / r2 / r3 / 普通＝74 / 48 / 30 / 14%）在这个上限内同比缩小，写进 `<style id="data-css">`。色条格里的角标和小字（†、*、AA、→$4）用正文色。不要用白字硬救（色条只盖住格子一部分）。`qa/contrast_check.py` 逐格核对 ≥ 4.5:1，换颜色、加厂商后必跑。

**加新厂商的步骤**
1. `vendors.json → vendors[]` 加一条：`group` 选 `frontier` / `bigtech` / `open`（决定进第 2 章还是第 3 章）；`css_var` 取一个没用过的（如 `--tv`）；`light` / `dark` 按上面的规则从官方色里选；`color_src`（浅 / 深各一句中英出处说明，派生要写原因）；`derived`（是否派生）；`legend_tip`；`t22_class`；`builtin_css: false`。位置决定它在表格分组和图例里的顺序。全部厂商的颜色都由构建写进 `<style id="data-css">`；前沿三家还写在报告原 CSS 开头的 `:root` 里，构建时会核对两处一致。
2. `timeline_lanes[]` 加一条泳道（`lane`、`vendor`），时间轴节点写进 `models.json → timeline_events`。
3. 颜色报告：`python3 qa/palette_check.py <dataviz 的 scripts 目录>`。它列出最终颜色与出处、8 家（或更多）两两全部的正常视力 / CVD ΔE、撞色的对（正常 <12 或 CVD <6）、与算力泳道三色的距离，并附 dataviz 校验器原样输出（官方色多为黑白蓝，校验器的亮度带 / 彩度下限 FAIL 是预期的，只作参考）。结果写进 `qa/palette_report.txt` 一起提交。
4. 跑第 3 节全部命令，外加 `python3 qa/rehearsal.py`（演练里就有一个虚构的新开源厂商 TestLab）。

