---
name: ship
description: Token-Economy-Tracker 的发布流程。在这个项目里做完一件事（改代码、改文档、更新数据或内容）之后自动使用：测试、构建、提交、合入并推送 main、确认 GitHub Pages 部署成功。只有影响很大的破坏性改动才先问用户。用户说「发布」「上线」「推上去」「ship」时也用它。
---

# 发布（ship）

这个项目的约定：**做完一件事就发布，不攒着，不逐次请示**。用户已经为本仓库长期授权了
「推送 main + 部署」，所以除非命中下面的「先问再发」清单，直接走完全部步骤并在最后汇报。

## 先问再发（只有这些情况停下来问）

- 会改写或删除 `data/**/daily/` 历史快照（refetch 窗口内的正常回补不算）。
- 换数据源或换估算口径，导致已发布的数字整体跳变（例如改 ARR 模型使大数字变动 20% 以上）。
- 删除面板或数据源。
- 改 CI 权限、密钥、仓库设置，或需要 force push / 改写已推送的历史。
- `make test` 或 `make build` 不绿，而你无法在本次任务范围内修好。

界面改版、加面板、加数据源、修 bug、文档调整、日常数据与内容更新都**不用问**。

## 步骤

1. **自检**：`make test` 必须全绿；`make build` 重新生成 `site/index.html`（禁止手改它）。
   改了前端就用浏览器打开 `site/index.html`（file:// 直开，8000 端口常被占用）看一眼：
   无 console 报错、无横向溢出。
2. **文档同步**：行为改动对应的 docs 已在同一批改动里更新；`docs/worklog.md` 末尾追加一行
   `日期 | harness | 做了什么 | 下一步`（三句话以内）。
3. **提交**：只提交本次任务的改动（仓库里可能有别的 agent 在工作，不要动别人的改动）。
   按性质拆分：抓数产物 `data: YYYY-MM-DD`；功能 `feat:`；修复 `fix:`；纯文档 `docs:`；
   CI `ci:`。格式 `<type>: <summary>`，英文祈使句，≤72 字符（规范见 README）。
   小的后续修正并入尚未推送的对应提交，不堆 fixup 提交。
4. **合入 main 并推送**：
   - 在功能分支上：`git fetch origin && git rebase origin/main`（每日 bot 会往 main 推
     `data:` 提交，冲突几乎只会出在 `site/index.html` 和 `data/`——以 origin/main 的数据为准，
     然后重新 `make build`），再 `git checkout main && git merge --ff-only <分支> && git push origin main`，
     最后删掉已合入的本地分支。
   - 已在 main 上：`git pull --rebase origin main` 后 `git push origin main`。
   - push 被拒（远端有新提交）就重新 rebase 再推，不要 force。
5. **确认部署**：push 触发 `deploy.yml`。`gh run list --workflow=deploy.yml --limit 1` 拿到 run，
   `gh run watch <id> --exit-status` 等它结束。失败时**不要 rerun**（会产生同名 artifact 再失败），
   改用 `gh workflow run deploy.yml --ref main`；仍失败就读日志修，细节见 `docs/runbook.md`。
6. **验证线上**：`curl -s https://charlesliuyx.github.io/Token-Economy-Tracker/ | grep -o 'BUILD [0-9T:+-]*'`
   确认构建时间是刚才这次（CDN 可能滞后一两分钟）。
7. **汇报**：一两句话说明发布了什么、线上是否已更新；没验证到的直接说没验证到。
