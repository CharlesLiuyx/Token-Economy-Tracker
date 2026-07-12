# worklog（跨 harness 接力日志，append-only）

> 格式：`日期 | harness | 做了什么 | 下一步/坑`。每次会话结束追加一行，只追加不整理。

2026-07-09 | 人工+Claude | 定稿 PLAN.md（docs/PLAN.md），建 AGENTS.md/CLAUDE.md | 从 M0 开始实施
2026-07-12 | Claude Code | M0+M1 完成：脚手架/lib/Makefile/docs 骨架/15 单测；epoch+sdk+news 三源真实落盘（含 samples 三件套）；build 骨架页 90KB 离线可开 | M2 高风险源探测（openrouter/vercel/gpu，各写 ADR）；M3 ARR 锚点收集可并行。坑：Python 本机是 3.14（无 3.12），venv 正常；epoch CSV 实测 72 站点 11.2GW
2026-07-12 | Claude Code | M2+M3 完成：openrouter（frontend rankings ×3 端点，ADR-002）、vercel_gateway（RSC flight rawData 61 天，ADR-003）、gpu_prices（Vast.ai API，OCPI=Ornn 不可得，ADR-004）三源落盘+三件套；ARR 锚点 34 条（bootstrap 自 Epoch revenue CSV）+ derive/arr.py 加权对数拟合 + 8 单测；build 内嵌 7 数据块 319KB | 下一步 M4：panels/*.j2 + renderPanel + Chart.js vendor + 实时计数器。坑：vercel 是份额%非绝对量；openrouter 无日频端点（滚动 7 天口径）；vast gpu_name 拼错静默返回空
2026-07-12 | Claude Code | M4 完成：Chart.js 4.5.1 vendored；build.py 重写为 spec 函数 + 17 个 panels/*.j2 + renderPanel 薄封装 + ARR 每秒跳动计数器 + 新鲜度徽章 + Methodology 区；neo-brutalist 主题对齐参考图；gzip 97KB，file:// 双击可开，26 单测全绿。M5 的 daily.yml 已写好（cron 00:30 UTC + 失败自动开 Issue + Pages 部署）| 剩余：建 GitHub repo、开 Pages（Settings→Pages→Source: GitHub Actions）、跑通 3 天。坑：内嵌浏览器面板滚动截图有合成故障，验证页面用 headless Chrome --screenshot 更可靠；epoch timelines 与 sites 两表口径独立（14.3 vs 11.2 GW），增长图注释已写明
