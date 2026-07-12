# ARR 估算方法论

> TL;DR：手工锚点（口径必填）→ 对数空间加权最小二乘 → 外推 + 置信带；页面常驻「估算」徽章。
> 何时读我：改 scripts/derive/arr.py、加锚点、质疑大数字之前。
> 最后核对日期：2026-07-12（M3 实施时充实公式与单测说明）

## 数据

锚点在 `data/manual/arr_anchors.yml`，每条：
`company / date / value_usd / metric / source_url / note`。

**metric 口径必填**，混拟合会出鬼图：

- `run_rate_arr` —— 披露的年化运行率收入。**拟合只用这一种。**
- `projected_rev` —— 全年预测，仅展示为散点。
- `reported_rev` —— 事后实际收入，仅展示为散点。

## 模型（M3 实施）

1. 每家公司取 run_rate_arr 锚点，在 log 空间做加权最小二乘（近期权重高），
   得分段指数曲线；残差 → 置信带。
2. 外推：曲线延伸至今日 + 未来 N 月（页面画虚线区）。
3. 实时跳动：build 输出 `{arr_at_build, build_ts, usd_per_hour, mom_implied}`，
   前端每秒 `+= usd_per_hour / 3600`。**纯展示效果**，刷新回到 build 基准。

## 诚实性要求（PLAN §11 风险 2）

- 卡片常驻「估算」徽章 + 本文档锚链接。
- 走势图必须画锚点散点与置信带，让读者看到估算的地基。
- 异常口径（metric 非法值 / 缺 source_url）在 derive 阶段直接拒绝。
