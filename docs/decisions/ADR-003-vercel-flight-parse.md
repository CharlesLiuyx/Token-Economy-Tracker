# ADR-003：Vercel Gateway 解析 RSC flight 载荷内嵌 rawData

> 状态：已决策 2026-07-12

## 背景

vercel.com/ai-gateway/leaderboards 无 `__NEXT_DATA__`、无公开 API；数据以
Next.js App Router flight 载荷（`self.__next_f.push`）内嵌于 HTML，含 ~61 天
× 5 指标的每日模型份额（百分比）。

## 决定

拼接 flight 字符串块 → 定位 `"rawData":` → 括号配平截取数组。保留 tokens/cost/
requests 三指标、每日 top20 + others。不上无头浏览器。

## 后果

+ 一次 GET 拿 61 天历史；无 JS 运行时依赖。
− flight 格式是框架内部实现，改版风险最高的一个源；validate 硬卡（≥30 天、
  含 tokens、份额 0–100），断供时面板冻结显示旧数据 + stale 徽章（设计内降级）。
  两级 fallback 顺序：① 重探页面结构 ② 无头浏览器（均未实现，按需再做）。
