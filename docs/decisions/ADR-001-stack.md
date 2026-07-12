# ADR-001：技术栈与总体取舍

> 状态：已定稿（PLAN §11 定稿取舍的存档）。最后核对日期：2026-07-12

## 背景

多 harness（Cursor / Claude Code / Codex）接力迭代的每日数据仪表盘，零服务器。

## 决定

1. Python（requests/pyyaml/numpy/jinja2）做管道，不用 Node——数据处理生态 + 无 node_modules 噪音。
2. Chart.js vendored 内联，不自绘 SVG——换 tooltip/legend 交互与 AI 熟悉度，代价 ~200KB。
3. 单文件 HTML，不做多页应用——分发托管最简，体积用降采样守住。
4. ARR 锚点手工维护，不自动爬——低频高价值信息，人工录入质量更高。
5. 构建产物 site/index.html 提交入库——Pages 零配置，任何历史时刻页面可考古。

## 后果

依赖最小、任何模型都熟；体积上限 & 手工锚点的维护成本被接受。**勿重议**，除非
出现新事实（写新 ADR 替代本篇）。
