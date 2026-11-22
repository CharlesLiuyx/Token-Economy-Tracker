# 前端

> TL;DR：单文件 HTML，CSS / JS / Chart.js / 数据全内联。报告式外壳（24px 顶栏 + 左侧目录），
> 无圆角、无动效。时序图走 Chart.js，条形图与表格是原生 DOM（ADR-006）。文案走 i18n.yml，
> 术语释义走 terms.yml，悬停提示全站只有一个节点。
> 何时读我：加 / 改面板、调样式、改文案、动 build.py 渲染逻辑前。
> 最后核对日期：2026-11-22（外壳与图表整体改版；此前为 Linear 风格卡片页）

## 单文件产物

- `make build` 把 `site/template/index.html.j2` + `style.css` + `app.js` + `i18n.yml` +
  `terms.yml` + `site/vendor/chart.umd.min.js` + 当日展示数据渲染为 `site/index.html`。
- 时序图数据内联在 `<script id="dashboard-data">`；表格 / 条形图 / 卡片直接渲染成 HTML。
- 体积：日频序列只内联近 90 天；目标 gzip 后 < 600KB（2026-11-22 实测 144KB）。

## 外壳

- **顶栏 24px**：站名、区块导航、【返回 ×N】（仅跳转栈非空时出现）、构建时间，以及直接外露的
  三个常用控件：语言切换、浅色 / 深色切换、GitHub 链接（2026-11-22 按用户要求移出菜单）。
- **「更多」菜单**收纳低频控制：宽度三档（880 / 1160 缺省 / 100%）、字号三档、术语释义开关。
  偏好存 localStorage，`<head>` 内联脚本在首帧前写到
  `<html data-theme|width|fs|lang|terms>`，防闪。
- **左侧目录**（fixed）：一行切换「章节 / 资产 / ±」。章节＝区块（h2）→ 面板（h3）；资产＝带
  `data-toc="fig|tbl"` 的面板，自动编号「图 3-2」。区块条目带开关，收起会同时隐藏正文
  （标题保留 +「已收起」标记）；Ctrl 点开关或点 ± 是批量三态（全展开→收起，否则→展开）。
- **锚点跳转**：目标落在视口高 5% 处（下限＝顶栏高 + 8px），目标块浅色高亮 2 秒；目标在收起的
  区块里先展开。只有正文内锚点入返回栈（上限 5），目录与顶栏导航不入栈。
- 无圆角（`* { border-radius: 0 }`）、无 transition / animation / smooth scroll。
- 断点：≤1320px 两栏收成一栏并隐藏表格次要列（`.opt`）；≤1000px 目录降为顶部静态块，
  表格放弃吸顶换横向滚动。**任何宽度下都不允许横向溢出**——加宽表格前先算最窄正文列。

## 面板约定

- 每个面板 = `site/template/panels/<panel>.j2` + build.py 里一个生成函数，外壳用
  `_macros.j2` 的 `panel(id, title_key, source, kind, flush, note_key)`（`{% call %}` 包正文）
  或 `chart_panel(...)`。面板 id 固定为 `p-<id>`；`kind='fig'|'tbl'` 才进「资产」目录。
- 每个面板带新鲜度徽章；OpenRouter / Vercel 面板标题必须保留来源后缀。
- **时序图（Chart.js）**：`renderPanel(id, spec)`，只用 line / scatter / 叠加 bar。类目 x 轴的图
  用 index 模式提示（同一天全部系列，按数值降序）+ 十字指示线；跨数量级的图用对数轴
  （重点模型、GPU 走势、ARR）。图例 hover 聚光：其余系列淡出，同 `dataset.__group` 一起亮。
  图内文字 ≥12px。spec 占位符：`"__surface"`、`"__i18n:<key>"`、`ticks.__epochDays`、
  `legend.labels.__filterUnderscore`。
- **条形图（原生 DOM）**：`.bars` 网格，每行＝名称 / 条 / 数值 / 较 7 天前。条厚 20px，
  hover 用 outline 高亮，文本可选中可搜索。
- **表格**：`.data-table`，表头吸顶。`top` 取 `--thTop`（app.js 实测顶栏高度，ResizeObserver
  重测，禁止硬编码）；`border-collapse: separate`；sticky 表头的祖先不得有 overflow。
  `th[data-sort="num|text"]` 可点排序，单元格用 `data-v` 提供原始值，空值恒在末尾。
  `td.num`（右对齐 + nowrap + tabular-nums）只给短数值格。
- **配色**：同一厂商全页同色（build.py `VENDORS`，按 slug / 显示名关键字归属），同厂商多条线
  靠线型区分；未识别厂商用中性色 + 空心。GPU 走势按 sources.yml 顺序取 `PALETTE`。
- **变化量**：`series_delta(series, days)` 由每日快照现算，模板用 `| delta` / `| dcls` 过滤器
  或 `dcell` 宏渲染（涨绿跌红，「—」＝无可比快照）。
- **可信度**：关键数字标〔高 / 中 / 低〕（`ui.conf.*`）。ARR 估算：最近披露 ≤45 天〔中〕，
  更久〔低〕；披露锚点：公司一手〔高〕、媒体引述〔中〕、第三方估算〔低〕。

## 悬停提示（全站单例）

禁用原生 `title`。目标只声明 `data-tip`（纯文本，`\n` 换行）或 `data-tiph`（受信 HTML）；
需要翻译的用 `data-i18n-tip="<key>"` + `data-i18n-args`，app.js 写入 `data-tip`。一个 `#tip` 节点、
document 级事件委托、显示时定位一次（目标正下方左对齐，越界才滑入或翻到上方）。目录里被
截断的条目用 peek 形态原位展开。Chart.js 画布内的提示仍用其自带 tooltip（同样无圆角、无动画）。

## 术语释义

`site/template/terms.yml`：`词条: {aliases, zh, en}`。app.js 加载后扫正文文本节点自动包成
`<span class="term">`，每处出现都标，hover 现查词典。长词优先匹配，英数词做词边界校验；
标题、链接、`code`、徽章、已带提示的元素内部不标。释义写法：缩写先给全称，一句「它是什么」
+ 一句「本质在衡量什么」。新增面板用到新术语就补词条。

## i18n（zh/en，决策见 ADR-005）

**模板与 spec 不允许硬编码可见文案**，全部进 `site/template/i18n.yml`（扁平点分命名空间
ui / sec / panel / chart / meth）。tests/test_i18n.py 校验：zh/en 齐全、`{args}` 双语一致、
引用与目录双向对齐（无死 key；app.js 里用到的 key 必须以字面量出现在某个模板里）。

- 静态 DOM：`{{ t(key) }}` 渲染默认 zh，同元素标 `data-i18n`（textContent）/
  `data-i18n-html`（受信 HTML，仅 `<b>` / `<code>`）/ `data-i18n-tip` / `data-i18n-aria-label`。
- 图表 spec：build.py `L(key)` 生成 `"__i18n:<key>"`，app.js `resolveSpec` 解析。
- **数据内容也要双语**：每日速读（`text.zh` / `text.en`）、锚点备注（`note` / `note_en`）、观点场合
  （`role` / `role_en`）渲染为带 `data-zh` / `data-en` 的元素，切语言时一并替换；build 与
  tests/test_manual_data.py 校验英文必填且不含中文。只有外部原文不翻译：新闻标题、引语原话、
  模型 / 站点 / 卡型名。**验收标准：英文模式下页面可见文本不出现中文**（语言按钮除外）。
- 切语言 = 去掉术语标注 → 重写文案 → 重新标注 → 重建目录 → 重建图表 → 重算位置缓存。

## 性能约定

滚动帧内零几何查询：目录条目对应的文档位置一次性缓存（`recalc`），只在布局真正变化时重算
（resize、字号 / 宽度切换、区块收放、排序、load、fonts.ready）；主题切换不重算。scroll / resize
监听一律 passive + rAF 节流；同一帧先读后写；scrollspy 结果与上帧相同则不写 DOM。
