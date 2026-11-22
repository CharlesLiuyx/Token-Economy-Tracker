#!/usr/bin/env python3
"""把 data/models.json + data/vendors.json 写进报告 HTML：
  顶栏与首屏的快照日期 / 分组模型计数、第 2 章（前沿）的表 2-1、表 2-2、图 2-1 的模型泳道、
  第 3 章（大厂与开源）的章首快照行、表 3-1、图 3-2、第 4 章（全部模型）的图 4-1…4-5、附录「核对方式」与第 3 章来源、
  新厂商的配色 CSS、第 3/4 章的样式块（c34css）与散点标签避让脚本（c34js）。
模型进哪一章由 vendors.json 的 groups[].chapter 决定：2＝前沿（表 2-1、图 2-1），3＝大厂与开源（表 3-1、图 3-2）；第 4 章取全部。
算力三条泳道、图 2-2 / 2-3、表 2-3 归 compute/build.py 管（标记 <!--compute:…-->），本脚本只认 <!--data:…-->，互不覆盖。

幂等：每块包在 <!--data:NAME:start--> … <!--data:NAME:end--> 里。第一次运行按原文锚点找到原块并包上标记；
之后只替换标记之间的内容。重复跑结果逐字节一致。

另外输出 i18n/static.json 里的固定文字块（<!--data:s-NAME:…-->：顶栏控件与目录头、各章标题、第 1 章结论、
第 5 章、附录手写来源、图 2-1 图注与图例、TERMS 术语表与页面 JS 的界面字），以及 h1、图 2-1 的 <div class="hl">（横轴）。
所有文字都输出中英两份（见 bilingual.py 开头的约定），页面按 :root[data-lang] 显示其一。

用法：python3 build_tables.py [报告路径] [--data 数据目录] [--check] [--no-ch1-check]
  报告路径默认＝本脚本旁边的正式报告；--data 默认＝本脚本旁的 data/；--check 只校验不写盘；
  --no-ch1-check 跳过第 1 章新增结论的数字核对（只给 qa/rehearsal.py 这类虚构数据的演练用）。
只用 Python 标准库。

====================================================================== 规则（全部从 2026-11-22 前的手写版反推，并已逐字节回归）
表 2-1
  · 行序：厂商按 vendors.json 的顺序分组（没有模型的厂商不出组标题行）；组内先放已发布与受限模型，按发布日从新到旧，
    同日按 JSON 里的先后；再放内部代号模型，按训练完成日从新到旧。
  · 列序：基本 3 列（发布 / 输入 / 输出）→ benches 按 JSON 顺序；分组表头＝按 group 连续合并，组的第一列加 gs（分组线）。
    组里没有任何列时整组不出。
  · 前三名 r1/r2/r3：每列按 v 去重后从高到低排（「密集名次」：并列同名次，下一名紧接），只给前三个不同的值。
    direction=lower 的列反过来排。名次写进格子 data-tip：「{测试名}：{显示值}{单位}。本列第 N 名。{note}」。
  · 分数色条 --w：bar=auto 时，本列有分数的模型 ≥5 个→ 8 + 92 ×（v − 最低）/（最高 − 最低）；<5 个→ v / 最高 × 100。
    bar=zero 总是从 0 画；bar=minmax 总是最低到最高。保留 1 位小数。
  · 发布列色条：8 + 92 ×（发布日 − 最早发布日）/（最晚 − 最早），按天算，所有有发布日的模型一起比。
  · 价格色条：价格 / 公开模型（status=public）里的最高价 × 100，最短 1.5%，1 位小数；受限模型价格超过这个最高价时不画长度，加 over（斜纹）。
    显示：整数 $3，非整数 $1.50；有 in_next / out_next 时写成 $2<small>→$4</small>。
  · 表头 data-tip：desc + 「 有分数的模型：N 个。」。
  · colgroup：模型列、发布、输入、输出、每个 bench 列的宽度来自 layout.t21（bench 列同宽）；table 的 width＝各列之和，3 位小数。
表 2-2
  · 列＝t22.columns，按 vendor 连续合并成分组表头；每个分组第一列加 gs。行＝sections → rows。
  · 每行单独算：色条 v / 本行最高 × 100（1 位小数）；本行前三名同表 2-1 的密集名次。
  · 格子 data-tip：「{列名} · {测试名}：{显示值}{单位}。本行第 N 名。{note}」；dagger=true 时显示值后加 <sup>†</sup>。
  · 单元格厂商类：vendors.json 的 t22_class（va / vo / vg …）。
图 2-1（模型泳道）
  · 横轴由快照日推导（bilingual.axis）：快照日所在月往前 5 个月的月初 t0 → 快照月最后一天（落在 100%），span＝两者相差的天数。
    compute/build.py 用同一个函数，所以两边永远一致。
  · 泳道顺序＝vendors.json 的 timeline_lanes；没有（落在横轴内的）事件的泳道不出。left＝（日期 − t0）/ span × 100，3 位小数。
    落在横轴外的点节点不画（打印提示）；区间节点（有 end）裁到横轴内，整段在外就不画。
    区间节点：left 取 date，width＝（end − date）/ span × 100。
  · 每条泳道的竖线：每月 1 日（不含 t0）一条 ml；快照日一条 vl。泳道内节点按 date 排序（同日按 JSON 先后）。
  · 节点 data-tip：「YYYY-MM-DD：{tip}」；区间节点直接用 tip。hollow=true → 空心（mu，只是宣布）。
表 3-1（2026-11-22 新增）
  · 行＝第 3 章的模型，分组与组内排序同表 2-1；组标题行在厂商名后加分组名（大厂 / 开源）。
  · 列＝t31.groups[].cols 点名的列：基本列 release / price_in / price_out / license / params，其余是 benches 的 key。
    本章一个分数都没有的 bench 列不出（打印提示），组里没有列时整组不出。列宽：layout.t31（模型列、各基本列；bench 列同宽）。
  · 前三名、色条、表头提示的规则同表 2-1，但名次和色条只在本表的模型里算；价格色条的最高价＝本表公开模型的最高价。
  · 模型名格子挂 row_tip（简介＋没填进表的分数）；license / params 是 {d, tip}，license 为「否」时灰字。
  · 格子显示值可带角标（<sup>AA</sup>），提示文字里去掉角标。
图 3-2（2026-11-22 新增）
  · 与图 2-1 同一套组件（同一个 lanes_html / axis_html）：横轴由第 3 章快照 meta.chapters.ch3.snapshot 推导，泳道＝group 属于第 3 章的厂商，不含算力泳道。
  · 事件 before=true 且早于横轴起点：不画节点，写在泳道名下的小字（← M/D 名称，悬停看全文）。
图 4-1 / 4-2 / 4-3（原图 3-1 / 3-2，加 4-3）
  · 取对应 bench 有分数的全部模型（第 2 章 + 第 3 章），按 v 从高到低；同分按 表 2-1 → 表 3-1 的行序。
  · mark＝bar：条长＝v / 轴最大值；mark＝dot：点位置＝（v − 轴最小值）/（轴最大 − 轴最小）。数值保留 2 位小数并去掉末尾 0。
    轴：figures.*.axis 的 min / max / step；数据超出时自动按 step 外扩并打印提示。刻度类 dN＝（max − min）/ step。
  · xcol＝price：第 4 列＝输出价；xcol＝cost：第 4 列＝note 里「每题成本 $X」的 $X（Vals 两列的 note 必须写这一句，中英一致）。
  · 行名用 fig（可选的短名）否则 name。
图 4-4（散点，2026-11-22 新增）
  · 横轴＝输出价（对数，figures.f44.xaxis 的 min / max / ticks），纵轴＝AA（yaxis，超出自动外扩）。有 AA 但没有 price 的模型不画，列进图注。
  · 实心＝不开放权重，空心（.spt.ow）＝开放权重（license 不是「否」）。价格与 AA 都相同的点左右错开 12px（--dx）。
  · 点按 AA 从高到低排在 DOM 里，页面 JS fitScatter 依次给标签找位置（右、左、上、下、四角…），放不下就隐藏标签（悬停仍有提示）。
图 4-5（原图 3-3）
  · 每个 panel 一个 bench，规则同 4-1，横轴 0–100；没有分数的模型不画，整个 panel 没有分数时不出。行名用 short。
图例（图 4-x）：只列这张图里出现的厂商，按 vendors.json 的 groups 分组（组名在前），组内按 vendors.json 顺序。
计数：首屏「前沿 N 个 + 大厂与开源 M 个已发布模型」＝第 2 章 / 第 3 章里 status≠internal 的模型数；内部代号模型单独计。
第 1 章后 3 条结论：check_ch1() 用数据重算关键数字，与 i18n/static.json 的 blocks.ch1 对不上就构建失败。
"""
import datetime as dt, html, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bilingual import Bi, L, bi, get, by, join, TX, BLOCK, att, esc, axis, MONTH_EN, report_missing, CJK

REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
args = [a for a in sys.argv[1:]]
CHECK = '--check' in args
if CHECK: args.remove('--check')
NO_CH1 = '--no-ch1-check' in args                                  # 只给演练用：数据是虚构的，第 1 章结论核对必然不过
if NO_CH1: args.remove('--no-ch1-check')
DATA = os.path.join(HERE, 'data')
if '--data' in args:
    i = args.index('--data'); DATA = args[i + 1]; del args[i:i + 2]
REPORT = args[0] if args else os.path.join(HERE, REPORT_NAME)
D = json.load(open(os.path.join(DATA, 'models.json'), encoding='utf-8'))
VJ = json.load(open(os.path.join(DATA, 'vendors.json'), encoding='utf-8'))
SJ = json.load(open(os.path.join(HERE, 'i18n', 'static.json'), encoding='utf-8'))
WARN = []
def warn(msg):
    if msg not in WARN: WARN.append(msg)

def A(s): return esc(s)                                            # 属性转义（' → &#x27;）
def apos(s): return s.replace("'", '&#x27;')                       # 显示文字里的 ' 写成 &#x27;（原文如此）
def f1(x): return '%.1f' % x
def f3(x): return '%.3f' % x
def t2(x):                                                        # 2 位小数、去掉末尾 0（92.86 / 83.4 / 40）
    s = '%.2f' % x
    return s.rstrip('0').rstrip('.') if '.' in s else s
def day(s): return dt.date.fromisoformat(s)
def subst(x, mp):
    """x：Bi / 字段 / 字符串；mp 的值可以是 Bi（按语言取）。返回 Bi。"""
    def one(l):
        s = get(x, l)
        for k, v in mp.items(): s = s.replace('{%s}' % k, str(get(v, l)))
        return s
    return by(one)

VEN = VJ['vendors']; VK = {v['key']: v for v in VEN}; VORD = [v['key'] for v in VEN]
VGROUPS = VJ['groups']; GK = {g['key']: g for g in VGROUPS}
for v in VEN: assert v['group'] in GK, ('vendors.json：厂商的 group 不在 groups 里', v['key'], v['group'])
def chapter_of(vk): return GK[VK[vk]['group']]['chapter']
BEN = D['benches']; BK = {b['key']: b for b in BEN}
ALLM = D['models']                                                # 全部模型（第 4 章）
for m in ALLM:
    assert m['vendor'] in VK, ('vendors.json 里没有这个厂商', m['vendor'], m['name'])
    for k in m.get('scores', {}): assert k in BK, ('models.json 里没有这个 bench', k, m['name'])
MODELS = [m for m in ALLM if chapter_of(m['vendor']) == 2]       # 第 2 章（前沿）：表 2-1、图 2-1、首屏计数
M3 = [m for m in ALLM if chapter_of(m['vendor']) == 3]           # 第 3 章（大厂与开源）：表 3-1、图 3-2
CH3 = D['meta']['chapters']['ch3']
SNAP3 = CH3['snapshot']
SNAP = D['meta']['snapshot']
UI = D['ui']
def ui(k, **kw): return subst(UI[k], kw)
T0, SPAN, MONTHS = axis(SNAP)
def ndigit(n):
    def one(l):
        d = get(UI['groups_zh_digits'], l); d = d.split() if ' ' in d else list(d)
        return d[n] if n < len(d) else str(n)
    return by(one)

# ------------------------------------------------------------------ row order (表 2-1)
def row_order(models):
    out = []
    for vk in VORD:
        ms = [m for m in models if m['vendor'] == vk]
        pub = [m for m in ms if m['status'] != 'internal']; inn = [m for m in ms if m['status'] == 'internal']
        pub.sort(key=lambda m: -day(m['release']).toordinal())
        inn.sort(key=lambda m: -day(m['trained']['end']).toordinal())
        if pub or inn: out.append((vk, pub + inn))
    return out
ROWS = row_order(MODELS)
FLAT = [m for _, ms in ROWS for m in ms]
ROWS3 = row_order(M3)
FLAT3 = [m for _, ms in ROWS3 for m in ms]
FLAT_ALL = FLAT + FLAT3                                            # 第 4 章：同分时按 表 2-1 → 表 3-1 的行序

def dense_rank(vals, lower=False):
    u = sorted(set(vals), reverse=not lower)[:3]
    return {v: i + 1 for i, v in enumerate(u)}

def price_txt(p, nxt):
    def one(x): return ('$%d' % x) if float(x) == int(x) else ('$%.2f' % x)
    return one(p) + ('<small>→%s</small>' % one(nxt) if nxt is not None else '')
def price_plain(p):
    return ('$%d' % p) if float(p) == int(p) else ('$%.2f' % p)

def bench_groups():
    """表 2-1 的列：benches 里 group 属于 t21.groups 的（按 JSON 顺序）。其余 bench 只给表 3-1 用（t31.groups[].cols 点名）。"""
    gs = []
    for g in D['t21']['groups']:
        if g['key'] == 'basic': gs.append((g, ['release', 'price_in', 'price_out'])); continue
        ks = [b['key'] for b in BEN if b['group'] == g['key']]
        if ks: gs.append((g, ks))
    return gs
GROUPS = bench_groups()
BENCH_ORDER = [k for g, ks in GROUPS if g['key'] != 'basic' for k in ks]
T31_BASIC = ('release', 'price_in', 'price_out', 'license', 'params')
T31_COLS = [k for g in D['t31']['groups'] for k in g['cols']]
for k in T31_COLS: assert k in T31_BASIC or k in BK, ('t31.groups[].cols 里有不认识的列', k)
for b in BEN:
    assert b['key'] in BENCH_ORDER or b['key'] in T31_COLS, ('bench 既不在 t21.groups 的组里，也不在 t31 的列配置里', b['key'], b['group'])

def price_max(side, models=None):
    v = [m['price'][side] for m in (MODELS if models is None else models) if m['status'] == 'public' and 'price' in m]
    return max(v)


# ------------------------------------------------------------------ text-width estimate (列宽告警用，两种语言都估)
def est_em(text, fs=1.0):
    t = re.sub(r'<[^>]+>', '', html.unescape(text)); w = 0.0
    for ch in t: w += 1.0 if ord(ch) > 0x2e80 else 0.56
    return w * fs + 0.9   # 左右内边距约 0.45em × 2
def est_bi(x, fs=1.0): b = bi(x); return max(est_em(b.zh, fs), est_em(b.en, fs))

# ------------------------------------------------------------------ 表 2-1
def t21():
    L_ = D['layout']['t21']
    pin_max, pout_max = price_max('in'), price_max('out')
    rel = [day(m['release']) for m in MODELS if 'release' in m]
    rmin, rmax = min(rel), max(rel)
    colv = {k: [m['scores'][k]['v'] for m in FLAT if k in m.get('scores', {})] for k in BENCH_ORDER}
    ranks = {k: dense_rank(colv[k], BK[k]['direction'] == 'lower') for k in BENCH_ORDER}
    first = set(ks[0] for g, ks in GROUPS)
    widths = [L_['model'], L_['release'], L_['price_in'], L_['price_out']] + [L_['bench']] * len(BENCH_ORDER)
    ncol = len(widths)
    h = ['<div class="tblwrap wide" id="t21"%s><table style="width:%sem"><colgroup>' % (att('data-toc', D['t21']['toc']), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    c0 = D['t21']['c0']
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0"%s>%s</th>' % (att('data-tip', c0['tip']), TX(c0['label'])))
    for g, ks in GROUPS:
        h.append('<th colspan="%d" class="gh gs"%s>%s</th>' % (len(ks), att('data-tip', g['tip']), TX(g['label'])))
    h.append('</tr><tr class="h2">')
    bs = D['t21']['basic']
    h.append('<th class="num gs"%s>%s</th>' % (att('data-tip', bs['release']['tip']), TX(bs['release']['label'])))
    h.append('<th class="num"%s>%s</th>' % (att('data-tip', subst(bs['price_in']['tip'], {'max': price_plain(pin_max)})), TX(bs['price_in']['label'])))
    h.append('<th class="num"%s>%s</th>' % (att('data-tip', subst(bs['price_out']['tip'], {'max': price_plain(pout_max)})), TX(bs['price_out']['label'])))
    for k in BENCH_ORDER:
        b = BK[k]
        h.append('<th class="num%s"%s>%s</th>' % (' gs' if k in first else '', att('data-tip', bi(b['desc']) + ui('count_suffix', n=len(colv[k]))), TX(b['label'])))
        if est_bi(b['label'], 0.93) > L_['bench']: warn('表 2-1 列「%s」表头可能放不下（估 %.2fem > %.3fem）' % (bi(b['label']).zh, est_bi(b['label'], .93), L_['bench']))
    h.append('</tr></thead><tbody>')
    for vk, ms in ROWS:
        v = VK[vk]
        h.append('<tr class="grp"><td colspan="%d"><span class="gl"><span class="sw k-%s"></span>%s</span></td></tr>' % (ncol, vk, TX(v['name'])))
        for m in ms:
            tag = m.get('tag')
            nm = TX(m['name']) + ('<span class="tag"%s>%s</span>' % (att('data-tip', tag['tip']), TX(tag['text'])) if tag else '')
            if max(est_em(bi(m['name']).get(l)) + (est_em(bi(tag['text']).get(l), 0.78) if tag else 0) for l in ('zh', 'en'))  + 0.4 > L_['model']: warn(   # 小标字号 .78em
                '表 2-1 模型名「%s」可能放不下模型列' % bi(m['name']).zh)
            h.append('<tr class="v-%s"><td class="mn c0 noterm"><span class="sw k-%s"></span>%s</td>' % (vk, vk, nm))
            if 'release' in m:
                d = day(m['release']); w = 8 + 92 * (d - rmin).days / ((rmax - rmin).days or 1)
                tip = att('data-tip', m['release_tip']) if m.get('release_tip') else ''
                h.append('<td class="num cb nb gs"%s style="--w:%s%%">%s%s</td>' % (tip, f1(w), m['release'][5:], '<sup>*</sup>' if m.get('release_star') else ''))
            else:
                tr = m['trained']
                h.append('<td class="num na gs"%s>%s</td>' % (att('data-tip', tr['tip']), TX(tr['label'])))
            p = m.get('price')
            for side, mx in (('in', pin_max), ('out', pout_max)):
                if not p:
                    bl = m.get('blank', {}).get('price_' + side)
                    h.append('<td class="num na"%s>%s</td>' % (att('data-tip', bl['tip']) if bl and bl.get('tip') else '', TX(bl['d']) if bl else '—'))
                    continue
                tip = att('data-tip', p['tip']) if p.get('tip') else ''
                txt = price_txt(p[side], p.get(side + '_next'))
                if p[side] > mx:
                    if m['status'] == 'public': warn('公开模型 %s 的价格超过最高价？' % bi(m['name']).zh)
                    h.append('<td class="num cb nb over"%s>%s</td>' % (tip, txt))
                else:
                    h.append('<td class="num cb nb"%s style="--w:%s%%">%s</td>' % (tip, f1(max(1.5, p[side] / mx * 100)), txt))   # 最短 1.5%，免得 $0.10 看不见
            for k in BENCH_ORDER:
                b = BK[k]; gs = ' gs' if k in first else ''
                c = m.get('scores', {}).get(k)
                if c is None:
                    bl = m.get('blank', {}).get(k)
                    if bl:
                        h.append('<td class="num na%s"%s>%s</td>' % (gs, att('data-tip', bl['tip']) if bl.get('tip') else '', TX(bl['d'])))
                    else:
                        h.append('<td class="num na%s">—</td>' % gs)
                    continue
                vals = colv[k]; lo, hi = min(vals), max(vals)
                mode = b.get('bar', 'auto')
                if mode == 'zero' or (mode == 'auto' and len(vals) < 5): w = c['v'] / hi * 100 if hi else 0
                else: w = 8 + 92 * (c['v'] - lo) / (hi - lo) if hi > lo else 100
                if b['direction'] == 'lower':   # 越低越好：色条反过来
                    w = (lo / c['v'] * 100 if c['v'] else 100) if (mode == 'zero' or (mode == 'auto' and len(vals) < 5)) else (8 + 92 * (hi - c['v']) / (hi - lo) if hi > lo else 100)
                r = ranks[k].get(c['v'])
                tip = L('%s：%s%s。%s%s', '%s: %s%s. %s%s') % (b['name'], c['d'], b['unit'], ui('rank_col', n=r) if r else '', c['note'])
                h.append('<td class="num cb%s%s" style="--w:%s%%"%s>%s</td>' % ((' r%d' % r) if r else '', gs, f1(w), att('data-tip', tip), TX(c['d'])))
            h.append('</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def hints(items, mp):
    out = ['<div class="hints">']
    for it in items:
        if 'text' in it: out.append('<span>%s</span>' % TX(subst(it['text'], mp)))
        else: out.append('<span class="hint"%s>%s<i>?</i></span>' % (att('data-tiph', subst(it['tip'], mp)), TX(it['label'])))
    out.append('</div>')
    return ''.join(out)

def t21_hints():
    names = [bi(g['short']) for g, ks in GROUPS if g['key'] != 'basic']
    return hints(D['t21']['hints'], {'n_bench': len(BENCH_ORDER), 'n_groups_zh': ndigit(len(names)), 'group_names': join(L('、', ', '), names),
                                     'price_in_max': price_plain(price_max('in')), 'price_out_max': price_plain(price_max('out'))})

# ------------------------------------------------------------------ 表 2-2
def t22():
    T = D['t22']; L_ = D['layout']['t22']; cols = T['columns']
    runs = []
    for c in cols:
        if runs and runs[-1][0] == c['vendor']: runs[-1][1].append(c)
        else: runs.append((c['vendor'], [c]))
    first = set(r[1][0]['id'] for r in runs)
    widths = [L_['test']] + [L_['model']] * len(cols)
    h = ['<div class="tblwrap wide" id="t22"%s><table style="width:%sem"><colgroup>' % (att('data-toc', T['toc']), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0"%s>%s</th>' % (att('data-tip', T['c0']['tip']), TX(T['c0']['label'])))
    for vk, cs in runs:
        h.append('<th colspan="%d" class="gh gs"><span class="sw k-%s"></span>%s</th>' % (len(cs), vk, TX(VK[vk]['name'])))
    h.append('</tr><tr class="h2">')
    for c in cols:
        h.append('<th class="num wrapok%s"%s>%s</th>' % (' gs' if c['id'] in first else '', att('data-tip', c['tip']), TX(c['label'])))
    h.append('</tr></thead><tbody>')
    for s in T['sections']:
        h.append('<tr class="grp"><td colspan="%d"><span class="gl">%s</span></td></tr>' % (len(cols) + 1, TX(s['label'])))
        for r in s['rows']:
            h.append('<tr><td class="c0 noterm"%s>%s</td>' % (att('data-tip', r['tip']), TX(r['name'])))
            vals = [c['v'] for c in r['cells'].values() if not c.get('blank')]
            hi = max(vals) if vals else 1; rk = dense_rank(vals)
            for c in cols:
                gs = ' gs' if c['id'] in first else ''
                x = r['cells'].get(c['id'])
                if x is None: h.append('<td class="num na%s">—</td>' % gs); continue
                if x.get('blank'):
                    h.append('<td class="num na%s"%s>%s</td>' % (gs, att('data-tip', x['tip']) if x.get('tip') else '', TX(x['d']))); continue
                n = rk.get(x['v']); lab = bi(c['label']).map(lambda s: re.sub(r'<br>.*', '', s))
                tip = L('%s · %s：%s%s。%s%s', '%s · %s: %s%s. %s%s') % (lab, r['name'], x['d'], r['unit'], ui('rank_row', n=n) if n else '', x['note'])
                h.append('<td class="num cb %s%s%s" style="--w:%s%%"%s>%s%s</td>' % (
                    VK[c['vendor']]['t22_class'], (' r%d' % n) if n else '', gs, f1(x['v'] / hi * 100), att('data-tip', tip), TX(x['d']), '<sup>†</sup>' if x.get('dagger') else ''))
            h.append('</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def t22_hints():
    T = D['t22']; nrows = sum(len(s['rows']) for s in T['sections'])
    first_id = T['columns'][0]['id']
    ncmp = sum(1 for s in T['sections'] for r in s['rows'] for k, c in r['cells'].items() if k != first_id and not c.get('blank'))
    return hints(T['hints'], {'n_rows': nrows, 'n_cmp': len(T['columns']) - 1, 'n_cmp_scores': ncmp})

# ------------------------------------------------------------------ 时间轴泳道（图 2-1 模型泳道 / 图 3-2）
def pos(d): return (day(d) - T0).days / SPAN * 100
def f21_hl():
    return '<div class="hl" data-t0="%s" data-span="%d">' % (T0.isoformat(), SPAN)
def lanes_html(chapter, snap, fig):
    """chapter＝只画 vendors.json 里 group 属于这一章的泳道；snap＝该图的快照日（横轴、快照竖线都由它推导）。"""
    t0, span, months = axis(snap)
    def ps(d): return (day(d) - t0).days / span * 100
    lines = ''.join('<i class="ml" style="left:%s%%"></i>' % f3((d - t0).days / span * 100) for d in months[1:])
    lines += '<i class="vl" style="left:%s%%"></i>' % f3(ps(snap))
    out = []
    evs = D['timeline_events']
    for e in evs:
        assert any(l['lane'] == e['lane'] for l in VJ['timeline_lanes']), ('vendors.json 的 timeline_lanes 里没有这条泳道', e['lane'])
    lanes = [ln for ln in VJ['timeline_lanes'] if chapter_of(ln['vendor']) == chapter]
    lk = {ln['lane'] for ln in lanes}
    def visible(e):
        if 'end' in e: return ps(e['end']) >= 0 and ps(e['date']) <= 100
        return 0 <= ps(e['date']) <= 100
    for e in evs:
        if e['lane'] in lk and not visible(e) and not e.get('before'):
            warn('%s 节点在横轴（%s 至 %s 月底）之外，不画：%s %s' % (fig, t0.isoformat(), snap[:7], e['date'], bi(e['label']).zh))
    for ln in lanes:
        es = [e for e in evs if e['lane'] == ln['lane'] and visible(e)]
        pre = [e for e in evs if e['lane'] == ln['lane'] and e.get('before') and ps(e['date']) < 0]   # 早于横轴起点：写在泳道名下
        if not es and not pre: continue
        es = sorted(es, key=lambda e: day(e['date']))
        vk = ln['vendor']; v = VK[vk]
        sw = ('<span class="sw ho-%s"></span>' if ln.get('hollow_swatch') else '<span class="sw k-%s"></span>') % vk
        small = ''.join('<small class="pre noterm"%s>← %d/%d %s</small>' % (att('data-tip', L('%s：%s', '%s: %s') % (e['date'], e['tip'])), day(e['date']).month, day(e['date']).day, TX(e['label']))
                        for e in sorted(pre, key=lambda e: e['date']))
        out.append('<div class="hl-lab li" data-key="%s"%s>%s%s%s</div>' % (vk, att('data-tip', ui('lane_tip', name=v['name'])), sw, TX(ln.get('label', v['name'])), small))
        out.append('<div class="hl-track" data-lane="%s">%s' % (ln['lane'], lines))
        for e in es:
            if 'end' in e:
                a, b = max(0.0, ps(e['date'])), min(100.0, ps(e['end']))   # 区间节点裁到横轴内
                out.append('<span class="pin rng" data-key="%s" style="left:%s%%;width:%s%%"%s><span class="pl noterm">%s</span></span>' % (
                    vk, f3(a), f3(b - a), att('data-tip', e['tip']), TX(e['label'])))
            else:
                d = day(e['date'])
                out.append('<span class="pin%s" data-key="%s" style="left:%s%%"%s><i class="pd"></i><span class="pl noterm"><small>%d/%d</small> %s%s</span></span>' % (
                    ' mu' if e.get('hollow') else '', vk, f3(ps(e['date'])), att('data-tip', L('%s：%s', '%s: %s') % (e['date'], e['tip'])), d.month, d.day, TX(e['label']),
                    ('<span class="tag">%s</span>' % TX(e['tag'])) if e.get('tag') else ''))
        out.append('</div>')
    return ''.join(out)
def f21_lanes(): return lanes_html(2, SNAP, '图 2-1')

def axis_html(snap, tip='snap_tip', short_tip='snap_short_tip'):
    """时间轴底部刻度行：每月 1 日一个刻度（含 t0），快照日一个「M/D 快照」标签。
    放不下时页面 JS（compute 的 fitSnap）改用 data-short / data-short-tip（按当前语言取 -en）。"""
    t0, span, months = axis(snap)
    def ps(d): return (day(d) - t0).days / span * 100
    out = ['<div class="hl-axis">']
    for d in months:
        out.append('<i class="mt" style="left:%s%%">%s</i>' % (f3((d - t0).days / span * 100), TX(ui('month', m=d.month, mon=MONTH_EN[d.month - 1]))))
    sd = day(snap)
    out.append('<i class="mt vm fl" style="left:%s%%"%s%s%s>%s</i></div>' % (
        f3(ps(snap)), att('data-tip', ui(tip, snap2=SNAP)), att('data-short', ui('snap_short', m=sd.month, d=sd.day)), att('data-short-tip', ui(short_tip, date=snap)),
        TX(ui('snap_label', m=sd.month, d=sd.day))))
    return ''.join(out)
def f21_axis(): return axis_html(SNAP)

# ------------------------------------------------------------------ 第 3 章：表 3-1、图 3-2、章首快照行
def dplain(d):
    """格子显示值去掉角标（<sup>AA</sup> 等），给提示文字用。"""
    return bi(d).map(lambda x: re.sub(r'<sup>.*?</sup>', '', x))
def t31_layout():
    """表 3-1 实际出的列：配置里点名的列，去掉本章一个分数都没有的 bench 列；组里没有列时整组不出。"""
    T = D['t31']; gs = []
    for g in T['groups']:
        ks = []
        for k in g['cols']:
            if k in T31_BASIC: ks.append(k); continue
            if not any(k in m.get('scores', {}) for m in FLAT3):
                warn('表 3-1 列「%s」本章没有任何分数，不出（数据里有了分数会自动出现）' % bi(BK[k]['name']).zh); continue
            ks.append(k)
        if ks: gs.append((g, ks))
    return gs
G31 = t31_layout()
B31 = [k for g, ks in G31 for k in ks if k not in T31_BASIC]
def t31():
    T = D['t31']; L_ = D['layout']['t31']
    pin_max, pout_max = price_max('in', M3), price_max('out', M3)
    rel = [day(m['release']) for m in M3 if 'release' in m]
    rmin, rmax = min(rel), max(rel)
    colv = {k: [m['scores'][k]['v'] for m in FLAT3 if k in m.get('scores', {})] for k in B31}
    ranks = {k: dense_rank(colv[k], BK[k]['direction'] == 'lower') for k in B31}
    first = set(ks[0] for g, ks in G31)
    order = [k for g, ks in G31 for k in ks]
    widths = [L_['model']] + [L_.get(k, L_['bench']) for k in order]
    ncol = len(widths)
    h = ['<div class="tblwrap wide" id="t31"%s><table style="width:%sem"><colgroup>' % (att('data-toc', T['toc']), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0"%s>%s</th>' % (att('data-tip', T['c0']['tip']), TX(T['c0']['label'])))
    for g, ks in G31:
        h.append('<th colspan="%d" class="gh gs"%s>%s</th>' % (len(ks), att('data-tip', g['tip']), TX(g['label'])))
    h.append('</tr><tr class="h2">')
    bs = T['basic']
    for k in order:
        gs = ' gs' if k in first else ''
        if k in T31_BASIC:
            tip = subst(bs[k]['tip'], {'max': price_plain(pin_max if k == 'price_in' else pout_max)})
            h.append('<th class="num%s"%s>%s</th>' % (gs, att('data-tip', tip), TX(bs[k]['label'])))
        else:
            b = BK[k]
            h.append('<th class="num%s"%s>%s</th>' % (gs, att('data-tip', bi(b['desc']) + ui('count_suffix', n=len(colv[k]))), TX(b['label'])))
            if est_bi(b['label'], 0.93) > L_['bench']: warn('表 3-1 列「%s」表头可能放不下（估 %.2fem > %.3fem）' % (bi(b['label']).zh, est_bi(b['label'], .93), L_['bench']))
    h.append('</tr></thead><tbody>')
    for vk, ms in ROWS3:
        v = VK[vk]; g = GK[v['group']]
        h.append('<tr class="grp"><td colspan="%d"><span class="gl"><span class="sw k-%s"></span>%s<small class="gk"%s>%s</small></span></td></tr>' % (
            ncol, vk, TX(v['name']), att('data-tip', g['tip']), TX(g['label'])))
        for m in ms:
            tag = m.get('tag')
            nm = TX(m['name']) + ('<span class="tag"%s>%s</span>' % (att('data-tip', tag['tip']), TX(tag['text'])) if tag else '')
            if max(est_em(bi(m['name']).get(l)) + (est_em(bi(tag['text']).get(l), 0.78) if tag else 0) for l in ('zh', 'en')) + 0.4 > L_['model']:
                warn('表 3-1 模型名「%s」可能放不下模型列' % bi(m['name']).zh)
            h.append('<tr class="v-%s"><td class="mn c0 noterm"%s><span class="sw k-%s"></span>%s</td>' % (vk, att('data-tip', m['row_tip']) if m.get('row_tip') else '', vk, nm))
            for k in order:
                gs = ' gs' if k in first else ''
                if k == 'release':
                    d = day(m['release']); w = 8 + 92 * (d - rmin).days / ((rmax - rmin).days or 1)
                    tip = att('data-tip', m['release_tip']) if m.get('release_tip') else ''
                    h.append('<td class="num cb nb%s"%s style="--w:%s%%">%s%s</td>' % (gs, tip, f1(w), m['release'][5:], '<sup>*</sup>' if m.get('release_star') else ''))
                elif k in ('price_in', 'price_out'):
                    side = k[6:]; mx = pin_max if side == 'in' else pout_max; p = m.get('price')
                    if not p:
                        bl = m.get('blank', {}).get(k)
                        h.append('<td class="num na%s"%s>%s</td>' % (gs, att('data-tip', bl['tip']) if bl and bl.get('tip') else '', TX(bl['d']) if bl else '—'))
                        continue
                    tip = att('data-tip', p['tip']) if p.get('tip') else ''
                    txt = price_txt(p[side], p.get(side + '_next'))
                    if p[side] > mx: h.append('<td class="num cb nb over%s"%s>%s</td>' % (gs, tip, txt))
                    else: h.append('<td class="num cb nb%s"%s style="--w:%s%%">%s</td>' % (gs, tip, f1(max(1.5, p[side] / mx * 100)), txt))
                elif k in ('license', 'params'):
                    x = m.get(k)
                    if not x: h.append('<td class="num na%s">—</td>' % gs); continue
                    na = ' na' if (k == 'license' and m.get('license') and bi(x['d']).en == 'No') or bi(x['d']).zh == '—' else ''
                    h.append('<td class="num%s%s"%s>%s</td>' % (na, gs, att('data-tip', x['tip']), TX(x['d'])))
                    if est_bi(x['d'], 1.0) > L_[k]: warn('表 3-1「%s」的%s「%s」可能放不下' % (bi(m['name']).zh, k, bi(x['d']).en))
                else:
                    b = BK[k]; c = m.get('scores', {}).get(k)
                    if c is None:
                        bl = m.get('blank', {}).get(k)
                        if bl: h.append('<td class="num na%s"%s>%s</td>' % (gs, att('data-tip', bl['tip']) if bl.get('tip') else '', TX(bl['d'])))
                        else: h.append('<td class="num na%s">—</td>' % gs)
                        continue
                    vals = colv[k]; lo, hi = min(vals), max(vals)
                    mode = b.get('bar', 'auto')
                    if mode == 'zero' or (mode == 'auto' and len(vals) < 5): w = c['v'] / hi * 100 if hi else 0
                    else: w = 8 + 92 * (c['v'] - lo) / (hi - lo) if hi > lo else 100
                    if b['direction'] == 'lower':
                        w = (lo / c['v'] * 100 if c['v'] else 100) if (mode == 'zero' or (mode == 'auto' and len(vals) < 5)) else (8 + 92 * (hi - c['v']) / (hi - lo) if hi > lo else 100)
                    r = ranks[k].get(c['v'])
                    tip = L('%s：%s%s。%s%s', '%s: %s%s. %s%s') % (b['name'], dplain(c['d']), b['unit'], ui('rank_col', n=r) if r else '', c['note'])
                    h.append('<td class="num cb%s%s" style="--w:%s%%"%s>%s</td>' % ((' r%d' % r) if r else '', gs, f1(w), att('data-tip', tip), TX(c['d'])))
            h.append('</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)
def t31_hints():
    names = [bi(g['short']) for g, ks in G31 if g['key'] != 'basic']
    return hints(D['t31']['hints'], {'n_models': len(FLAT3), 'n_bench': len(B31), 'n_groups_zh': ndigit(len(names)), 'group_names': join(L('、', ', '), names),
                                     'price_in_max': price_plain(price_max('in', M3)), 'price_out_max': price_plain(price_max('out', M3))})
def ch3_meta():
    return '<p class="meta">%s</p>' % TX(subst(CH3['label'], {'snapshot': SNAP3, 'n': len(FLAT3)}))
def f32():
    F = D['f32']; t0, span, months = axis(SNAP3)
    top = ''.join('<i class="mt" style="left:%s%%">%s</i>' % (f3((d - t0).days / span * 100), TX(ui('month', m=d.month, mon=MONTH_EN[d.month - 1]))) for d in months)
    leg = ('<div class="legend"><span class="li2"><i class="pd lg"></i>%s</span><span class="li2"><i class="pd lg ho"></i>%s</span><span class="li2"><i class="vd"></i>%s</span></div>' % (
        TX(F['l_solid']), TX(F['l_hollow']), TX(F['l_snap'])))
    return ('<figure id="f32" class="bleedw"%s><figcaption>%s%s</figcaption>%s<div class="hl" data-t0="%s" data-span="%d">'
            '<div class="hl-lab ax top"></div><div class="hl-axis top">%s<b class="hl-date" aria-hidden="true"></b></div>%s'
            '<div class="hl-lab ax"></div>%s<i class="hl-cur"><b></b></i></div></figure>') % (
        att('data-toc', F['toc']), TX(F['caption']), ''.join('<span class="hint"%s>%s<i>?</i></span>' % (att('data-tiph', subst(x['tip'], {'snapshot': SNAP3})), TX(x['label'])) for x in F['hints']),
        leg, t0.isoformat(), span, top, lanes_html(3, SNAP3, '图 3-2'), axis_html(SNAP3, 'snap3_tip', 'snap3_short_tip'))

# ------------------------------------------------------------------ 第 4 章：图 4-1…4-5（全部模型）
def legend(keys, extra=''):
    """图例按厂商分组（vendors.json 的 groups 顺序）：组名 + 组内厂商色块。只列这张图里出现的厂商。"""
    parts = []
    for g in VGROUPS:
        ks = [k for k in VORD if k in keys and VK[k]['group'] == g['key']]
        if not ks: continue
        parts.append('<span class="lgg"><span class="lgn"%s>%s</span>%s</span>' % (att('data-tip', g['tip']), TX(g['label']), ''.join(
            '<span class="li" data-key="%s"%s><i class="sw k-%s"></i>%s</span>' % (k, att('data-tip', VK[k]['legend_tip']), k, TX(VK[k]['name'])) for k in ks)))
    return '<div class="legend">' + ''.join(parts) + extra + '</div>'
def axis_of(F, vals, name):
    a = dict(F['axis'])
    if vals and max(vals) > a['max']:
        a['max'] = a['min'] + math.ceil((max(vals) - a['min']) / a['step']) * a['step']; warn('%s 轴最大值自动外扩到 %s' % (name, a['max']))
    if vals and min(vals) < a['min']:
        a['min'] = a['max'] - math.ceil((a['max'] - min(vals)) / a['step']) * a['step']; warn('%s 轴最小值自动外扩到 %s' % (name, a['min']))
    a['n'] = int(round((a['max'] - a['min']) / a['step']))
    return a
def ticks(a, extra_cols):
    n = a['n']; out = []
    for i in range(n + 1):
        cl = 'f' if i == 0 else ('l' if i == n else '')
        v = a['min'] + a['step'] * i
        out.append('<i class="%s" style="left:%s%%">%s</i>' % (cl, t2(i / n * 100), t2(v)))
    return '<span></span><span class="ticks">%s</span>%s' % (''.join(out), '<span></span>' * extra_cols)
def ranked(k):
    rows = [m for m in FLAT_ALL if k in m.get('scores', {})]
    return sorted(rows, key=lambda m: -m['scores'][k]['v'])      # sorted() 稳定：同分保留 表 2-1 → 表 3-1 的行序
def price_pair(p):
    # 原文写法：输入「$2 →$4」、输出「$10 → $20」（两边空格不一致，按原样保留）
    pi = price_plain(p['in']) + (' →%s' % price_plain(p['in_next']) if 'in_next' in p else '')
    po = price_plain(p['out']) + (' → %s' % price_plain(p['out_next']) if 'out_next' in p else '')
    return pi, po
def fig_head(fid, F, a=None):
    mp = {'snapshot': SNAP, 'snapshot3': SNAP3}
    if a: mp.update({'min': t2(a['min']), 'max': t2(a['max'])})
    return '<figure id="%s"%s><figcaption>%s<span class="hint"%s>%s<i>?</i></span></figcaption>' % (
        fid, att('data-toc', F['toc']), TX(F['caption']), att('data-tiph', subst(F['source_tip'], mp)), TX(ui('source')))
def fname(m): return m.get('fig', m['name'])
def cost_of(m, k, fig):
    note = bi(m['scores'][k]['note'])
    cm = re.search(bi(UI['cost_re']).zh, note.zh); cme = re.search(bi(UI['cost_re']).en, note.en)
    if not cm: warn('%s：%s 的 note 里没有「每题成本 $X」' % (fig, bi(m['name']).zh))
    elif not cme or cme.group(1) != cm.group(1): warn('%s：%s 的英文 note 里没有与中文一致的「Cost per task $X」' % (fig, bi(m['name']).zh))
    return cm.group(1) if cm else '—'
def rank_fig(fid):
    """图 4-1 / 4-2 / 4-3：一个 bench 的全部模型排名。mark＝bar（条长＝v / 轴最大）或 dot（点位＝（v − 轴最小）/ 轴宽）；
    xcol＝price（第 4 列输出价）或 cost（第 4 列取 note 里的「每题成本 $X」）。"""
    F = D['figures'][fid]; k = F['bench']; rows = ranked(k); fig = '图 %s-%s' % (fid[1], fid[2])
    a = axis_of(F, [m['scores'][k]['v'] for m in rows], fig)
    hd = [TX(subst(x, {'min': t2(a['min']), 'max': t2(a['max'])})) for x in F['head']]
    h = [fig_head(fid, F, a), legend({m['vendor'] for m in rows}),
         '<div class="row hd c4"><span>%s</span><span>%s</span><span class="v">%s</span><span class="x">%s</span></div>' % tuple(hd)]
    for m in rows:
        c = m['scores'][k]; pct = t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100)
        tip = L('%s：%s %s%s。%s', '%s: %s %s%s. %s') % (m['name'], F['label'], dplain(c['d']), BK[k]['unit'], c['note'])
        if F['xcol'] == 'price':
            pi, po = price_pair(m['price']) if 'price' in m else ('—', '—'); x = po
            tip = tip + ui('api_price', pin=pi, pout=po)
        else: x = cost_of(m, k, fig)
        mark = '<span class="mark dot" style="left:%s%%"></span>' % pct if F['mark'] == 'dot' else '<span class="mark bar" style="width:%s%%"></span>' % pct
        h.append('<div class="row c4" data-key="%s"%s><span class="nm noterm">%s</span><span class="track d%d">%s</span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], att('data-tip', tip), TX(fname(m)), a['n'], mark, TX(c['d']), x))
    h.append('<div class="row ax c4">%s</div></figure>' % ticks(a, 2))
    return ''.join(h)
def f45():
    F = D['figures']['f45']
    panels = [p for p in F['panels'] if ranked(p['bench'])]
    keys = {m['vendor'] for p in panels for m in ranked(p['bench'])}
    h = [fig_head('f45', F), legend(keys), '<div class="sm">']
    for p in panels:
        k = p['bench']; rows = ranked(k); a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 4-5 ' + bi(p['title']).zh)
        h.append('<div class="panel"><div class="pt noterm">%s<span class="pn">%s</span></div>' % (TX(p['title'], apos), TX(p['sub'], apos)))
        for m in rows:
            c = m['scores'][k]
            tip = L('%s：%s %s%s。%s', '%s: %s %s%s. %s') % (m['name'], p['title'], dplain(c['d']), BK[k]['unit'], c['note'])   # 用面板标题，不用 bench.name
            h.append('<div class="row c3" data-key="%s"%s><span class="nm noterm">%s</span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span></div>' % (
                m['vendor'], att('data-tip', tip), TX(m['short']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), TX(c['d'])))
        h.append('<div class="row ax c3">%s</div></div>' % ticks(a, 1))
    h.append('</div></figure>')
    return ''.join(h)
def f44():
    """图 4-4 散点：横轴输出价（对数），纵轴 AA。实心＝不开放权重，空心＝开放权重。没有 API 价的不画、写进图注。
    价格与 AA 都相同的点左右错开几像素（--dx），免得完全重合；标签位置由页面 JS（fitScatter）避让。"""
    F = D['figures']['f44']; k = F['y']
    pts, miss = [], []
    for m in FLAT_ALL:
        if k not in m.get('scores', {}): continue
        (pts if m.get('price') else miss).append(m)
    pts.sort(key=lambda m: -m['scores'][k]['v'])                  # 标签按 AA 从高到低优先占位
    xa = dict(F['xaxis']); ya = axis_of({'axis': F['yaxis']}, [m['scores'][k]['v'] for m in pts], '图 4-4 纵轴')
    outs = [m['price']['out'] for m in pts]
    if max(outs) > xa['max']: warn('图 4-4 横轴：最高输出价 %s 超出 %s，改 figures.f44.xaxis' % (max(outs), xa['max']))
    if min(outs) < xa['min']: warn('图 4-4 横轴：最低输出价 %s 低于 %s，改 figures.f44.xaxis' % (min(outs), xa['min']))
    lg0, lg1 = math.log10(xa['min']), math.log10(xa['max'])
    def px(v): return (math.log10(v) - lg0) / (lg1 - lg0) * 100
    def py(v): return (v - ya['min']) / (ya['max'] - ya['min']) * 100
    same = {}
    for m in pts: same.setdefault((m['price']['out'], m['scores'][k]['v']), []).append(m)
    grid = ''.join('<i class="gy" style="bottom:%s%%"><b>%s</b></i>' % (t2(i / ya['n'] * 100), t2(ya['min'] + ya['step'] * i)) for i in range(ya['n'] + 1))
    grid += ''.join('<i class="gx" style="left:%s%%"><b>%s</b></i>' % (t2(px(t)), price_plain(t)) for t in xa['ticks'])
    dots = []
    for m in pts:
        c = m['scores'][k]; grp = same[(m['price']['out'], c['v'])]; j = grp.index(m)
        dx = '' if len(grp) == 1 else ';--dx:%dpx' % round((j - (len(grp) - 1) / 2) * 12)
        ow = m.get('license') and bi(m['license']['d']).en != 'No'
        pi, po = price_pair(m['price'])
        tip = subst(F['tip'], {'name': m['name'], 'pout': po, 'pin': pi, 'aa': dplain(c['d']),
                               'ow': subst(F['ow_yes'], {'lic': m['license']['d']}) if ow else F['ow_no']})
        dots.append('<span class="spt%s" data-key="%s" style="left:%s%%;bottom:%s%%%s"%s><i class="mark"></i><span class="pl noterm">%s</span></span>' % (
            ' ow' if ow else '', m['vendor'], f3(px(m['price']['out'])), f3(py(c['v'])), dx, att('data-tip', tip), TX(m['short'] if len(bi(fname(m)).en) > 18 else fname(m))))
    extra = ('<span class="li2"><i class="ptl"></i>%s</span><span class="li2"><i class="ptl ow"></i>%s</span>' % (TX(F['legend_solid']), TX(F['legend_hollow'])))
    h = [fig_head('f44', F), legend({m['vendor'] for m in pts}, extra),
         '<div class="sc"><div class="sc-yl">%s</div><div class="sc-plot">%s%s</div><div class="sc-xl">%s</div></div>' % (TX(F['ylabel']), grid, ''.join(dots), TX(F['xlabel']))]
    if miss:
        names = by(lambda l: L('、', ', ').get(l).join(('%s（AA %s）' if l == 'zh' else '%s (AA %s)') % (bi(x['name']).get(l), x['scores'][k]['d']) for x in miss))
        h.append('<p class="note">%s</p>' % TX(subst(F['missing'], {'names': names})))
    h.append('</figure>')
    return ''.join(h)

# ------------------------------------------------------------------ 附录：第 3 章来源（research/ 两份研究文件，去重、分组）
def src3():
    S = D['sources_ch3']; out = ['<p class="note">%s</p>' % TX(S['note'])]
    for g in S['groups']:
        if not g['items']: continue
        out.append('<p class="sg">%s</p><ol class="src">' % TX(g['label']))
        for it in g['items']:
            dte = TX(subst(S['accessed'], {'date': it['date']})) if it.get('accessed') else it['date']
            out.append('<li><a href="%s" target="_blank" rel="noopener">%s</a><span class="sw2">%s</span></li>' % (A(it['url']), TX(it['title'], lambda x: html.escape(x, quote=False)), dte))
        out.append('</ol>')
    return ''.join(out)

# ------------------------------------------------------------------ 顶栏 / 首屏 / 附录 / 新厂商 CSS
HOME_URL = 'https://charlesliuyx.github.io/Token-Economy-Tracker/'   # TET 主页；链接由页面 JS 按当前语言补 ?lang=zh|en
def topbar():
    home = '<a id="home" href="%s?lang=zh" data-base="%s"%s>%s</a>' % (HOME_URL, HOME_URL, att('data-tip', ui('home_tip')), TX(ui('home_label')))
    return home + '<span class="tt">%s</span>' % TX(L('%s · %s %s', '%s · %s %s') % (D['meta']['title'], ui('snapshot'), SNAP))
def h1(): return '<h1>%s</h1>' % TX(D['meta']['title'])
def meta_line():
    npub = sum(1 for m in MODELS if m['status'] != 'internal')
    n3 = sum(1 for m in M3 if m['status'] != 'internal')
    inn = [m for m in ALLM if m['status'] == 'internal']
    ivs = sorted({m['vendor'] for m in inn})
    cnt = ui('count_groups', n_front=npub, n_other=n3) if n3 else ui('published', n=npub)   # 分组计数：前沿 N + 大厂与开源 M（+ 内部代号）
    s = L('%s｜%s %s｜%s', '%s | %s %s | %s') % (D['meta']['meta_prefix'], ui('snapshot'), SNAP, cnt)
    if inn: s = s + (ui('internal_one', n=len(inn), vendor=VK[ivs[0]]['name']) if len(ivs) == 1 else ui('internal_many', n=len(inn)))
    return '<p class="meta">%s</p>' % TX(s)
def appendix(): return hints(D['meta']['appendix_hints'], {'snapshot': SNAP})
def vendor_css():
    used = {m['vendor'] for m in ALLM} | {l['vendor'] for l in VJ['timeline_lanes'] if any(e['lane'] == l['lane'] for e in D['timeline_events'])}
    new = [v for v in VEN if v['key'] in used and not v.get('builtin_css')]
    dn = set()
    for fid in ('f41', 'f42', 'f43'):
        F = D['figures'][fid]; k = F['bench']; dn.add(axis_of(F, [m['scores'][k]['v'] for m in ranked(k)], '图 %s-%s' % (fid[1], fid[2]))['n'])
    dn.add(axis_of(D['figures']['f45'], [], 'f45')['n'])
    dn -= {4, 5, 7}                                    # 原文 CSS 已有 .track.d4 / d5 / d7
    if not new and not dn: return ''
    c = ['<style id="data-css">', '/* build_tables.py 生成：新厂商配色（已过 dataviz 校验，见 vendors.json）与新刻度数 */']
    c.append(':root{%s}' % ''.join('%s:%s;' % (v['css_var'], v['light']) for v in new))
    c.append(':root[data-theme=dark]{%s}' % ''.join('%s:%s;' % (v['css_var'], v['dark']) for v in new))
    for v in new:
        k, cv = v['key'], v['css_var']
        c.append('tr.v-%s{--vc:var(%s)}\n.pin[data-key=%s]{--vc:var(%s)}\ntd.%s{--vc:var(%s)}\n.k-%s{background:var(%s)}\n.sw.ho-%s{background:transparent;box-shadow:inset 0 0 0 1.5px var(%s)}\n[data-key~=%s] .mark{background:var(%s)}' % (
            k, cv, k, cv, v['t22_class'], cv, k, cv, k, cv, k, cv))
        c.append('figure[data-hl=%s] [data-key]:not([data-key~=%s]){opacity:.3}\nfigure[data-hl=%s] [data-key~=%s] .mark{outline:1px solid var(--ink);outline-offset:1px}\nfigure[data-hl=%s] .li[data-key~=%s]{background:var(--hover);color:var(--ink)}' % (k, k, k, k, k, k))
    for n in sorted(dn): c.append('.track.d%d{background-size:calc(100%% / %d) 100%%}' % (n, n))
    c.append('</style>')
    return '\n'.join(c)

# ------------------------------------------------------------------ 第 3、4 章的样式与页面脚本（表 3-1、图 3-2、分组图例、图 4-4 散点）
C34_CSS = """tr.grp .gk{font-weight:400;color:var(--ink3);font-size:.9em;margin-left:8px;cursor:help}
.hl-lab small.pre{font-weight:400;color:var(--ink3);overflow:hidden;text-overflow:ellipsis;max-width:100%;cursor:help}
.legend .lgg{display:inline-flex;align-items:center;flex-wrap:wrap;gap:0 6px}
.legend .lgn{color:var(--ink3);font-size:12px;cursor:help;padding-right:2px}
.legend .ptl{display:inline-block;width:10px;height:10px;margin-right:6px;background:var(--ink3)}
.legend .ptl.ow{background:transparent;box-shadow:inset 0 0 0 2px var(--ink3)}
.sc{display:grid;grid-template-columns:18px minmax(0,1fr);grid-template-rows:auto 32px;margin-top:6px}
.sc-yl{grid-column:1;grid-row:1;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;font-size:12px;color:var(--ink3)}
.sc-plot{grid-column:2;grid-row:1;position:relative;height:440px;margin-left:26px;border-left:1px solid var(--line);border-bottom:1px solid var(--line)}
.sc-xl{grid-column:2;grid-row:2;margin-left:26px;padding-top:15px;text-align:center;font-size:12px;color:var(--ink3);line-height:16px}
.sc .gy{position:absolute;left:0;right:0;height:0;border-top:1px solid var(--grid)}
.sc .gx{position:absolute;top:0;bottom:0;width:0;border-left:1px solid var(--grid)}
.sc .gy b,.sc .gx b{position:absolute;font-weight:400;font-size:12px;line-height:14px;color:var(--ink3);font-variant-numeric:tabular-nums;white-space:nowrap}
.sc .gy b{right:calc(100% + 5px);top:-8px}
.sc .gx b{top:calc(100% + 1px);transform:translateX(-50%)}
.sc .spt{position:absolute;width:0;height:0;z-index:1;transform:translateX(var(--dx,0));cursor:help}
.sc .spt:hover{z-index:3}
.sc .spt .mark{position:absolute;left:-5px;top:-5px;width:10px;height:10px;box-shadow:0 0 0 2px var(--bg)}
.sc .spt.ow .mark{background:var(--bg);box-shadow:inset 0 0 0 2px var(--vc),0 0 0 2px var(--bg)}
.sc .spt .pl{position:absolute;left:0;top:0;padding:0 2px;font-size:12px;line-height:14px;white-space:nowrap;color:var(--ink2)}
.sc .spt .pl.hid{visibility:hidden}
.sc .spt:hover .mark{outline:1px solid var(--ink);outline-offset:1px}
.sc .spt:hover .pl{color:var(--ink);background:var(--bg)}
figure p.note{margin-top:4px}"""
def c34_css():
    ks = ''.join('.sc .spt[data-key=%s]{--vc:var(%s)}' % (v['key'], v['css_var']) for v in VEN)
    return '<style id="c34-css">\n/* build_tables.py 生成：第 3、4 章（表 3-1、图 3-2、图 4-x 分组图例、图 4-4 散点）的样式 */\n%s\n%s\n</style>' % (C34_CSS, ks)
C34_JS = r"""
/* ---- fig 4-4 scatter: place point labels without overlaps (read everything, then write); a label with no free slot is hidden, the tooltip still has it ---- */
function fitScatter(){
  $$('.sc-plot',main).forEach(function(pl){
    if(!pl.getClientRects().length)return;
    var pts=$$('.spt',pl),labs=pts.map(function(p){return $('.pl',p)});
    labs.forEach(function(l){l.classList.remove('hid');l.style.transform=''});
    var pr=pl.getBoundingClientRect(),W=pr.width,H=pr.height;
    var info=pts.map(function(p,i){var r=p.getBoundingClientRect(),lr=labs[i].getBoundingClientRect();return {x:r.left-pr.left,y:r.top-pr.top,w:lr.width,h:lr.height}});
    var dots=info.map(function(o){return [o.x-7,o.y-7,o.x+7,o.y+7]}),placed=[];
    function hit(b,own){
      if(b[0]<1||b[1]<1||b[2]>W-1||b[3]>H-1)return true;
      for(var i=0;i<dots.length;i++){if(i===own)continue;var d=dots[i];if(b[0]<d[2]&&d[0]<b[2]&&b[1]<d[3]&&d[1]<b[3])return true}
      for(var j=0;j<placed.length;j++){var q=placed[j];if(b[0]<q[2]+3&&q[0]<b[2]+3&&b[1]<q[3]+1&&q[1]<b[3]+1)return true}
      return false;
    }
    var res=info.map(function(o,i){
      var w=o.w,h=o.h,C=[[8,-h/2],[-8-w,-h/2],[-w/2,-9-h],[-w/2,9],[7,-h-3],[7,3],[-7-w,-h-3],[-7-w,3],[10,-h-10],[10,10],[-10-w,-h-10],[-10-w,10]];
      for(var c=0;c<C.length;c++){var b=[o.x+C[c][0],o.y+C[c][1],o.x+C[c][0]+w,o.y+C[c][1]+h];if(!hit(b,i)){placed.push(b);return C[c]}}
      return null;
    });
    res.forEach(function(c,i){if(c)labs[i].style.transform='translate('+Math.round(c[0])+'px,'+Math.round(c[1])+'px)';else labs[i].classList.add('hid')});
  });
}
var relayout1=relayout;
relayout=function(){relayout1();fitScatter()};
"""

# ------------------------------------------------------------------ i18n/static.json 的固定文字块
STR = SJ['strings']
LANG_SWITCH = '<span id="lang" role="group" data-i18n-skip%s%s><button data-set="lang:zh" lang="zh-CN">中文</button><button data-set="lang:en" lang="en">EN</button></span>\n  '
def render_tpl(name):
    t = SJ['templates'][name]
    def tx(m):
        k = m.group(1); assert k in STR, ('static.json strings 缺键', k); return TX(STR[k])
    def at(m):
        k = m.group(2); assert k in STR, ('static.json strings 缺键', k); return att(m.group(1), STR[k])
    t = re.sub(r'\{\{t:([a-z0-9_]+)\}\}', tx, t)
    t = re.sub(r'\{\{a:([a-z-]+):([a-z0-9_]+)\}\}', at, t)
    if '{{lang}}' in t: t = t.replace('{{lang}}', LANG_SWITCH % (att('aria-label', STR['lang_aria']), att('data-tip', STR['lang_tip'])))
    assert '{{' not in t, (name, t[t.index('{{'):][:40])
    return t
def render_block(name):
    b = bi(SJ['blocks'][name]); return BLOCK(b.zh, b.en)
def js_str(s): return json.dumps(s, ensure_ascii=False)
def terms_js():
    T = SJ['terms']
    lines = ['var TERMS={']
    items = []
    for k, e in T.items():
        n, d = bi(e['n']), bi(e['d'])
        items.append(' %s:{n:%s,d:%s,ne:%s,de:%s}' % (k, js_str(n.zh), js_str(d.zh), js_str(n.en), js_str(d.en)))
    lines.append(',\n'.join(items)); lines.append('};')
    lines.append('var ALIAS=%s;' % js_str(SJ['alias']['zh']))
    lines.append('var ALIAS_EN=%s;' % js_str(SJ['alias']['en']))
    return '\n'.join(lines)
def ui_js():
    """页面 JS 用的界面字：I18N.zh / I18N.en。标题取 models.json 的 meta.title。"""
    u = {k: bi(v) for k, v in SJ['js_ui'].items()}
    u['title'] = bi(D['meta']['title'])
    return 'var I18N={zh:%s,en:%s};' % (js_str({k: v.zh for k, v in u.items()}), js_str({k: v.en for k, v in u.items()}))
def i18n_css():
    c = bi(STR['collapsed'])
    return ('<style id="i18n-css">\n/* build_tables.py 生成：随语言变化的 CSS 文字 */\n'
            'section.collapsed>h2::after{content:%s}\n:root[data-lang=en] section.collapsed>h2::after{content:%s}\n</style>') % (js_str(c.zh), js_str(c.en))

# ------------------------------------------------------------------ splice（标记必须已存在：第一次包标记的工作已由 qa/oneoff/ 完成）
def region(name, js=False):
    if js: return '/*<!--data:%s:start-->*/' % name, '/*<!--data:%s:end-->*/' % name
    return '<!--data:%s:start-->' % name, '<!--data:%s:end-->' % name
def put(src, name, content, js=False, first=None):
    st, en = region(name, js); block = st + content + en
    if st not in src:
        assert first, ('报告里找不到标记 %s：先确认报告是带标记的正式版本' % st)
        return first(src, block)
    assert src.count(st) == 1 and src.count(en) == 1, name
    a = src.index(st); b = src.index(en, a) + len(en)
    return src[:a] + block + src[b:]
def after(anchor):
    def f(src, block):
        assert src.count(anchor) == 1, anchor; a = src.index(anchor) + len(anchor); return src[:a] + block + src[a:]
    return f

# ------------------------------------------------------------------ 第 1 章后 3 条结论的数字核对（数据变了而结论没改时构建失败，提示人工改 blocks.ch1）
def check_ch1():
    z, e = SJ['blocks']['ch1']['zh'], SJ['blocks']['ch1']['en']
    def aa(m): return m['scores']['aa']['v']
    has = lambda ms: [m for m in ms if 'aa' in m.get('scores', {})]
    top2 = max(has(MODELS), key=aa); top3 = max(has(M3), key=aa)
    api3 = max([m for m in has(M3) if m.get('price')], key=aa)
    ow = sorted([m for m in has(M3) if m.get('license') and bi(m['license']['d']).en != 'No'], key=lambda m: -aa(m))
    mit = max([m for m in ow if bi(m['license']['d']).en == 'MIT'], key=aa)
    tier = [m for m in has(ALLM) if m.get('price') and (m['price']['in'], m['price']['out']) == (0.1, 0.5)]     # 最便宜一档 $0.10 / $0.50
    cheap = sorted([m for m in tier if aa(m) == max(aa(x) for x in tier)], key=lambda m: m['name'])
    need = [
        ('%s，AA %d' % (top3['name'], aa(top3)), '%s, AA %d' % (top3['name'], aa(top3))),
        ('%s（%d）低 %d' % (top2['name'].replace('Claude ', ''), aa(top2), aa(top2) - aa(top3)), '%d points behind the frontier leader, %s (%d)' % (aa(top2) - aa(top3), top2['name'].replace('Claude ', ''), aa(top2))),
        ('%s（%d），低 %d' % (api3['name'], aa(api3), aa(top2) - aa(api3)), '%s (%d), %d behind' % (api3['name'], aa(api3), aa(top2) - aa(api3))),
        ('AA 都是 %d' % aa(cheap[0]), 'Both score %d on AA' % aa(cheap[0])),
        ('%s，AA %d' % (ow[0]['name'], aa(ow[0])), '%s, AA %d' % (ow[0]['name'], aa(ow[0]))),
        ('%s（%d）高 %d' % (ow[1]['name'], aa(ow[1]), aa(ow[0]) - aa(ow[1])), '%d ahead of the runner-up, %s (%d)' % (aa(ow[0]) - aa(ow[1]), ow[1]['name'], aa(ow[1]))),
        ('MIT 许可里最强的是 %s' % mit['short'], 'strongest MIT-licensed model is %s' % mit['short']),
    ]
    assert len(cheap) == 2 and all(aa(m) == aa(cheap[0]) for m in cheap), ('第 1 章第 10 条：最便宜一档的模型或 AA 变了', [(m['name'], aa(m)) for m in cheap])
    for m in cheap:
        v = m['scores']['vals']; c = re.search(bi(UI['cost_re']).zh, bi(v['note']).zh).group(1)
        need.append(('%s%%' % v['d'], '%s%%' % v['d']))
        need.append(('$%.2f' % float(c[1:]), '$%.2f' % float(c[1:])))
    for a, b in need:
        assert a in z and b in e, ('第 1 章新增结论与数据不一致，请改 i18n/static.json 的 blocks.ch1（中英两份）：缺「%s」/「%s」' % (a, b))
if NO_CH1: print('提示：跳过第 1 章结论核对（--no-ch1-check，只用于演练）')
else: check_ch1()

src = open(REPORT, encoding='utf-8').read()
before = src
src = put(src, 'vcss', vendor_css())
src = put(src, 's-css', i18n_css(), first=after('<!--data:vcss:end-->'))
src = put(src, 'topbar', topbar())
src = put(src, 'h1', h1())
src = put(src, 'meta', meta_line())
src = put(src, 't21hints', t21_hints())
src = put(src, 't21', t21())
src = put(src, 'f21hl', f21_hl())
src = put(src, 'f21lanes', f21_lanes())
src = put(src, 'f21axis', f21_axis())
src = put(src, 't22hints', t22_hints())
src = put(src, 't22', t22())
src = put(src, 'c34css', c34_css())
src = put(src, 'ch3meta', ch3_meta())
src = put(src, 't31hints', t31_hints())
src = put(src, 't31', t31())
src = put(src, 'f32', f32())
for fid in ('f41', 'f42', 'f43'): src = put(src, fid, rank_fig(fid))
src = put(src, 'f44', f44())
src = put(src, 'f45', f45())
src = put(src, 'appendix', appendix())
src = put(src, 'src3', src3())
src = put(src, 'c34js', C34_JS, js=True)
for name in SJ['templates']: src = put(src, 's-' + name, render_tpl(name))
for name in SJ['blocks']: src = put(src, 's-' + name, render_block(name))
src = put(src, 's-terms', terms_js(), js=True)
src = put(src, 's-ui', ui_js(), js=True, first=after('/*<!--data:s-terms:end-->*/'))

# 与 compute/build.py 的横轴核对（两边都用 bilingual.axis，正常不会不一致）
m = re.search(r'<div class="hl-track cmp"[^>]*>.*?<i class="vl" style="left:([0-9.]+)%"', src)
if m and abs(float(m.group(1)) - pos(SNAP)) > 0.01:
    warn('图 2-1 算力泳道的快照竖线在 %s%%，与 models.json 的快照日 %s（%s%%）不一致：接着跑 compute/build.py 即可（改了快照日后先跑 build_tables.py 时出现这条是正常的）' % (m.group(1), SNAP, f3(pos(SNAP))))
for w in WARN: print('提示：' + w)
report_missing()
if CHECK:
    print('check only:', 'would change' if src != before else 'no change'); sys.exit(0)
if src != before: open(REPORT, 'w', encoding='utf-8').write(src)
print('wrote' if src != before else 'unchanged', REPORT, len(before), '->', len(src), 'chars')
