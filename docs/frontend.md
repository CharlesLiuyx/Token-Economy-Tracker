# 前端

> TL;DR：单文件 HTML，CSS/JS/Chart.js/数据全内联；面板 = panels/*.j2 + spec 函数 + renderPanel；
> 文案走 i18n.yml（zh/en 运行时切换）。
> 何时读我：加/改面板、调样式、改文案、动 build.py 渲染逻辑前。
> 最后核对日期：2026-07-24（新增 legend hover 高亮；此前：Linear 风格重构 +
> dark/light 双主题 + zh/en i18n）

## 单文件产物

- `make build` 把 `site/template/index.html.j2` + `style.css` + `app.js` +
  `site/vendor/chart.umd.min.js`（M4 引入）+ 当日展示数据渲染为 `site/index.html`。
- 数据内联在 `<script id="dashboard-data" type="application/json">`，
  前端从 `window.DASHBOARD` 读。无任何外部请求，离线可开。
- 体积控制：日频序列近 90 天，更早降采样为周频；全量历史留在 data/ 不进 HTML；
  目标 gzip 后 < 600KB。

## 面板约定（M4）

- 每个面板一个 `site/template/panels/<panel>.j2` 片段 + build.py 里一个 spec 生成函数；
  加减面板不动骨架。
- 图表统一走 `renderPanel(id, spec)` 薄封装，只允许 Chart.js 子集：
  line / bar / horizontalBar / area + tooltip。方便日后整体换库。
- 交互只用 Chart.js 自带 hover tooltip、legend 开关与 legend hover 高亮；不做缩放/刷选。
- legend hover 高亮（app.js `setEmphasis`）：hover 图例项时其余系列颜色淡出到 15%
  （只改 spec 里的十六进制色，原色缓存在 chart 实例上，onLeave 还原）。同一
  `dataset.__group` 的系列一起高亮——ARR 图的置信带/外推段/锚点靠它跟拟合线同组；
  不写 `__group` 则每系列自成一组。
- 每个面板带新鲜度徽章（数据来自 _status.json，ok/warn/stale 样式见 style.css）。
- 口径警示：OpenRouter / Vercel 面板标题必须保留来源后缀，Methodology 区写清
  「测的是什么、不是什么」。

## 主题

Linear 风格：中性色、1px 细边框、8px 圆角、紧凑排版、mono 数字。dark/light 双主题：

- token 集中在 style.css：`:root` 为 light 缺省（无 JS 时兜底），
  `:root[data-theme="dark"]` 覆盖。系列色 = build.py `PALETTE`（双主题可读，
  0=Anthropic clay / 1=OpenAI teal，与 CSS `--c-clay/--c-teal` 对应）。
- 初始主题由 index.html.j2 `<head>` 内联脚本在首帧前设定（localStorage `theme`
  覆盖 > 系统 `prefers-color-scheme`），防白闪；顶栏按钮切换并持久化。
- 全站动效原则：瞬时到位。顶栏锚点跳转不用 `scroll-behavior: smooth`（原生
  平滑滚动几百 ms 且不可调速，粘滞感来源）；主题切换硬切无颜色过渡。若日后
  重加过渡注意坑：图表同步重建（~30ms+）与 CSS 过渡同帧启动会吃掉动画首帧。
- 图表随主题重渲染：app.js 从 CSS 变量读色注入 Chart.defaults，销毁全部实例后
  按 `D.charts` 原 spec 深拷贝重建。spec 里的 `"__surface"` 占位符（锚点描边 /
  空心点填充）渲染时替换为当前面板底色。改 CSS 变量名需同步 app.js。

## i18n（zh/en，决策见 ADR-005）

**规则：模板与 spec 不允许硬编码可见文案**，全部进 `site/template/i18n.yml`
（key -> {zh, en}，扁平点分命名空间 ui/sec/panel/chart/meth）。
tests/test_i18n.py 校验：zh/en 齐全、`{args}` 双语一致、引用与目录双向对齐（无死 key）。

- 静态 DOM：模板 `{{ t(key) }}` 渲染默认语言 zh（无 JS 兜底），同元素标
  `data-i18n`（textContent，配 `| e`）/ `data-i18n-html`（受信 HTML，
  仅 <b>/<code> 级内联标签）/ `data-i18n-title` / `data-i18n-aria-label`；
  参数化文案用 `data-i18n-args`（JSON，`{name}` 占位，见 _macros.j2 badge）。
- 图表 spec：build.py `L(key)` 生成 `"__i18n:<key>"` 占位符（可嵌长串），
  app.js resolveSpec 按当前语言正则解析——与 `__surface` 同一管线；
  语言切换与主题切换共用 renderAll 销毁重建。
- 偏好：localStorage `lang` > `navigator.language`（zh* → zh，否则 en），
  head 内联脚本首帧前设 `data-lang`；顶栏按钮显示切换目标（EN / 中）。
- 面板宏约定：`chart_panel(id, title_key, source, note_key=...)` /
  `panel_head(title_key, source)` 一律传 key；数据内容（新闻标题、引语、
  站点/模型名、日期数字格式）不翻译。
