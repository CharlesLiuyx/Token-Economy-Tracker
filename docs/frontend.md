# 前端

> TL;DR：单文件 HTML，CSS/JS/Chart.js/数据全内联；面板 = panels/*.j2 + spec 函数 + renderPanel。
> 何时读我：加/改面板、调样式、动 build.py 渲染逻辑前。
> 最后核对日期：2026-07-12（M4 实施时充实 renderPanel 规格）

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
- 交互只用 Chart.js 自带 hover tooltip 与 legend 开关；不做缩放/刷选。
- 每个面板带新鲜度徽章（数据来自 _status.json，ok/warn/stale 样式见 style.css）。
- 口径警示：OpenRouter / Vercel 面板标题必须保留来源后缀，Methodology 区写清
  「测的是什么、不是什么」。

## 主题

neo-brutalist：奶油底 `#FDF6E3`、2px 黑描边、硬阴影 `4px 4px 0 #111`、mono 数字字体。
变量集中在 style.css `:root`，对齐参考图 `docs/AI MONETIZATION TRACKER.png`。
