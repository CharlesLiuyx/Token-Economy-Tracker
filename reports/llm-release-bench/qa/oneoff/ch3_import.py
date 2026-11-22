#!/usr/bin/env python3
"""一次性脚本（2026-11-22，第 3 章「大厂与开源模型」）：把 research/2026-11-22-bigtech.json、research/2026-11-22-open.json
里的 16 个模型整理成 data/models.json 的条目（分数、价格、参数、许可证、提示文字中英两份），并加上：
  新 Bench 列（DeepSWE / ProgramBench / SWE-Marathon / HLE / GDPval-AA / CyberGym）、表 3-1 列配置 t31、
  图 3-2 时间轴节点、第 3 章快照、图 4-1…4-5 配置（由原图 3-1…3-3 改号扩展）、附录来源（两份研究文件去重）。
哪些厂商自报分数能填、填哪一个，按 research/decisions-ch3.md 的裁定逐格手写在下面的 CELLS 里；没填的写进行首提示 row_tip。
已经跑过，以后不要再跑（再跑会重复追加）。以后加模型直接改 data/models.json，见 MAINTAIN.md 第 5 节。"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(ROOT, 'data', 'models.json')
D = json.load(open(P, encoding='utf-8'))
assert not any(m['vendor'] in ('xai', 'meta', 'deepseek', 'moonshot', 'zhipu') for m in D['models']), '已经导入过'
RB = json.load(open(os.path.join(ROOT, 'research', '2026-11-22-bigtech.json'), encoding='utf-8'))
RO = json.load(open(os.path.join(ROOT, 'research', '2026-11-22-open.json'), encoding='utf-8'))
RM = {m['id']: m for m in RB['models'] + RO['models']}

def Z(zh, en): return {'zh': zh, 'en': en}
CFE = {'高': 'high', '中': 'medium', '低': 'low'}
def money(x):
    return '$%.2f' % x if abs(round(x, 2) - x) < 1e-9 else '$%g' % x
def num(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else str(v)
    return s

# ---------------------------------------------------------------- independent columns (AA / Vals / TB 4.0 Vals)
def aa(mid, setting_zh, setting_en, extra_zh='', extra_en=''):
    a = RM[mid]['independent']['aa']
    cost_zh = ('跑完整个指数每题约 %s。' % money(a['cost_per_task'])) if a.get('cost_per_task') else ''
    cost_en = ('About %s per task over the full index. ' % money(a['cost_per_task'])) if a.get('cost_per_task') else ''
    return {'d': str(a['v']), 'v': a['v'], 'src': 'artificial_analysis', 'cf': '高',
            'note': Z('Artificial Analysis v5.0.1，%s，精确值 %s。%s%s〔高〕' % (setting_zh, num(a['exact']), cost_zh, extra_zh),
                      'Artificial Analysis v5.0.1, %s, exact %s. %s%s[high]' % (setting_en, num(a['exact']), cost_en, extra_en))}
def rank(r, n):
    return r if isinstance(r, str) else '%d/%d' % (r, n)
def vals(mid, extra_zh='', extra_en=''):
    a = RM[mid]['independent']['vals']
    return {'d': '%.2f' % a['v'], 'v': a['v'], 'src': 'vals_ai', 'cf': '高',
            'note': Z('Vals Index v2.2（2026-11-19 更新），Vals 全榜 43 个模型里排第 %s。每题成本 %s。%s〔高〕' % (rank(a['rank'], 43).split('/')[0], money(a['cost_per_task']), extra_zh),
                      'Vals Index v2.2 (updated 2026-11-19), #%s of 43 on the full Vals leaderboard. Cost per task %s. %s[high]' % (rank(a['rank'], 43).split('/')[0], money(a['cost_per_task']), extra_en))}
def tb4(mid, extra_zh='', extra_en='', cf='高'):
    a = RM[mid]['independent']['tb4_vals']
    return {'d': '%.2f' % a['v'], 'v': a['v'], 'src': 'vals_ai', 'cf': cf,
            'note': Z('Vals 用 mini-SWE-agent 统一测（2026-11-19 更新），Vals 全榜 70 个模型里排第 %s。每题成本 %s。%s〔%s〕' % (rank(a['rank'], 70).split('/')[0], money(a['cost_per_task']), extra_zh, cf),
                      'Run by Vals with mini-SWE-agent (updated 2026-11-19), #%s of 70 on the full Vals leaderboard. Cost per task %s. %s[%s]' % (rank(a['rank'], 70).split('/')[0], money(a['cost_per_task']), extra_en, CFE[cf]))}
def c(v, zh, en, cf='中', d=None, src='release_table'):
    return {'d': d if d is not None else num(v), 'v': v, 'src': src, 'cf': cf,
            'note': Z(zh + '〔%s〕' % cf, en + ' [%s]' % CFE[cf])}
def caa(v, zh='Artificial Analysis 模型页的分项成绩（FrontierCode-AA 2.0，132 题私有集），max 档。',
        en='Component result on the Artificial Analysis model page (FrontierCode-AA 2.0, 132-task private set), max setting.'):
    x = c(v, zh, en, '中', src='artificial_analysis'); x['d'] = num(v) + '<sup>AA</sup>'; return x
def blank(zh, en, d='—'): return {'d': Z(d, d), 'tip': Z(zh, en)}

LIC = {
    'no': Z('否', 'No'), 'mit': Z('MIT', 'MIT'), 'mmit': Z('Modified MIT', 'Modified MIT'), 'custom': Z('自定义', 'Custom')}
def lic(kind, zh, en): return {'d': LIC[kind], 'tip': Z(zh, en)}
PROP = lic('no', '不开放权重，只能通过 API 或自家产品用。〔高〕', 'Weights are not released; available only through the API or the vendor\'s own products. [high]')
MIT_ = lic('mit', 'MIT 许可证：可以商用、可以修改，基本没有附加条件。〔高〕', 'MIT license: commercial use and modification allowed, with essentially no strings attached. [high]')
def par(d, zh, en): return {'d': d, 'tip': Z(zh, en)}
TAG_SUPER = lambda zh, en: {'text': Z('已取代', 'Superseded'), 'tip': Z(zh, en)}
TAG_RETIRE = lambda zh, en: {'text': Z('将下线', 'Retiring'), 'tip': Z(zh, en)}
TAG_PLAN = {'text': Z('仅订阅', 'Plan only'), 'tip': Z('没有 API，只在 Meta 的 Muse Code 订阅（Power Usage / Maximum Usage 两档）里能用。',
                                                    'No API; available only inside Meta\'s Muse Code subscription (Power Usage and Maximum Usage plans).')}

M = []
def add(**kw): M.append(kw)

# ================================================================ xAI
add(id='grok-4-7', name='Grok 4.7', short='Grok 4.7', vendor='xai', status='public', release='2026-09-21',
    price={'in': 2, 'out': 6, 'tip': Z('xAI 官方 API 标准价（提示不超过 200K token）：输入 $2、缓存输入 $0.50、输出 $6；超过 200K 是 $4 / $1 / $12。Grok 4.7 Fast（输出快一倍、价格翻倍）只在 Cursor 和 Grok Build 里有。〔高〕',
                                      'xAI standard API price (prompts up to 200K tokens): $2 input, $0.50 cached input, $6 output; above 200K, $4 / $1 / $12. Grok 4.7 Fast (twice the output speed at twice the price) is only in Cursor and Grok Build. [high]')},
    license=PROP,
    params=par('~2.1T / —', '总参数约 2.1T，出自 Decrypt 和 Epoch AI 的引述，xAI 官方文档没有写；激活参数没有公开。〔低〕',
               'About 2.1T total parameters, per Decrypt and Epoch AI; xAI\'s own docs do not say. Active parameters are not disclosed. [low]'),
    row_tip=Z('SpaceXSI（原 xAI）现在的旗舰，主打编码和知识工作，换了更大的新底座。价格和 Grok 4.6 一样。没有 Model Card。没填进表的：GDPval 1695（发布文没写是不是 v2）、CursorBench 46.3%、EEBench 64.0% 等本表没有的测试。',
              'The current flagship of SpaceXSI (formerly xAI), aimed at coding and knowledge work, on a larger new base model. Same price as Grok 4.6. No model card. Not in the table: GDPval 1695 (the launch post does not say whether it is v2), CursorBench 46.3%, EEBench 64.0% and other tests this table does not track.'),
    scores={
        'aa': aa('grok-4-7', 'xhigh 档（high 35.21、low 31.13）', 'xhigh setting (high 35.21, low 31.13)', '发布当天 AA 文章用的旧版指数是 46，不能混用。', "AA's launch-day article used the older index, where it scored 46; do not mix. "),
        'vals': vals('grok-4-7', '发布当天 Vals 在旧版指数上测得 60.22%。', 'On launch day Vals measured 60.22% on the older index. '),
        'tb4_vals': tb4('grok-4-7'),
        'tb4_vendor': c(37.6, 'xAI 的 Grok 4.7 发布文（9 月 21 日）分数表，xhigh 档；没写用的什么工具。AA 在 Grok Build 里测是 33%，Vals 测是 28.79%。',
                        "Benchmark table in xAI's Grok 4.7 launch post (Sep 21), xhigh setting; harness not stated. AA measured 33% in Grok Build and Vals 28.79%."),
        'deepswe': c(71.0, 'xAI 的 Grok 4.7 发布文，high 档（表里打了星号，其余各项是 xhigh）。', "xAI's Grok 4.7 launch post, high setting (starred in the table; the other rows are xhigh).", d='71.0'),
    })
add(id='grok-4-6', name='Grok 4.6', short='Grok 4.6', vendor='xai', status='public', release='2026-08-12',
    price={'in': 2, 'out': 6, 'tip': Z('xAI 官方 API 标准价（提示不超过 200K token）：$2 / 缓存 $0.50 / $6；超过 200K 是 $4 / $1 / $12。fast 版价格翻倍。〔高〕',
                                      'xAI standard API price (prompts up to 200K tokens): $2 / $0.50 cached / $6; above 200K, $4 / $1 / $12. The fast variant costs twice as much. [high]')},
    license=PROP,
    params=par('~1.5T / —', 'Grok 4.6 Model Card 说是「1.5T 级」模型家族；激活参数没有公开。〔中〕', 'The Grok 4.6 model card calls it a "1.5T-scale model family"; active parameters are not disclosed. [medium]'),
    row_tip=Z('Grok 4.7 的上一代，价格相同。没填进表的：FrontierCode 61.3%（是 v1.1 扩展版，不是 2.0）、Terminal-Bench 3.0 26.0%。Grok 4.7 发布文里给它的 DeepSWE 是 65.2%，Model Card 写 65.9%，表里用 Model Card。',
              'The generation before Grok 4.7, at the same price. Not in the table: FrontierCode 61.3% (the v1.1 Extended set, not 2.0) and Terminal-Bench 3.0 at 26.0%. The Grok 4.7 launch post gives it 65.2% on DeepSWE while the model card says 65.9%; the table uses the model card.'),
    scores={
        'aa': aa('grok-4-6', 'xhigh 档', 'xhigh setting', 'xAI 发布时引用的是旧版 AA 指数 61。', "xAI's launch post cited 61 on an older AA index. "),
        'tb4_vals': tb4('grok-4-6'),
        'tb4_vendor': c(20.3, 'xAI 在 Grok 4.7 发布文里给 Grok 4.6 的对照分数，high 档。', "Comparison score for Grok 4.6 in xAI's Grok 4.7 launch post, high setting."),
        'deepswe': c(65.9, 'Grok 4.6 Model Card §2.4，high 档，mini-SWE-agent，Datacurve 测，pass@1。xhigh 档是 67.0%。', 'Grok 4.6 model card §2.4, high setting, mini-SWE-agent, run by Datacurve, pass@1. 67.0% at xhigh.'),
        'swem': c(31.9, 'Grok 4.6 Model Card §2.5，v1.1，high 档，在 Grok Build 里跑，Abundant AI 测。', 'Grok 4.6 model card §2.5, v1.1, high setting, run in Grok Build by Abundant AI.'),
        'gdpval': c(1753, 'Grok 4.6 Model Card §3.1，v2，high 档，AA 测。', 'Grok 4.6 model card §3.1, v2, high setting, run by AA.'),
        'cygym': c(79.7, 'Grok 4.6 Model Card §7.1，high 档，不带防护，按平均复现率算。', 'Grok 4.6 model card §7.1, high setting, safeguards off, mean reproduction rate.'),
    },
    blank={'vals': blank('不在 Vals Index v2.2 榜上。Vals 9 月 21 日的更新里引用旧版指数 59.17%，不能和 v2.2 混用。',
                         "Not on the Vals Index v2.2 leaderboard. Vals' Sep 21 update cites 59.17% on the older index; do not mix with v2.2.")})
add(id='grok-4-5', name='Grok 4.5', short='Grok 4.5', vendor='xai', status='public', release='2026-07-08', release_star=True,
    release_tip=Z('7 月 8 日先上 API（xAI 发布说明），7 月 16 日发正式博文，7 月 22 日上消费端 App。', 'API first on Jul 8 (xAI release notes), launch post on Jul 16, consumer apps on Jul 22.'),
    price={'in': 2, 'out': 6, 'tip': Z('xAI 官方 API 标准价 $2 / $6。AA 页显示缓存打 85 折以下（约 $0.30），xAI 文档没单列。〔高〕',
                                      "xAI standard API price $2 / $6. AA lists cached input at about $0.30; xAI's docs do not break it out. [high]")},
    license=PROP,
    params=par('~1.5T / —', 'Grok 4.6 Model Card 说两者是同一个 1.5T 级家族；激活参数没有公开。〔中〕', 'The Grok 4.6 model card places both in the same 1.5T-scale family; active parameters are not disclosed. [medium]'),
    row_tip=Z('xAI 6 月以来的第一个文本模型。没填进表的：DeepSWE v1.0 62.0%（不是 v1.1）、SWE-Marathon 29.0%（没写版本）、ProgramBench 57.2%（按测试通过率算，不是「几乎做对」）、Terminal-Bench 2.1 83.3%。',
              "xAI's first text model since June. Not in the table: DeepSWE v1.0 at 62.0% (not v1.1), SWE-Marathon 29.0% (version not stated), ProgramBench 57.2% (share of tests passed, not the \"almost solved\" metric) and Terminal-Bench 2.1 at 83.3%."),
    scores={
        'tb4_vals': tb4('grok-4-5'),
        'deepswe': c(53.0, 'Grok 4.5 Model Card §2.2，v1.1，high 档，mini-SWE-agent，Datacurve 测。Grok 4.6 的卡里写的是 54.0%。', 'Grok 4.5 model card §2.2, v1.1, high setting, mini-SWE-agent, run by Datacurve. The Grok 4.6 card gives 54.0%.', d='53.0'),
        'gdpval': c(1535, 'Grok 4.5 Model Card §4.1，v2，high 档，AA 测。Grok 4.6 的卡里写的是 1526。', 'Grok 4.5 model card §4.1, v2, high setting, run by AA. The Grok 4.6 card gives 1526.'),
        'cygym': c(79.0, 'Grok 4.6 Model Card §7.1 里给 Grok 4.5 的分数，high 档，不带防护。', 'Score for Grok 4.5 in the Grok 4.6 model card §7.1, high setting, safeguards off.', d='79.0'),
    },
    blank={'aa': blank('Artificial Analysis 没给它算 v5.0.1 分数（页面显示 N/A）。xAI 引用的旧版 AA 指数是 56，不能混用。', "Artificial Analysis has no v5.0.1 score for it (the page shows N/A). xAI cites 56 on an older AA index; do not mix."),
           'vals': blank('不在 Vals Index v2.2 榜上；旧版指数是 51.53%（Vals 9 月 21 日的更新）。', "Not on the Vals Index v2.2 leaderboard; 51.53% on the older index (Vals' Sep 21 update).")})

# ================================================================ Meta
add(id='muse-wonder-full', name='Muse Wonder Full', short='Wonder Full', vendor='meta', status='restricted', release='2026-10-12', tag=TAG_PLAN,
    license=PROP, params=par('—', 'Meta 没有公布参数量。', 'Meta has not disclosed the parameter count.'),
    row_tip=Z('Muse Wonder 的加强版，没有 API，只在 Muse Code 订阅里用；API 把 Muse Wonder 调到 max 也不会切到它。没填进表的：OSWorld 78.4%（108 题全集、Meta 自己的框架，不是离线子集）、SWE-Marathon 57.5%（没写版本）、AutomationBench-AA 45.4%（AA 的严格计分版，不是 v1.0.6）、ExploitGym 20 个目标 flag（是个数不是 %）。',
              "A stronger version of Muse Wonder with no API, used only inside the Muse Code subscription; setting Muse Wonder to max on the API does not switch to it. Not in the table: OSWorld 78.4% (the full 108-task set on Meta's own harness, not the offline subset), SWE-Marathon 57.5% (version not stated), AutomationBench-AA 45.4% (AA's strict-scoring variant, not v1.0.6) and ExploitGym 20 intended flags (a count, not a %)."),
    scores={
        'aa': aa('muse-wonder-full', 'max 档', 'max setting', '没有 API 价格，所以 AA 没算每题成本。', 'No API price, so AA gives no cost per task. '),
        'vals': vals('muse-wonder-full', 'Vals 按 $4 / $20 算成本。', 'Vals prices it at $4 / $20. '),
        'tb4_vals': tb4('muse-wonder-full'),
        'tb4_vendor': c(57.1, 'Meta 的 Muse Wonder 发布表，max 档，成绩来自 AA。', "Meta's Muse Wonder launch table, max setting, score from AA."),
        'deepswe': c(79.0, 'Meta 的 Muse Wonder 发布表，v1.1，max 档，Datacurve 测，pass@1。', "Meta's Muse Wonder launch table, v1.1, max setting, run by Datacurve, pass@1.", d='79.0'),
        'progb': c(59.0, 'Meta 的 Muse Wonder 发布表，max 档，mini-SWE-agent，按「测试通过 ≥95% 的比例」算。', "Meta's Muse Wonder launch table, max setting, mini-SWE-agent, share of runs passing at least 95% of tests.", d='59.0'),
        'cygym': c(88.4, 'Muse Wonder Model Card §4，不带防护。', 'Muse Wonder model card §4, safeguards off.'),
    },
    blank={'price_in': blank('没有 API：只在 Muse Code 的 Power Usage / Maximum Usage 订阅里提供。Vals 按 $4 / $20（与 Muse Wonder 相同）算成本，AA 页没有价格。〔中〕',
                             'No API: offered only in the Muse Code Power Usage / Maximum Usage plans. Vals prices it at $4 / $20 (same as Muse Wonder); AA lists no price. [medium]'),
           'price_out': blank('没有 API：只在 Muse Code 的 Power Usage / Maximum Usage 订阅里提供。Vals 按 $4 / $20（与 Muse Wonder 相同）算成本，AA 页没有价格。〔中〕',
                              'No API: offered only in the Muse Code Power Usage / Maximum Usage plans. Vals prices it at $4 / $20 (same as Muse Wonder); AA lists no price. [medium]')})
add(id='muse-wonder', name='Muse Wonder', short='Wonder', vendor='meta', status='public', release='2026-10-12',
    price={'in': 4, 'out': 20, 'tip': Z('Meta Model API 标准价（muse-wonder-1.0）：输入 $4、缓存输入 $0.20、输出 $20，不收长上下文溢价。API 还标着 preview。〔高〕',
                                       'Meta Model API standard price (muse-wonder-1.0): $4 input, $0.20 cached input, $20 output, no long-context premium. Still marked preview on the API. [high]')},
    license=PROP, params=par('—', 'Meta 没有公布参数量。', 'Meta has not disclosed the parameter count.'),
    row_tip=Z('Meta 当前对外的旗舰。没填进表的：OSWorld 72.6%（108 题全集，不是离线子集）、SWE-Marathon 53.1%（没写版本）、AutomationBench-AA 39.1%（AA 的严格计分版）。',
              "Meta's current public flagship. Not in the table: OSWorld 72.6% (the full 108-task set, not the offline subset), SWE-Marathon 53.1% (version not stated) and AutomationBench-AA 39.1% (AA's strict-scoring variant)."),
    scores={
        'aa': aa('muse-wonder', 'max 档', 'max setting'),
        'vals': vals('muse-wonder', '发布当天旧版指数是 61.06%。', '61.06% on the older index at launch. '),
        'tb4_vals': tb4('muse-wonder'),
        'tb4_vendor': c(52.0, 'Meta 的 Muse Wonder 发布表，max 档，成绩来自 AA。', "Meta's Muse Wonder launch table, max setting, score from AA.", d='52.0'),
        'deepswe': c(78.8, 'Meta 的 Muse Wonder 发布表，v1.1，max 档，Datacurve 测。', "Meta's Muse Wonder launch table, v1.1, max setting, run by Datacurve."),
        'progb': c(50.0, 'Meta 的 Muse Wonder 发布表，max 档，mini-SWE-agent，按「测试通过 ≥95% 的比例」算。', "Meta's Muse Wonder launch table, max setting, mini-SWE-agent, share of runs passing at least 95% of tests.", d='50.0'),
    })
add(id='muse-ember', name='Muse Ember', short='Ember', vendor='meta', status='public', release='2026-11-09',
    price={'in': 0.1, 'out': 0.5, 'tip': Z('Meta Model API 标准价（muse-ember-1.0）：输入不超过 200K token 时 $0.10 / 缓存 $0.004 / 输出 $0.50；超过 200K 整单按 $0.30 / $1.50 算。〔高〕',
                                         'Meta Model API standard price (muse-ember-1.0): with input up to 200K tokens, $0.10 / $0.004 cached / $0.50 output; above 200K the whole request bills at $0.30 / $1.50. [high]')},
    license=PROP, params=par('—', 'Meta 没有公布参数量。', 'Meta has not disclosed the parameter count.'),
    row_tip=Z('Meta 最小最省的模型，和 Haiku 5.5 同价。没填进表的：Agents\' Last Exam 61.6%（是 v1.0 的 Linux 子集，不是 v1.1）、OSWorld 69.5%（108 题全集）、AutomationBench-AA 37.8%（AA 的严格计分版）。',
              "Meta's smallest, cheapest model, priced like Haiku 5.5. Not in the table: Agents' Last Exam 61.6% (the v1.0 Linux subset, not v1.1), OSWorld 69.5% (the full 108-task set) and AutomationBench-AA 37.8% (AA's strict-scoring variant)."),
    scores={
        'aa': aa('muse-ember', 'max 档（xhigh 34.11）', 'max setting (xhigh 34.11)'),
        'vals': vals('muse-ember', 'Vals 说它是榜上每题成本最低的模型。', 'Vals calls it the cheapest per test on the index. '),
        'tb4_vals': tb4('muse-ember'),
        'tb4_vendor': c(40.9, 'Meta 的评测方法说明（11 月），max 档，AA 在 mini-SWE-agent 里测。', "Meta's evaluation methodology note (November), max setting, run by AA with mini-SWE-agent."),
        'fc2': caa(27.2, 'Meta 的 Muse Ember 发布文，引用 AA 测的 FrontierCode-AA 2.0（132 题私有集），max 档。', "Meta's Muse Ember launch post, citing AA's FrontierCode-AA 2.0 run (132-task private set), max setting."),
    })
add(id='muse-spark-open', name='Muse Spark Open', short='Spark Open', vendor='meta', status='public', release='2026-10-15',
    price={'in': 1.25, 'out': 4.25, 'tip': Z('开放权重，Meta 自家 API 不托管。价格是 AA 和 Vals 列的第三方托管价（Baseten、Fireworks、Together AI 等），各家可能不同；和 Muse Spark 1.3 的 API 价一样。〔中〕',
                                           "Open weights; not hosted on Meta's own API. Price is the third-party hosting rate listed by AA and Vals (Baseten, Fireworks, Together AI and others) and may vary by provider; it matches Muse Spark 1.3's API price. [medium]")},
    license=lic('custom', 'Muse Model License：自定义许可，商用有限制；Hugging Face 上的权重要人工审批才能下载。〔中〕', 'Muse Model License: custom, with limited commercial use; the Hugging Face weights require manual approval to download. [medium]'),
    params=par('816B / 42B', 'Hugging Face 模型卡：总参数 816B，激活 42B。〔高〕', 'Hugging Face model card: 816B total, 42B active. [high]'),
    row_tip=Z('Meta 第一个大尺寸开放权重模型。没填进表的：OSWorld-Verified 80.4%（另一个测试集）、Terminal-Bench 2.1 76.4%、HLE 不带工具的 26.1%（Diamond 子集）。Vals 测的 Terminal-Bench 4.0 只有 6.57%，可能是第三方托管或接入问题。',
              "Meta's first large open-weight model. Not in the table: OSWorld-Verified 80.4% (a different test set), Terminal-Bench 2.1 at 76.4% and HLE without tools at 26.1% (Diamond subset). Vals' Terminal-Bench 4.0 run gives only 6.57%, possibly a hosting or integration issue."),
    scores={
        'aa': aa('muse-spark-open', 'xhigh 档', 'xhigh setting', 'Meta 发布时引用的旧版 v4.3 是 39，两版不能比。', "Meta's launch cited 39 on the older v4.3; the two versions are not comparable. "),
        'vals': vals('muse-spark-open'),
        'tb4_vals': tb4('muse-spark-open', '远低于同家其他型号（Ember 39.39%），可能是第三方托管或接入问题。', 'Far below the rest of the family (Ember scores 39.39%); possibly a third-party hosting or integration issue. ', cf='低'),
        'deepswe': c(60, 'Muse Spark Open 模型卡，v1.1，Muse Code 工具，成绩来自 AA。', 'Muse Spark Open model card, v1.1, Muse Code harness, score from AA.'),
        'hle': c(61.0, 'Muse Spark Open 模型卡，带工具，xhigh 档。', 'Muse Spark Open model card, with tools, xhigh setting.', d='61.0'),
        'gdpval': c(1401, 'Muse Spark Open 模型卡，v2，xhigh 档，AA 测。', 'Muse Spark Open model card, v2, xhigh setting, run by AA.'),
    })

# ================================================================ DeepSeek
DS_PAR = par('552B / 8–16B', 'Hugging Face 模型卡：主干 552B（safetensors 里算上 196B 的 Engram 记忆和视觉编码器是 763B）；激活参数预填充 8B、解码 16B。〔高〕',
             'Hugging Face model card: a 552B backbone (763B in the safetensors, counting the 196B Engram memory and the vision encoder); 8B active in prefill, 16B in decode. [high]')
add(id='deepseek-v4-1-flash-1017', name='DeepSeek-V4.1-Flash-1017', short='V4.1-Flash-1017', fig='DS V4.1-Flash-1017', vendor='deepseek', status='public', release='2026-10-17',
    price={'in': 0.3, 'out': 1.2, 'tip': Z('DeepSeek 官方价（高峰）：输入 $0.30、输出 $1.20；空闲时段半价 $0.15 / $0.60；缓存命中 $0.006。API 名 deepseek-flash 现在指向它。〔高〕',
                                         'DeepSeek list price (peak): $0.30 input, $1.20 output; half price off-peak ($0.15 / $0.60); cached input $0.006. The API name deepseek-flash now points to it. [high]')},
    license=MIT_, params=DS_PAR,
    row_tip=Z('DeepSeek 现役模型，权重和 API 同一天放出。不少对照分数出自 Moonshot 的 Kimi K3.1 Pro 模型卡（多数是 Moonshot 用 Claude Code 跑的）。没填进表的：OSWorld V2.1 69.3%（Moonshot 的表，没写是不是离线子集）、HLE 不带工具 42.6%。',
              "DeepSeek's current model; weights and API shipped the same day. Many comparison scores come from Moonshot's Kimi K3.1 Pro model card (mostly Moonshot's own runs in Claude Code). Not in the table: OSWorld V2.1 69.3% (Moonshot's table; offline subset not stated) and HLE without tools at 42.6%."),
    scores={
        'aa': aa('deepseek-v4-1-flash-1017', 'max 档（high 28.64）', 'max setting (high 28.64)'),
        'vals': vals('deepseek-v4-1-flash-1017'),
        'tb4_vals': tb4('deepseek-v4-1-flash-1017'),
        'tb4_vendor': c(42.3, 'DeepSeek 模型卡，Claude Code 工具（见卡片脚注）。Moonshot 的表里同为 42.3%。', "DeepSeek's model card, Claude Code harness (per the card's footnote). Moonshot's table gives the same 42.3%."),
        'ale': c(37.7, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数，v1.1 全部 122 题。DeepSeek 自己报 35.4%，没写版本。', "Comparison score in Moonshot's Kimi K3.1 Pro model card, v1.1, all 122 tasks. DeepSeek itself reports 35.4% without a version."),
        'auto': c(60.5, 'DeepSeek 模型卡，AutomationBench v1.0.6；没写推理强度（V4.1 的卡全部按 max 报）。', "DeepSeek's model card, AutomationBench v1.0.6; reasoning effort not stated (the V4.1 card reports everything at max)."),
        'chart': c(83.0, 'DeepSeek 模型卡，带工具。Moonshot 的表里同为 83.0%。', "DeepSeek's model card, with tools. Moonshot's table gives the same 83.0%.", d='83.0'),
        'tbsci': c(9.3, 'Moonshot 在 Kimi K3.1 Pro 模型卡脚注里写的自测分数。表里那一格写的 15.7% 其实是旧版 V4.1-Flash 的官方榜成绩。', "Moonshot's own run, given in a footnote to its Kimi K3.1 Pro model card. The 15.7% printed in that table is actually the older V4.1-Flash's official leaderboard score.", cf='低'),
        'fc2': caa(28.5),
        'deepswe': c(77.0, 'DeepSeek 模型卡，v1.1，Mini-SWE-V2 工具（见卡片脚注）。', "DeepSeek's model card, v1.1, Mini-SWE-V2 harness (per the card's footnote).", d='77.0'),
        'progb': c(29.1, 'DeepSeek 模型卡；Moonshot 的表里同为 29.1%，按「几乎做对」算。', "DeepSeek's model card; Moonshot's table gives the same 29.1%, on the \"almost solved\" metric."),
        'swem': c(40.0, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数，v1.1。', "Comparison score in Moonshot's Kimi K3.1 Pro model card, v1.1.", d='40.0'),
        'hle': c(58.8, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数，全集、带工具。DeepSeek 自己只报了不带工具的 42.6%。', "Comparison score in Moonshot's Kimi K3.1 Pro model card, full set, with tools. DeepSeek itself reports only the no-tools 42.6%."),
        'gdpval': c(1746, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数，v2，引用 AA。AA 模型页现在是 1745.8。', "Comparison score in Moonshot's Kimi K3.1 Pro model card, v2, citing AA. The AA model page now shows 1745.8."),
    })
add(id='deepseek-v4-1-flash', name='DeepSeek-V4.1-Flash', short='V4.1-Flash', fig='DS V4.1-Flash', vendor='deepseek', status='public', release='2026-09-10',
    tag=TAG_SUPER('10 月 17 日起 API 上被 V4.1-Flash-1017 取代：现在调 deepseek-flash 实际由 1017 服务。权重仍可下载。', 'Replaced on the API by V4.1-Flash-1017 on Oct 17: calls to deepseek-flash are now served by -1017. The weights remain available.'),
    price={'in': 0.3, 'out': 1.2, 'tip': Z('和 1017 同价：高峰 $0.30 / $1.20，空闲时段半价。〔高〕', 'Same price as -1017: $0.30 / $1.20 at peak, half off-peak. [high]')},
    license=MIT_, params=DS_PAR,
    row_tip=Z('1017 的前一版，权重和 API 同一天放出。没填进表的：Agents\' Last Exam 31.8%（没写版本）、HLE 不带工具 36.8%。',
              "The version before -1017; weights and API shipped the same day. Not in the table: Agents' Last Exam 31.8% (version not stated) and HLE without tools at 36.8%."),
    scores={
        'tb4_vals': tb4('deepseek-v4-1-flash'),
        'tb4_vendor': c(31.2, 'DeepSeek 模型卡，max 档，DeepSeek Harness 的 Minimal 模式，1M 上下文。', "DeepSeek's model card, max setting, DeepSeek Harness in Minimal mode, 1M context."),
        'auto': c(54.8, 'DeepSeek 模型卡，max 档，官方脚手架；1017 的卡里标的是 v1.0.6。', "DeepSeek's model card, max setting, official scaffold; the -1017 card labels it v1.0.6."),
        'chart': c(78.9, 'DeepSeek 模型卡，带工具，max 档，Claude Code，512K 上下文。', "DeepSeek's model card, with tools, max setting, Claude Code, 512K context."),
        'tbsci': c(15.7, 'Terminal-Bench-Science 官方榜成绩，由 Moonshot 在 Kimi K3.1 Pro 模型卡里引用。', "Official Terminal-Bench-Science leaderboard score, cited in Moonshot's Kimi K3.1 Pro model card.", cf='低'),
        'deepswe': c(74.2, 'DeepSeek 模型卡，v1.1，max 档，mini-SWE。换成 Claude Code 是 69.8%。', "DeepSeek's model card, v1.1, max setting, mini-SWE. 69.8% in Claude Code."),
        'progb': c(20.3, 'DeepSeek 模型卡，Almost@1（「几乎做对」），max 档。', "DeepSeek's model card, Almost@1 (\"almost solved\"), max setting."),
        'hle': c(63.9, 'DeepSeek 模型卡，带工具，max 档。', "DeepSeek's model card, with tools, max setting."),
        'cygym': c(88.1, 'DeepSeek 模型卡，max 档。', "DeepSeek's model card, max setting."),
    },
    blank={'aa': blank('AA 把它标成已停用，没算 v5.0.1 指数。', 'AA marks it deprecated and computes no v5.0.1 index.'),
           'vals': blank('不在 Vals Index v2.2 榜上。', 'Not on the Vals Index v2.2 leaderboard.')})
add(id='deepseek-v4-pro-0813', name='DeepSeek-V4-Pro-0813', short='V4-Pro-0813', fig='DS V4-Pro-0813', vendor='deepseek', status='public', release='2026-08-13',
    price={'in': 1.32, 'out': 3.96, 'tip': Z('DeepSeek 官方价（高峰）$1.32 / $3.96，空闲时段半价 $0.66 / $1.98；缓存命中 $0.044。不支持看图。〔高〕',
                                           'DeepSeek list price (peak) $1.32 / $3.96, half off-peak ($0.66 / $1.98); cached input $0.044. No image input. [high]')},
    license=MIT_,
    params=par('1.6T / 49B', 'Hugging Face 模型卡：总参数 1.6T（safetensors 里算上 DSpark 草稿模块是 1.65T），激活 49B。〔高〕', 'Hugging Face model card: 1.6T total (1.65T in the safetensors, counting the DSpark draft module), 49B active. [high]'),
    row_tip=Z('V4-Pro 的正式版。9 月 10 日宣布下线，之后两次改口；11 月 22 日官方价格页仍列着 deepseek-v4-pro。没填进表的：Agents\' Last Exam 25.7%（只是 CLI 子集）；它自己的模型卡里 AutomationBench 写 31.8%（Public 子集，较早版本）。',
              "The GA release of V4-Pro. Its retirement was announced on Sep 10 and reversed twice since; the official pricing page still lists deepseek-v4-pro on Nov 22. Not in the table: Agents' Last Exam 25.7% (CLI subset only); its own model card gives AutomationBench 31.8% (Public subset, an earlier version)."),
    scores={
        'aa': aa('deepseek-v4-pro-0813', 'max 档（high 20.8）', 'max setting (high 20.8)'),
        'vals': vals('deepseek-v4-pro-0813'),
        'tb4_vals': tb4('deepseek-v4-pro-0813'),
        'tb4_vendor': c(12.4, 'DeepSeek 在 V4.1-Flash 模型卡里给它的对照分数，max 档。', "Comparison score in DeepSeek's V4.1-Flash model card, max setting."),
        'auto': c(43.2, 'DeepSeek 在 V4.1-Flash 模型卡里给的对照分数；Z.ai 的表里同为 43.2%（v1.0.6）。', "Comparison score in DeepSeek's V4.1-Flash model card; Z.ai's table gives the same 43.2% (v1.0.6)."),
        'fc2': caa(17.1),
        'deepswe': c(62.7, 'DeepSeek 模型卡；后来的 V4.1-Flash 卡标明是 v1.1。', "DeepSeek's model card; the later V4.1-Flash card labels it v1.1."),
        'progb': c(15.5, 'DeepSeek 在 V4.1-Flash 模型卡里给的对照分数，Almost@1。', "Comparison score in DeepSeek's V4.1-Flash model card, Almost@1."),
        'hle': c(60.0, 'DeepSeek 模型卡，带工具。', "DeepSeek's model card, with tools.", d='60.0'),
        'gdpval': c(1590, 'Z.ai 在 GLM-5.3 模型卡里给的对照分数，v2。AA 模型页现在是 1455.6，取数时间不同。', "Comparison score in Z.ai's GLM-5.3 model card, v2. The AA model page now shows 1455.6; the two were taken at different times.", cf='低'),
        'cygym': c(83.3, 'DeepSeek 模型卡。', "DeepSeek's model card."),
    })

# ================================================================ Moonshot
add(id='kimi-k3-1-pro', name='Kimi K3.1 Pro', short='K3.1 Pro', vendor='moonshot', status='public', release='2026-10-24',
    release_tip=Z('10 月 24 日 API 和 App 上线；权重约 11 月 4 日放出（Hugging Face 仓库 11 月 2 日建立）。', 'API and apps went live on Oct 24; weights followed around Nov 4 (Hugging Face repo created Nov 2).'),
    price={'in': 2, 'out': 10, 'tip': Z('Moonshot 官方价 $2 / $10；缓存命中 $0.20，写缓存另计。批量接口打 6 折。快 2–3 倍的 Highspeed 版 $4 / $20。〔高〕',
                                       'Moonshot list price $2 / $10; cached input $0.20, cache writes billed separately. Batch API at 60% of list. The 2–3× faster Highspeed variant costs $4 / $20. [high]')},
    license=lic('custom', 'Kimi K3.1 Pro License：MIT 式的自定义许可。任意 12 个月收入超过 2,000 万美元的 MaaS 业务要另签协议；月活超 1 亿或月收入超 2,000 万美元的产品要在界面上显示「Kimi K3.1-Pro」。〔高〕',
                'Kimi K3.1 Pro License: a custom, MIT-style license. MaaS businesses with more than $20M revenue in any 12 months need a separate agreement; products with over 100M monthly users or $20M monthly revenue must display "Kimi K3.1-Pro". [high]'),
    params=par('2.8T / 104B', 'Moonshot 模型卡：总参数 2.8T，激活 104B。〔高〕', 'Moonshot model card: 2.8T total, 104B active. [high]'),
    row_tip=Z('开放权重里 AA 第一，Vals 测的 Terminal-Bench 4.0 排第 4。没填进表的：OSWorld V2.1 79.6%（模型卡没说是不是离线子集）、AutomationBench-AA 73.3%（AA 的部分分口径，不是 v1.0.6）。',
              "Top open-weight model on the AA Index, and fourth on Vals' Terminal-Bench 4.0. Not in the table: OSWorld V2.1 79.6% (the card does not say whether it is the offline subset) and AutomationBench-AA 73.3% (AA's partial-credit variant, not v1.0.6)."),
    scores={
        'aa': aa('kimi-k3-1-pro', 'max 档', 'max setting', 'v5.0.1 上开放权重模型第一。', 'The top open-weight model on v5.0.1. '),
        'vals': vals('kimi-k3-1-pro'),
        'tb4_vals': tb4('kimi-k3-1-pro'),
        'tb4_vendor': c(65.7, 'Moonshot 模型卡，Claude Code 工具。AA 测是 67.2%。', "Moonshot's model card, Claude Code harness. AA measured 67.2%."),
        'ale': c(43.2, 'Moonshot 模型卡，v1.1 正式版全部 122 题，Kimi Code 工具。', "Moonshot's model card, the official v1.1 release, all 122 tasks, Kimi Code harness."),
        'chart': c(90.2, 'Moonshot 模型卡，带 Python 沙箱，5 次平均。', "Moonshot's model card, with a Python sandbox, averaged over 5 runs."),
        'tbsci': c(38.1, 'Moonshot 模型卡，Claude Code 工具。AA 测是 34.3%。', "Moonshot's model card, Claude Code harness. AA measured 34.3%."),
        'fc2': caa(25.5),
        'deepswe': c(75.5, 'Moonshot 模型卡，v1.1，Claude Code 工具。', "Moonshot's model card, v1.1, Claude Code harness."),
        'progb': c(31.5, 'Moonshot 模型卡，二值计分（一题测试通过 ≥95% 才算 1），Claude Code 工具。', "Moonshot's model card, binary scoring (a task counts only if at least 95% of its tests pass), Claude Code harness."),
        'swem': c(51.7, 'Moonshot 模型卡，v1.1，Claude Code 工具。', "Moonshot's model card, v1.1, Claude Code harness."),
        'hle': c(70.0, 'Moonshot 模型卡，全集、带工具，max 档。不带工具是 51.1%。', "Moonshot's model card, full set, with tools, max setting. 51.1% without tools.", d='70.0'),
        'gdpval': c(1846, 'Moonshot 模型卡，v2，引用 AA。AA 模型页现在是 1860.6。', "Moonshot's model card, v2, citing AA. The AA model page now shows 1860.6."),
    })
add(id='kimi-k3', name='Kimi K3', short='K3', vendor='moonshot', status='public', release='2026-07-16',
    release_tip=Z('7 月 16 日 API 和 App 上线（博文署北京时间 7 月 17 日）；完整权重 7 月 27 日放出。', 'API and apps went live on Jul 16 (the blog is dated Jul 17 Beijing time); full weights followed on Jul 27.'),
    price={'in': 3, 'out': 15, 'tip': Z('Moonshot 官方价 $3 / $15，缓存命中 $0.30；比后继的 K3.1 Pro 还贵。〔高〕', 'Moonshot list price $3 / $15, cached input $0.30; pricier than its successor K3.1 Pro. [high]')},
    license=lic('custom', 'Kimi K3 License：自定义许可（从 K3 起不再叫修改版 MIT）。任意 12 个月收入超过 2,000 万美元的 MaaS 业务要另签协议。〔高〕',
                'Kimi K3 License: custom (from K3 on it is no longer called modified MIT). MaaS businesses with more than $20M revenue in any 12 months need a separate agreement. [high]'),
    params=par('2.8T / 104B', 'Moonshot 模型卡：总参数 2.8T，激活 104B。〔高〕', 'Moonshot model card: 2.8T total, 104B active. [high]'),
    row_tip=Z('K3.1 Pro 的上一代。没填进表的：Agents\' Last Exam 28.3%（没写版本）、OSWorld-Verified 84.8% 和 OSWorld 2.0 58.3%（都不是 2.1 离线子集）。Moonshot 自己报的 ProgramBench 77.8% 是部分分口径，AutomationBench 30.8% 是 600 题公开子集，SWE-Marathon 42.0% 用的是 v1.1 定稿前的题，所以表里用了别家表格里口径一致的数。',
              "The generation before K3.1 Pro. Not in the table: Agents' Last Exam 28.3% (version not stated), OSWorld-Verified 84.8% and OSWorld 2.0 58.3% (neither is the 2.1 offline subset). Moonshot's own ProgramBench 77.8% is partial credit, its AutomationBench 30.8% is the 600-task public subset and its SWE-Marathon 42.0% predates the final v1.1 tasks, so the table uses like-for-like numbers from other vendors' tables."),
    scores={
        'vals': vals('kimi-k3'),
        'tb4_vals': tb4('kimi-k3'),
        'tb4_vendor': c(12.6, 'DeepSeek 在 V4.1-Flash 模型卡里给的对照分数，max 档。AA 测也是 12.6%。', "Comparison score in DeepSeek's V4.1-Flash model card, max setting. AA also measured 12.6%."),
        'auto': c(46.7, 'DeepSeek 和 Z.ai 的表里都给 46.7%（v1.0.6）。', "Both DeepSeek's and Z.ai's tables give 46.7% (v1.0.6)."),
        'chart': c(68.1, 'DeepSeek 在 V4.1-Flash 模型卡里给的对照分数，带工具。', "Comparison score in DeepSeek's V4.1-Flash model card, with tools."),
        'deepswe': c(67.5, 'Moonshot 模型卡，v1.1，Kimi Code 工具；用 mini-SWE-agent 在官方榜上是 67.3%。', "Moonshot's model card, v1.1, Kimi Code harness; 67.3% with mini-SWE-agent on the official leaderboard."),
        'progb': c(17.5, 'DeepSeek 和 Z.ai 的表里都给 17.5%（「几乎做对」）。', "Both DeepSeek's and Z.ai's tables give 17.5% (\"almost solved\")."),
        'swem': c(48.1, 'Z.ai 在 GLM-5.3 模型卡里给的对照分数，v1.1。', "Comparison score in Z.ai's GLM-5.3 model card, v1.1."),
        'hle': c(56.0, 'Moonshot 模型卡，全集、带工具。DeepSeek 和 Z.ai 的表里给的是 59.8%。', "Moonshot's model card, full set, with tools. DeepSeek's and Z.ai's tables give 59.8%.", d='56.0'),
        'gdpval': c(1686, 'Moonshot 模型卡，v2，引用 AA（7 月 23 日取数）。', "Moonshot's model card, v2, citing AA (as of Jul 23)."),
        'cygym': c(80.0, 'DeepSeek 和 Z.ai 的表里都给 80.0%。', "Both DeepSeek's and Z.ai's tables give 80.0%.", d='80.0'),
    },
    blank={'aa': blank('AA 把 K3 标成已停用：max 档没有 v5.0.1 指数，只有 low 档 17.42。', 'AA marks K3 deprecated: no v5.0.1 index at max, only 17.42 at the low setting.')})
add(id='kimi-k2-7-code', name='Kimi K2.7 Code', short='K2.7 Code', vendor='moonshot', status='public', release='2026-06-12',
    tag=TAG_RETIRE('10 月 31 日起不再对新 API 用户开放，计划 12 月底下线。', 'Closed to new API users since Oct 31; due to retire by end of December.'),
    price={'in': 0.95, 'out': 4, 'tip': Z('Moonshot 官方价 $0.95 / $4.00，缓存命中 $0.19；Highspeed 版 $1.90 / $8.00。〔高〕', 'Moonshot list price $0.95 / $4.00, cached input $0.19; Highspeed $1.90 / $8.00. [high]')},
    license=lic('mmit', '修改版 MIT 许可（Moonshot 的原话是 Modified MIT）。K3 起改用自定义许可证。〔高〕', 'A modified MIT license (Moonshot\'s own term). From K3 on, Moonshot switched to custom licenses. [high]'),
    params=par('1T / 32B', 'Moonshot 模型卡：总参数 1T，激活 32B。〔高〕', 'Moonshot model card: 1T total, 32B active. [high]'),
    row_tip=Z('K2 系列的编码版。没有可以横向比的分数：AA 列了它但没算 v5.0.1 指数；ProgramBench 53.6% 没写是哪种计分。',
              'The coding variant of the K2 series. No comparable scores: AA lists it but computes no v5.0.1 index, and its ProgramBench 53.6% does not say which scoring it uses.'),
    scores={},
    blank={'aa': blank('AA 列了它，但没算 v5.0.1 指数。', 'AA lists it but computes no v5.0.1 index.'),
           'vals': blank('不在 Vals Index v2.2 榜上。', 'Not on the Vals Index v2.2 leaderboard.'),
           'tb4_vals': blank('不在 Vals 的 Terminal-Bench 4.0 榜上。', "Not on Vals' Terminal-Bench 4.0 leaderboard.")})

# ================================================================ Zhipu
add(id='glm-5-3', name='GLM-5.3', short='GLM-5.3', vendor='zhipu', status='public', release='2026-08-18', release_star=True,
    release_tip=Z('8 月 14 日宣布（先给 Coding Plan 用户），8 月 18 日上 API；权重约两周后放出（Hugging Face 仓库 8 月 25 日建立）。', 'Announced Aug 14 (Coding Plan users first), on the API from Aug 18; weights about two weeks later (Hugging Face repo created Aug 25).'),
    price={'in': 1.4, 'out': 4.4, 'tip': Z('Z.ai 官方价 $1.40 / $4.40，缓存命中 $0.26。只接受文本输入，只能开思考模式。〔高〕', 'Z.ai list price $1.40 / $4.40, cached input $0.26. Text-only input; reasoning is always on. [high]')},
    license=lic('custom', 'GLM-5.3 License：MIT 式的自定义许可，但 12 个月收入超过 100 亿美元的 MaaS 运营方商用前要通过 Z.ai 的安全审查。〔高〕',
                'GLM-5.3 License: a custom, MIT-style license, but MaaS operators with more than $10B revenue over 12 months must pass a Z.ai security review before commercial use. [high]'),
    params=par('753B / 40B', '总参数 753B（按 safetensors 算）；激活 40B 是 Artificial Analysis 的说法，Z.ai 没写。〔中〕', '753B total (from the safetensors); the 40B active figure is from Artificial Analysis, as Z.ai does not state it. [medium]'),
    row_tip=Z('智谱现在的旗舰。Z.ai 自己没报 Terminal-Bench 4.0，表里那格用的是 Moonshot 的数。Z.ai 自己报的 Agents\' Last Exam 28.5% 是 CLI 子集、没写版本，表里用 Moonshot 给的 v1.1 全集分数。',
              "Zhipu's current flagship. Z.ai did not report Terminal-Bench 4.0 itself, so that cell uses Moonshot's number. Z.ai's own Agents' Last Exam figure, 28.5%, is the CLI subset with no version stated; the table uses Moonshot's full-set v1.1 score."),
    scores={
        'aa': aa('glm-5-3', 'max 档（low 23.11）', 'max setting (low 23.11)'),
        'vals': vals('glm-5-3'),
        'tb4_vals': tb4('glm-5-3'),
        'tb4_vendor': c(41.8, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数（Claude Code）。Z.ai 自己没报；DeepSeek 的表里是 37.9%，AA 测是 41.9%。', "Comparison score in Moonshot's Kimi K3.1 Pro model card (Claude Code). Z.ai did not report it; DeepSeek's table gives 37.9% and AA measured 41.9%.", cf='低'),
        'ale': c(26.2, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数，v1.1 全部题。', "Comparison score in Moonshot's Kimi K3.1 Pro model card, v1.1, all tasks."),
        'auto': c(48.2, 'Z.ai 模型卡，v1.0.6（含 null 类型修复）。DeepSeek 的表里是 48.8%。', "Z.ai's model card, v1.0.6 (with the null-type fix). DeepSeek's table gives 48.8%."),
        'tbsci': c(8.1, 'Moonshot 在 Kimi K3.1 Pro 模型卡里给的对照分数。', "Comparison score in Moonshot's Kimi K3.1 Pro model card.", cf='低'),
        'fc2': caa(21.6),
        'deepswe': c(66.9, 'Z.ai 模型卡，v1.1，mini-SWE-agent。', "Z.ai's model card, v1.1, mini-SWE-agent."),
        'progb': c(19.0, 'Z.ai 模型卡，「几乎做对」口径。', "Z.ai's model card, \"almost solved\" metric.", d='19.0'),
        'swem': c(42.5, 'Z.ai 模型卡，v1.1，Claude Code，max 档。', "Z.ai's model card, v1.1, Claude Code, max setting."),
        'hle': c(62.5, 'Z.ai 模型卡，带工具。', "Z.ai's model card, with tools."),
        'gdpval': c(1769, 'Z.ai 模型卡，v2，AA 测。AA 模型页现在是 1654.8。', "Z.ai's model card, v2, run by AA. The AA model page now shows 1654.8."),
        'cygym': c(84.5, 'Z.ai 模型卡，Claude Code，max 档，不用联网工具，1,507 题跑一次。', "Z.ai's model card, Claude Code, max setting, no web tools, one pass over 1,507 tasks."),
    })
add(id='glm-5-3-flash', name='GLM-5.3-Flash', short='GLM-5.3-Flash', vendor='zhipu', status='public', release='2026-08-26',
    price={'in': 0.15, 'out': 0.5, 'tip': Z('Z.ai 官方价 $0.15 / $0.50，缓存命中 $0.03；高速版 GLM-5.3-FlashX（约 200 token/秒）$0.37 / $1.25。〔高〕', 'Z.ai list price $0.15 / $0.50, cached input $0.03; the faster GLM-5.3-FlashX (about 200 tokens/s) is $0.37 / $1.25. [high]')},
    license=MIT_,
    params=par('320B / 18B', 'Hugging Face 模型卡：总参数 320B，激活 18B。〔高〕', 'Hugging Face model card: 320B total, 18B active. [high]'),
    row_tip=Z('GLM-5.3 的小号，MIT 许可，权重和 API 同时放出。没填进表的：Agents\' Last Exam 26.3%（没写版本）、OSWorld 2.0 59.1%（不是 2.1）。',
              'The small sibling of GLM-5.3, MIT-licensed, with weights and API at launch. Not in the table: Agents\' Last Exam 26.3% (version not stated) and OSWorld 2.0 59.1% (not 2.1).'),
    scores={
        'aa': aa('glm-5-3-flash', 'max 档', 'max setting'),
        'vals': vals('glm-5-3-flash'),
        'tb4_vals': tb4('glm-5-3-flash'),
        'auto': c(48.8, 'Z.ai 发布博文，v1.0.6。', "Z.ai's launch blog, v1.0.6."),
        'chart': c(78, 'Z.ai 发布博文，带工具。', "Z.ai's launch blog, with tools."),
        'fc2': caa(17.6),
        'deepswe': c(63.4, 'Z.ai 发布博文，v1.1，mini-SWE-agent。', "Z.ai's launch blog, v1.1, mini-SWE-agent."),
        'hle': c(55.3, 'Z.ai 发布博文，全集、带工具。', "Z.ai's launch blog, full set, with tools."),
        'gdpval': c(1773, 'Z.ai 发布博文，v2，AA 测。AA 模型页现在是 1648.3。', "Z.ai's launch blog, v2, run by AA. The AA model page now shows 1648.3."),
    })
add(id='glm-5-2', name='GLM-5.2', short='GLM-5.2', vendor='zhipu', status='public', release='2026-06-16',
    tag=TAG_SUPER('已被 GLM-5.3 取代。', 'Superseded by GLM-5.3.'),
    price={'in': 1.4, 'out': 4.4, 'tip': Z('Z.ai 官方价 $1.40 / $4.40，缓存命中 $0.26（与 GLM-5.3 同价）。〔高〕', 'Z.ai list price $1.40 / $4.40, cached input $0.26 (same as GLM-5.3). [high]')},
    license=MIT_,
    params=par('753B / 40B', '总参数 753B（按 safetensors 算；GLM-5 底座是 744B）；激活 40B 是 GLM-5 底座的数字。〔中〕', '753B total (from the safetensors; the GLM-5 base is 744B); 40B active is the GLM-5 base figure. [medium]'),
    row_tip=Z('6 月发布、MIT 许可，已被 GLM-5.3 取代。表里多是 Z.ai 在 GLM-5.3 模型卡里重跑的分数。没填进表的：HLE 带工具 54.7%（是纯文本子集，不是全集）；原博文的 ProgramBench 63.7% 是部分分、SWE-Marathon 13.0% 是 v1.1 之前的题。',
              'Released in June under MIT and superseded by GLM-5.3. Most scores here are Z.ai\'s re-runs in the GLM-5.3 model card. Not in the table: HLE with tools 54.7% (text-only subset, not the full set); the original blog\'s ProgramBench 63.7% is partial credit and its SWE-Marathon 13.0% predates v1.1.'),
    scores={
        'auto': c(26.2, 'Z.ai 在 GLM-5.3 模型卡里重跑的分数，v1.0.6。', "Z.ai's re-run in the GLM-5.3 model card, v1.0.6."),
        'deepswe': c(46.2, 'Z.ai 发布博文；GLM-5.3 模型卡标为 v1.1。', "Z.ai's launch blog; the GLM-5.3 model card labels it v1.1."),
        'progb': c(9.5, 'Z.ai 在 GLM-5.3 模型卡里重跑，「几乎做对」口径。', "Z.ai's re-run in the GLM-5.3 model card, \"almost solved\" metric."),
        'swem': c(19.4, 'Z.ai 在 GLM-5.3 模型卡里重跑，v1.1。', "Z.ai's re-run in the GLM-5.3 model card, v1.1."),
        'gdpval': c(1508, 'Z.ai 在 GLM-5.3 模型卡里给的分数，v2。', "Z.ai's figure in the GLM-5.3 model card, v2."),
        'cygym': c(77.2, 'Z.ai 在 GLM-5.3 模型卡里重跑。', "Z.ai's re-run in the GLM-5.3 model card."),
    },
    blank={'aa': blank('AA 把它标成已停用，没算 v5.0.1 指数。', 'AA marks it deprecated and computes no v5.0.1 index.'),
           'vals': blank('不在 Vals Index v2.2 榜上。', 'Not on the Vals Index v2.2 leaderboard.'),
           'tb4_vals': blank('不在 Vals 的 Terminal-Bench 4.0 榜上。', "Not on Vals' Terminal-Bench 4.0 leaderboard.")})

assert len(M) == 16
for m in M:
    for k in ('release',): assert m[k] == RM[m['id']]['release'], (m['id'], m[k])
    p = RM[m['id']]['price']
    if 'price' in m: assert (m['price']['in'], m['price']['out']) == (p['in'], p['out']), m['id']
    ind = RM[m['id']]['independent']
    for k in ('aa', 'vals', 'tb4_vals'):
        rv = (ind.get(k) or {}).get('v')
        if k in m['scores']: assert m['scores'][k]['v'] == rv, (m['id'], k)
        else: assert rv is None, (m['id'], k, rv)
    for k, s in m['scores'].items():
        assert isinstance(s['v'], (int, float)), (m['id'], k)
D['models'].extend(M)

# ---------------------------------------------------------------- new bench columns (only in Table 3-1 for now)
def B(key, label, name, unit, desc_zh, desc_en, bar='auto'):
    return {'key': key, 'label': Z(label, label), 'name': Z(name, name), 'unit': unit, 'group': 'ext', 'direction': 'higher', 'bar': bar, 'desc': Z(desc_zh, desc_en)}
PCT = Z('%', '%')
D['benches'] += [
    B('deepswe', 'DeepSWE', 'DeepSWE v1.1', PCT, 'DeepSWE v1.1，单位 %。在真实代码仓库里修 bug（Datacurve 出品）。分数来自各厂商自己的发布表，各家用的工具不同。〔中〕',
      'DeepSWE v1.1, in %. Fixing bugs in real code repositories (by Datacurve). Scores come from each vendor\'s launch table, and harnesses differ. [medium]'),
    B('progb', 'ProgB', 'ProgramBench', PCT, 'ProgramBench，单位 %。从零写出完整程序。只收「几乎做对」口径：一题测试通过 ≥95% 才算 1。按测试通过率算的部分分不填。分数来自各厂商发布表。〔中〕',
      'ProgramBench, in %. Writing complete programs from scratch. Only the "almost solved" metric is used: a task counts once at least 95% of its tests pass. Partial-credit scores (share of tests passed) are left out. Scores come from vendors\' launch tables. [medium]'),
    B('swem', 'Marathon', 'SWE-Marathon v1.1', PCT, 'SWE-Marathon v1.1，单位 %。要做好几个小时的长程编码任务（Abundant AI 出品）。v1.1 之前或没写版本的分数不填。分数来自各厂商发布表。〔中〕',
      'SWE-Marathon v1.1, in %. Long coding tasks that take hours (by Abundant AI). Scores from before v1.1, or with no version stated, are left out. Scores come from vendors\' launch tables. [medium]'),
    B('hle', 'HLE', "Humanity's Last Exam（全集，带工具）", PCT, "Humanity's Last Exam（HLE），全集、带工具，单位 %。跨学科的超难问答。不带工具、或只考纯文本子集的分数不填。分数来自各厂商发布表。〔中〕",
      "Humanity's Last Exam (HLE), full set, with tools, in %. Extremely hard questions across disciplines. Scores without tools, or on the text-only subset, are left out. Scores come from vendors' launch tables. [medium]"),
    B('gdpval', 'GDPval', 'GDPval-AA v2', Z(' Elo', ' Elo'), 'GDPval-AA v2，单位 Elo。Artificial Analysis 把模型在 OpenAI GDPval 职业任务上的产出两两比较，Elo 越高越好。分数来自各厂商发布表，多数引用 AA；取数时间不同，Elo 会随榜上模型变化而漂移。〔中〕',
      "GDPval-AA v2, in Elo. Artificial Analysis compares models head-to-head on OpenAI's GDPval professional tasks; higher is better. Scores come from vendors' launch tables, mostly citing AA; they were taken at different times, and Elo drifts as the field changes. [medium]"),
    B('cygym', 'CyberGym', 'CyberGym', PCT, 'CyberGym，单位 %。按漏洞描述复现真实软件里的漏洞（写出能触发它的输入）。多数是关掉防护测的。分数来自各厂商发布表。〔中〕',
      'CyberGym, in %. Reproducing real software vulnerabilities from a description (writing an input that triggers each one). Mostly run with safeguards off. Scores come from vendors\' launch tables. [medium]'),
]

# ---------------------------------------------------------------- Table 3-1 column config
D['t31'] = {
    'toc': Z('表 3-1 大厂与开源模型总表', 'Table 3-1 Big Tech and open-weight models'),
    'c0': {'label': Z('模型', 'Model'), 'tip': Z('厂商色块 + 模型名。悬停模型名看简介和没填进表的分数；小标签：仅订阅、已取代、将下线。',
                                                  'Vendor swatch + model name. Hover a name for a short profile and the scores left out of the table. Small tags: Plan only, Superseded, Retiring.')},
    'groups': [
        {'key': 'basic', 'label': Z('基本 · 2026 年 · $/百万 token', 'Basics · 2026 · $/M tokens'), 'short': Z('基本', 'Basics'),
         'tip': Z('发布日都在 2026 年。价格是 API 标准价，美元 / 每百万 token。开放权重写许可证简称，参数写总参数 / 激活参数。', 'All release dates are in 2026. Prices are standard API list prices, USD per million tokens. Open weights shows the license in short; parameters are total / active.'),
         'cols': ['release', 'price_in', 'price_out', 'license', 'params']},
        {'key': 'indep', 'label': Z('独立榜单', 'Independent leaderboards'), 'short': Z('独立榜单', 'Independent leaderboards'),
         'tip': Z('第三方用同一套方法统一测，可以横向比，也可以和表 2-1 的同名列直接比。', 'Measured by third parties with one method, so they compare across vendors and directly with the same columns in Table 2-1.'),
         'cols': ['aa', 'vals', 'tb4_vals']},
        {'key': 'shared', 'label': Z('厂商自报 · 与前沿同列', 'Vendor-reported · Shared with frontier'), 'short': Z('与前沿同列', 'Shared with frontier'),
         'tip': Z('和表 2-1 用同一个测试、同一版本、同一单位和子集的列。不一致的分数不填，写在模型名的悬停说明里。', 'Columns that match Table 2-1 on test, version, unit and subset. Mismatched scores are left out and listed in the model-name tooltip.'),
         'cols': ['tb4_vendor', 'ale', 'auto', 'chart', 'osw', 'tbsci', 'fc2']},
        {'key': 'ext', 'label': Z('厂商自报 · 本章新增', 'Vendor-reported · New in this chapter'), 'short': Z('本章新增', 'New in this chapter'),
         'tip': Z('大厂和开源厂商常报、前沿三家表里少见的测试。各家条件不同，只能看大致位置。', 'Tests that Big Tech and open-weight labs often report but the frontier tables rarely do. Conditions differ, so read them as rough positions.'),
         'cols': ['deepswe', 'progb', 'swem', 'hle', 'gdpval', 'cygym']},
    ],
    'basic': {
        'release': {'label': Z('发布', 'Release'), 'tip': Z('对外可用的日期，都在 2026 年。先宣布、后开放的标 *，悬停看两个日期。色条越长越新。〔高〕', 'Date of general availability, all in 2026. * marks models announced before they opened; hover for both dates. Longer bar = newer. [high]')},
        'price_in': {'label': Z('输入', 'Input'), 'tip': Z('API 标准价，美元 / 每百万输入 token。开源模型取厂商自家 API 的高峰价。色条按 0 到 {max}（本表公开模型最高价）画，越长越贵。〔高〕', "Standard API price, USD per million input tokens; open-weight models use the vendor's own API at peak rates. Bar runs from 0 to {max} (highest public-model price in this table); longer = pricier. [high]")},
        'price_out': {'label': Z('输出', 'Output'), 'tip': Z('API 标准价，美元 / 每百万输出 token。色条按 0 到 {max}（本表公开模型最高价）画，越长越贵。〔高〕', 'Standard API price, USD per million output tokens. Bar runs from 0 to {max} (highest public-model price in this table); longer = pricier. [high]')},
        'license': {'label': Z('开放权重', 'Weights'), 'tip': Z('权重能不能下载、用什么许可证：MIT、Modified MIT（修改版 MIT）、自定义（厂商自己写的许可证，通常对大客户另有条件）、否（不开放）。悬停看许可证要点。', 'Whether the weights can be downloaded, and under what license: MIT, Modified MIT, Custom (the vendor\'s own license, usually with extra terms for large users) or No (closed). Hover for the key terms.')},
        'params': {'label': Z('参数', 'Params'), 'tip': Z('总参数 / 激活参数（混合专家模型每个 token 只用一部分参数）。T＝万亿，B＝十亿。悬停看出处。', 'Total / active parameters (a mixture-of-experts model uses only part of its parameters per token). T = trillion, B = billion. Hover for the source.')},
    },
    'hints': [
        {'label': Z('怎么读', 'How to read'), 'tip': Z('<b>怎么读这张表</b>{n_models} 个模型：大厂 xAI、Meta，开源 DeepSeek、Moonshot、智谱。组内按发布日从新到旧。<br>分数 {n_bench} 列，分{n_groups_zh}组：{group_names}。<br>每列前三名加深；名次只在本表里排。<br>「—」是没有公开分数，或者分数口径和这一列不一致（悬停模型名看是哪些）。<br>悬停任何数字可看出处、测试条件和可信度。',
                                                     '<b>How to read this table</b>{n_models} models: Big Tech xAI and Meta; open-weight DeepSeek, Moonshot and Zhipu. Within each vendor, newest first.<br>{n_bench} score columns in {n_groups_zh} groups: {group_names}.<br>The top three in each column are shaded darker; ranks are within this table only.<br>"—" means no public score, or a score that does not match this column (hover the model name to see which).<br>Hover any number for its source, test conditions and confidence.')},
        {'label': Z('色条', 'Bars'), 'tip': Z('<b>格内色条</b>规则和表 2-1 一样：分数列从本列最低画到最高；有分数的模型少于 5 个时从 0 画起。颜色跟厂商。<br>价格列：灰色，从 0 画到本表公开模型最高价（输入 {price_in_max}，输出 {price_out_max}）。',
                                                '<b>In-cell bars</b>Same rules as Table 2-1: score columns run from the lowest to the highest score in the column; with fewer than 5 scored models, bars start at 0. Bar color follows the vendor.<br>Price columns: gray, from 0 to the highest public-model price in this table (input {price_in_max}, output {price_out_max}).')},
        {'label': Z('AA 角标', 'AA marker'), 'tip': Z('<b>AA 角标</b>FrontierCode 2.0 这一列里带「AA」的，是 Artificial Analysis 自己测的 FrontierCode-AA 2.0（132 题私有集），不是厂商自报；和表 2-1 那列只能看大致位置。',
                                                      "<b>AA marker</b>In the FrontierCode 2.0 column, cells marked \"AA\" are Artificial Analysis's own FrontierCode-AA 2.0 runs (132-task private set), not vendor reports; compare them with Table 2-1 only roughly.")},
        {'label': Z('少了哪列', 'Missing column'), 'tip': Z('<b>为什么没有 OSWorld 2.1 列</b>表 2-1 的 OSWorld 2.1 是离线子集。本章各家报的要么是 108 题全集（Meta），要么没说是不是离线子集（Moonshot），要么是 OSWorld-Verified / 2.0，都不能填。一列都没有分数时整列不出。',
                                                           "<b>Why there is no OSWorld 2.1 column</b>Table 2-1's OSWorld 2.1 is the offline subset. What this chapter's vendors report is either the full 108-task set (Meta), unclear on the subset (Moonshot), or OSWorld-Verified / 2.0, so none can go in. A column with no scores at all is not shown.")},
    ],
}
# ---------------------------------------------------------------- chapter 3 meta
D['meta']['chapters'] = {'ch3': {'snapshot': '2026-11-22', 'groups': ['bigtech', 'open'],
                                 'label': Z('快照 {snapshot} · 大厂 xAI、Meta · 开源 DeepSeek、Moonshot、智谱 · {n} 个模型',
                                            'Snapshot {snapshot} · Big Tech xAI, Meta · Open-weight DeepSeek, Moonshot, Zhipu · {n} models')}}
D['ui']['count_groups'] = Z('前沿 {n_front} 个 + 大厂与开源 {n_other} 个已发布模型', '{n_front} frontier + {n_other} Big Tech and open-weight released models')

# ---------------------------------------------------------------- timeline events (Fig 3-2)
def E(lane, date, zh, en, tz, te, hollow=False, before=False):
    e = {'lane': lane, 'date': date, 'label': Z(zh, en), 'tip': Z(tz, te)}
    if hollow: e['hollow'] = True
    if before: e['before'] = True
    return e
D['timeline_events'] += [
    E('xai', '2026-07-08', 'Grok 4.5', 'Grok 4.5', 'Grok 4.5 上 API（正式博文 7 月 16 日）。$2 / $6。', 'Grok 4.5 on the API (launch post Jul 16). $2 / $6.'),
    E('xai', '2026-08-12', 'Grok 4.6', 'Grok 4.6', 'Grok 4.6。$2 / $6。', 'Grok 4.6. $2 / $6.'),
    E('xai', '2026-09-21', 'Grok 4.7', 'Grok 4.7', 'Grok 4.7，现在的旗舰。$2 / $6。', 'Grok 4.7, the current flagship. $2 / $6.'),
    E('meta', '2026-04-08', 'Muse Spark', 'Muse Spark', 'Muse Spark 首发（早于横轴起点）。之后有 1.1 / 1.2 / 1.3，1.3 在 9 月 2 日。', 'Muse Spark first release (before the start of the axis), followed by 1.1, 1.2 and 1.3 (Sep 2).', before=True),
    E('meta', '2026-08-10', 'Glimmer', 'Glimmer', 'Muse Glimmer：30B 开放权重小模型，Apache 2.0。AA 6.3，没列进表 3-1。', 'Muse Glimmer: a 30B open-weight small model under Apache 2.0. AA 6.3; not in Table 3-1.'),
    E('meta', '2026-09-02', 'Spark 1.3', 'Spark 1.3', 'Muse Spark 1.3。$1.25 / $4.25，AA 36.6。没列进表 3-1（每家最多 4 个）。', 'Muse Spark 1.3. $1.25 / $4.25, AA 36.6. Not in Table 3-1 (four models per vendor at most).'),
    E('meta', '2026-10-12', 'Wonder · Wonder Full', 'Wonder · Wonder Full', 'Muse Wonder（API $4 / $20）和 Muse Wonder Full（只在 Muse Code 订阅里）。', 'Muse Wonder (API, $4 / $20) and Muse Wonder Full (Muse Code subscription only).'),
    E('meta', '2026-10-15', 'Spark Open', 'Spark Open', 'Muse Spark Open：816B 开放权重，Muse Model License。', 'Muse Spark Open: 816B open weights under the Muse Model License.'),
    E('meta', '2026-11-09', 'Ember', 'Ember', 'Muse Ember。$0.10 / $0.50。', 'Muse Ember. $0.10 / $0.50.'),
    E('deepseek', '2026-07-31', 'V4-Flash-0731', 'V4-Flash-0731', 'DeepSeek-V4-Flash-0731，现已下线，没列进表 3-1。', 'DeepSeek-V4-Flash-0731, since retired; not in Table 3-1.'),
    E('deepseek', '2026-08-13', 'V4-Pro-0813', 'V4-Pro-0813', 'DeepSeek-V4-Pro-0813，V4-Pro 正式版，MIT。$1.32 / $3.96。', 'DeepSeek-V4-Pro-0813, the GA release of V4-Pro, MIT. $1.32 / $3.96.'),
    E('deepseek', '2026-09-10', 'V4.1-Flash', 'V4.1-Flash', 'DeepSeek-V4.1-Flash，权重和 API 同日，MIT。$0.30 / $1.20。', 'DeepSeek-V4.1-Flash, weights and API the same day, MIT. $0.30 / $1.20.'),
    E('deepseek', '2026-10-17', 'V4.1-Flash-1017', 'V4.1-Flash-1017', 'DeepSeek-V4.1-Flash-1017，现役，API 名 deepseek-flash。$0.30 / $1.20。', 'DeepSeek-V4.1-Flash-1017, current; API name deepseek-flash. $0.30 / $1.20.'),
    E('moonshot', '2026-06-12', 'K2.7 Code', 'K2.7 Code', 'Kimi K2.7 Code，权重和 API 同日，修改版 MIT。$0.95 / $4.00。', 'Kimi K2.7 Code, weights and API the same day, modified MIT. $0.95 / $4.00.'),
    E('moonshot', '2026-07-16', 'K3', 'K3', 'Kimi K3 上 API 和 App。$3 / $15。', 'Kimi K3 on the API and apps. $3 / $15.'),
    E('moonshot', '2026-07-27', 'K3 权重', 'K3 weights', 'Kimi K3 完整权重放出，Kimi K3 License。', 'Kimi K3 full weights released under the Kimi K3 License.'),
    E('moonshot', '2026-10-24', 'K3.1 Pro', 'K3.1 Pro', 'Kimi K3.1 Pro 上 API 和 App。$2 / $10。', 'Kimi K3.1 Pro on the API and apps. $2 / $10.'),
    E('moonshot', '2026-11-04', 'K3.1 Pro 权重', 'K3.1 Pro weights', '约 11 月 4 日：Kimi K3.1 Pro 权重放出（Hugging Face 仓库 11 月 2 日建立）。', 'Around Nov 4: Kimi K3.1 Pro weights released (Hugging Face repo created Nov 2).'),
    E('zhipu', '2026-06-16', 'GLM-5.2', 'GLM-5.2', 'GLM-5.2，权重和 API 同日，MIT。$1.40 / $4.40。', 'GLM-5.2, weights and API the same day, MIT. $1.40 / $4.40.'),
    E('zhipu', '2026-08-14', 'GLM-5.3 宣布', 'GLM-5.3 announced', 'GLM-5.3 宣布，先给 Coding Plan 用户。', 'GLM-5.3 announced, Coding Plan users first.', hollow=True),
    E('zhipu', '2026-08-18', 'GLM-5.3', 'GLM-5.3', 'GLM-5.3 上 API；权重约两周后放出，改用 GLM-5.3 License。$1.40 / $4.40。', 'GLM-5.3 on the API; weights about two weeks later under the new GLM-5.3 License. $1.40 / $4.40.'),
    E('zhipu', '2026-08-26', 'GLM-5.3-Flash', 'GLM-5.3-Flash', 'GLM-5.3-Flash，权重和 API 同时，MIT。$0.15 / $0.50。', 'GLM-5.3-Flash, weights and API together, MIT. $0.15 / $0.50.'),
]

# ---------------------------------------------------------------- figures: old 3-1/3-2/3-3 -> 4-1/4-2/4-5, plus 4-3 and 4-4
F = D['figures']
f41, f42, f45 = F.pop('f31'), F.pop('f32'), F.pop('f33')
f41['caption'] = Z('图 4-1　AA 指数（独立，全部模型）', 'Fig 4-1 AA Index (independent, all models)')
f41['toc'] = Z('图 4-1 AA 指数排名', 'Fig 4-1 AA Index ranking')
f41['source_tip'] = Z('<b>来源</b>Artificial Analysis 各模型页，v5.0.1。<br>各模型取最高推理强度。<br>前沿快照 {snapshot}，大厂与开源快照 {snapshot3}。〔高〕',
                      '<b>Source</b>Artificial Analysis model pages, v5.0.1.<br>Each model at its highest reasoning effort.<br>Frontier snapshot {snapshot}; Big Tech and open-weight snapshot {snapshot3}. [high]')
f42['caption'] = Z('图 4-2　Vals Index（独立，全部模型）', 'Fig 4-2 Vals Index (independent, all models)')
f42['toc'] = Z('图 4-2 Vals Index 排名', 'Fig 4-2 Vals Index ranking')
f42['source_tip'] = Z('<b>来源</b>Vals AI 榜单，v2.2：前沿取 2026-11-16 版（Neon 是 11-18 追加的），大厂与开源取 11-19 版。<br>横轴从 {min}% 起，所以用点不用条。〔高〕',
                      '<b>Source</b>Vals AI leaderboard, v2.2: frontier models from the 2026-11-16 release (Neon added on 11-18), Big Tech and open-weight from the 11-19 release.<br>The axis starts at {min}%, so dots rather than bars. [high]')
f42['axis'] = {'min': 45, 'max': 75, 'step': 5}
f43 = {'bench': 'tb4_vals', 'caption': Z('图 4-3　Terminal-Bench 4.0（Vals 独立测，全部模型）', 'Fig 4-3 Terminal-Bench 4.0 (independent, Vals; all models)'),
       'source_tip': Z('<b>来源</b>Vals AI 的 Terminal-Bench 4.0 榜，所有模型用同一个工具 mini-SWE-agent 测：前沿取 2026-11-18 版，大厂与开源取 11-19 版。<br>厂商自报的 TB 4.0 各用各的工具，不在这张图里。〔高〕',
                       "<b>Source</b>Vals AI's Terminal-Bench 4.0 leaderboard, every model run with the same mini-SWE-agent harness: frontier models from the 2026-11-18 release, Big Tech and open-weight from 11-19.<br>Vendor-reported TB 4.0 scores use each vendor's own harness and are not in this chart. [high]"),
       'label': Z('Terminal-Bench 4.0', 'Terminal-Bench 4.0'), 'axis': {'min': 0, 'max': 70, 'step': 10},
       'head': [Z('模型', 'Model'), Z('TB 4.0（0–{max}%）', 'TB 4.0 (0–{max}%)'), Z('%', '%'), Z('每题成本', 'Cost per task')],
       'mark': 'bar', 'toc': Z('图 4-3 Terminal-Bench 4.0 排名', 'Fig 4-3 Terminal-Bench 4.0 ranking')}
f44 = {'x': 'price_out', 'y': 'aa', 'toc': Z('图 4-4 价格与 AA 指数', 'Fig 4-4 Price vs. AA Index'),
       'caption': Z('图 4-4　输出价与 AA 指数（横轴对数刻度）', 'Fig 4-4 Output price vs. AA Index (log scale)'),
       'source_tip': Z('<b>来源</b>横轴：API 标准输出价，美元 / 每百万 token（同表 2-1、表 3-1）。纵轴：Artificial Analysis v5.0.1。<br>横轴是对数刻度：每格价格翻倍或更多。<br>实心点＝不开放权重，空心点＝开放权重。〔高〕',
                       '<b>Source</b>X axis: standard API output price, USD per million tokens (as in Tables 2-1 and 3-1). Y axis: Artificial Analysis v5.0.1.<br>The x axis is logarithmic: each step is a doubling or more.<br>Solid dot = closed weights; hollow dot = open weights. [high]'),
       'xaxis': {'ticks': [0.5, 1, 2, 5, 10, 20, 50], 'min': 0.4, 'max': 60},
       'yaxis': {'min': 20, 'max': 70, 'step': 10},
       'xlabel': Z('输出价 $/百万 token（对数）', 'Output $/M tokens (log)'), 'ylabel': Z('AA 指数', 'AA Index'),
       'legend_solid': Z('实心：不开放权重', 'Solid: closed weights'), 'legend_hollow': Z('空心：开放权重', 'Hollow: open weights'),
       'missing': Z('没有 API 价、所以没画：{names}。', 'Not drawn for lack of an API price: {names}.'),
       'tip': Z('{name}：输出 {pout} / 百万 token（输入 {pin}），AA 指数 {aa}。{ow}', '{name}: output {pout} per million tokens (input {pin}), AA Index {aa}. {ow}'),
       'ow_yes': Z('开放权重（{lic}）。', 'Open weights ({lic}).'), 'ow_no': Z('不开放权重。', 'Closed weights.')}
f45['caption'] = Z('图 4-5　厂商自报的六项测试（%，全部模型里口径一致的分数）', 'Fig 4-5 Six vendor-reported tests (%, like-for-like scores from all models)')
f45['toc'] = Z('图 4-5 厂商自报的六项测试', 'Fig 4-5 Six vendor-reported tests')
f45['source_tip'] = Z('<b>来源</b>各厂商的发布表（前沿三家，以及第 3 章大厂与开源厂商里版本、单位、子集一致的分数）。<br>同一模型在不同厂商的表里分数可能不同，悬停看是谁报的。<br>FrontierCode 里第 3 章的分数多是 AA 测的 FrontierCode-AA 2.0。<br>没有分数的模型不画。〔中〕',
                      "<b>Source</b>Vendors' launch tables (the three frontier labs, plus chapter 3 scores that match on version, unit and subset).<br>The same model can score differently in different vendors' tables; hover to see who reported it.<br>Most chapter 3 FrontierCode scores are AA's own FrontierCode-AA 2.0 runs.<br>Models without a score are not drawn. [medium]")
D['figures'] = {'f41': f41, 'f42': f42, 'f43': f43, 'f44': f44, 'f45': f45}

# ---------------------------------------------------------------- appendix sources (research files, de-duplicated, two groups)
S = json.load(open(os.path.join(ROOT, 'i18n', 'static.json'), encoding='utf-8'))
have = set(re.findall(r'href="([^"]+)"', S['blocks']['src']['zh']))
seen = set(); groups = []
for key, R, label in (('bigtech', RB, Z('大厂与开源模型：大厂（xAI、Meta）', 'Big Tech and open-weight models: Big Tech (xAI, Meta)')),
                      ('open', RO, Z('大厂与开源模型：开源（DeepSeek、Moonshot、智谱）', 'Big Tech and open-weight models: open-weight (DeepSeek, Moonshot, Zhipu)'))):
    items = []
    for s in R['sources']:
        u = s['url'].strip()
        if u in seen or u in have: continue
        seen.add(u)
        dte = s.get('date') or ''
        acc = '(accessed)' in dte
        dd = dte.replace('(accessed)', '').strip()
        items.append({'title': s['title'], 'url': u, 'date': dd, 'accessed': acc})
    groups.append({'group': key, 'label': label, 'items': items})
D['sources_ch3'] = {'note': Z('出自 research/2026-11-22-bigtech.json 与 research/2026-11-22-open.json，去重，已在上面列过的链接不重复。', 'From research/2026-11-22-bigtech.json and research/2026-11-22-open.json, de-duplicated; links already listed above are not repeated.'),
                    'accessed': Z('访问于 {date}', 'accessed {date}'), 'groups': groups}

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('models', len(D['models']), 'benches', len(D['benches']), 'events', len(D['timeline_events']), 'sources', [len(g['items']) for g in groups])
