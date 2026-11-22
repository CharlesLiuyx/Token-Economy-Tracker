#!/usr/bin/env python3
"""把 data/models.json + data/vendors.json 写进报告 HTML：
  顶栏与首屏的快照日期 / 模型计数、表 2-1、表 2-2、图 2-1 的模型泳道（Google / Anthropic / 内部代号 / OpenAI / 新厂商）、
  图 3-1 / 3-2 / 3-3、附录「核对方式」、新厂商的配色 CSS。
算力三条泳道、图 2-2 / 2-3、表 2-3 归 compute/build.py 管（标记 <!--compute:…-->），本脚本只认 <!--data:…-->，互不覆盖。

幂等：每块包在 <!--data:NAME:start--> … <!--data:NAME:end--> 里。第一次运行按原文锚点找到原块并包上标记；
之后只替换标记之间的内容。重复跑结果逐字节一致。

另外输出 i18n/static.json 里的固定文字块（<!--data:s-NAME:…-->：顶栏控件与目录头、各章标题、第 1 章结论、
第 4 章、附录手写来源、图 2-1 图注与图例、TERMS 术语表与页面 JS 的界面字），以及 h1、图 2-1 的 <div class="hl">（横轴）。
所有文字都输出中英两份（见 bilingual.py 开头的约定），页面按 :root[data-lang] 显示其一。

用法：python3 build_tables.py [报告路径] [--data 数据目录] [--check]
  报告路径默认＝本脚本旁边的正式报告；--data 默认＝本脚本旁的 data/；--check 只校验不写盘。
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
图 3-1 / 3-2
  · 取对应 bench 有分数的模型，按 v 从高到低；同分按表 2-1 的行序。
  · 3-1：条长＝v / 轴最大值；3-2：点位置＝（v − 轴最小值）/（轴最大 − 轴最小）。数值保留 2 位小数并去掉末尾 0。
    轴：figures.*.axis 的 min / max / step；数据超出时自动按 step 外扩并打印提示。刻度类 dN＝（max − min）/ step。
  · 3-1 第 4 列＝输出价；3-2 第 4 列＝note 里「每题成本 $X」的 $X（Vals 列的 note 必须写这一句）。
图 3-3
  · 每个 panel 一个 bench，规则同 3-1，横轴 0–100；没有分数的模型不画，整个 panel 没有分数时不出。
图例（图 3-x）：只列这张图里出现的厂商，按 vendors.json 顺序。
计数：「N 个已发布模型」＝表 2-1 里 status≠internal 的行数；内部代号模型单独计。
"""
import datetime as dt, html, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bilingual import Bi, L, bi, get, by, join, TX, BLOCK, att, esc, axis, MONTH_EN, report_missing, CJK

REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
args = [a for a in sys.argv[1:]]
CHECK = '--check' in args
if CHECK: args.remove('--check')
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
BEN = D['benches']; BK = {b['key']: b for b in BEN}
MODELS = D['models']
for m in MODELS:
    assert m['vendor'] in VK, ('vendors.json 里没有这个厂商', m['vendor'], m['name'])
    for k in m.get('scores', {}): assert k in BK, ('models.json 里没有这个 bench', k, m['name'])
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
def row_order():
    out = []
    for vk in VORD:
        ms = [m for m in MODELS if m['vendor'] == vk]
        pub = [m for m in ms if m['status'] != 'internal']; inn = [m for m in ms if m['status'] == 'internal']
        pub.sort(key=lambda m: -day(m['release']).toordinal())
        inn.sort(key=lambda m: -day(m['trained']['end']).toordinal())
        if pub or inn: out.append((vk, pub + inn))
    return out
ROWS = row_order()
FLAT = [m for _, ms in ROWS for m in ms]

def dense_rank(vals, lower=False):
    u = sorted(set(vals), reverse=not lower)[:3]
    return {v: i + 1 for i, v in enumerate(u)}

def price_txt(p, nxt):
    def one(x): return ('$%d' % x) if float(x) == int(x) else ('$%.2f' % x)
    return one(p) + ('<small>→%s</small>' % one(nxt) if nxt is not None else '')
def price_plain(p):
    return ('$%d' % p) if float(p) == int(p) else ('$%.2f' % p)

def bench_groups():
    gs = []
    for g in D['t21']['groups']:
        if g['key'] == 'basic': gs.append((g, ['release', 'price_in', 'price_out'])); continue
        ks = [b['key'] for b in BEN if b['group'] == g['key']]
        if ks: gs.append((g, ks))
    return gs
GROUPS = bench_groups()
BENCH_ORDER = [k for g, ks in GROUPS if g['key'] != 'basic' for k in ks]
for b in BEN:
    assert b['key'] in BENCH_ORDER, ('bench 的 group 不在 t21.groups 里', b['key'], b['group'])

def price_max(side):
    v = [m['price'][side] for m in MODELS if m['status'] == 'public' and 'price' in m]
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

# ------------------------------------------------------------------ 图 2-1 模型泳道
def pos(d): return (day(d) - T0).days / SPAN * 100
def f21_hl():
    return '<div class="hl" data-t0="%s" data-span="%d">' % (T0.isoformat(), SPAN)
def f21_lanes():
    lines = ''.join('<i class="ml" style="left:%s%%"></i>' % f3((d - T0).days / SPAN * 100) for d in MONTHS[1:])
    lines += '<i class="vl" style="left:%s%%"></i>' % f3(pos(SNAP))
    out = []
    evs = D['timeline_events']
    for e in evs:
        assert any(l['lane'] == e['lane'] for l in VJ['timeline_lanes']), ('vendors.json 的 timeline_lanes 里没有这条泳道', e['lane'])
    def visible(e):
        if 'end' in e: return pos(e['end']) >= 0 and pos(e['date']) <= 100
        return 0 <= pos(e['date']) <= 100
    for e in evs:
        if not visible(e): warn('图 2-1 节点在横轴（%s 至 %s 月底）之外，不画：%s %s' % (T0.isoformat(), SNAP[:7], e['date'], bi(e['label']).zh))
    for ln in VJ['timeline_lanes']:
        es = [e for e in evs if e['lane'] == ln['lane'] and visible(e)]
        if not es: continue
        es = sorted(es, key=lambda e: day(e['date']))
        vk = ln['vendor']; v = VK[vk]
        sw = ('<span class="sw ho-%s"></span>' if ln.get('hollow_swatch') else '<span class="sw k-%s"></span>') % vk
        out.append('<div class="hl-lab li" data-key="%s"%s>%s%s</div>' % (vk, att('data-tip', ui('lane_tip', name=v['name'])), sw, TX(ln.get('label', v['name']))))
        out.append('<div class="hl-track" data-lane="%s">%s' % (ln['lane'], lines))
        for e in es:
            if 'end' in e:
                a, b = max(0.0, pos(e['date'])), min(100.0, pos(e['end']))   # 区间节点裁到横轴内
                out.append('<span class="pin rng" data-key="%s" style="left:%s%%;width:%s%%"%s><span class="pl noterm">%s</span></span>' % (
                    vk, f3(a), f3(b - a), att('data-tip', e['tip']), TX(e['label'])))
            else:
                d = day(e['date'])
                out.append('<span class="pin%s" data-key="%s" style="left:%s%%"%s><i class="pd"></i><span class="pl noterm"><small>%d/%d</small> %s%s</span></span>' % (
                    ' mu' if e.get('hollow') else '', vk, f3(pos(e['date'])), att('data-tip', L('%s：%s', '%s: %s') % (e['date'], e['tip'])), d.month, d.day, TX(e['label']),
                    ('<span class="tag">%s</span>' % TX(e['tag'])) if e.get('tag') else ''))
        out.append('</div>')
    return ''.join(out)

def f21_axis():
    """图 2-1 底部刻度行：每月 1 日一个刻度（含 t0），快照日一个「M/D 快照」标签。
    放不下时页面 JS（compute 的 fitSnap）改用 data-short / data-short-tip（按当前语言取 -en）。"""
    out = ['<div class="hl-axis">']
    for d in MONTHS:
        out.append('<i class="mt" style="left:%s%%">%s</i>' % (f3((d - T0).days / SPAN * 100), TX(ui('month', m=d.month, mon=MONTH_EN[d.month - 1]))))
    sd = day(SNAP)
    out.append('<i class="mt vm fl" style="left:%s%%"%s%s%s>%s</i></div>' % (
        f3(pos(SNAP)), att('data-tip', ui('snap_tip')), att('data-short', ui('snap_short', m=sd.month, d=sd.day)), att('data-short-tip', ui('snap_short_tip', date=SNAP)),
        TX(ui('snap_label', m=sd.month, d=sd.day))))
    return ''.join(out)

# ------------------------------------------------------------------ 图 3-x
def legend(keys):
    return '<div class="legend">' + ''.join('<span class="li" data-key="%s"%s><i class="sw k-%s"></i>%s</span>' % (
        k, att('data-tip', VK[k]['legend_tip']), k, TX(VK[k]['name'])) for k in VORD if k in keys) + '</div>'
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
    rows = [m for m in FLAT if k in m.get('scores', {})]
    return sorted(rows, key=lambda m: -m['scores'][k]['v'])      # sorted() 稳定：同分保留表 2-1 行序
def price_pair(p):
    # 原文写法：输入「$2 →$4」、输出「$10 → $20」（两边空格不一致，按原样保留）
    pi = price_plain(p['in']) + (' →%s' % price_plain(p['in_next']) if 'in_next' in p else '')
    po = price_plain(p['out']) + (' → %s' % price_plain(p['out_next']) if 'out_next' in p else '')
    return pi, po
def fig_head(fid, F):
    return '<figure id="%s"%s><figcaption>%s<span class="hint"%s>%s<i>?</i></span></figcaption>' % (
        fid, att('data-toc', F['toc']), TX(F['caption']), att('data-tiph', subst(F['source_tip'], {'snapshot': SNAP})), TX(ui('source')))
def f31():
    F = D['figures']['f31']; k = F['bench']; rows = ranked(k)
    a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-1')
    hd = [TX(subst(x, a)) for x in F['head']]
    h = [fig_head('f31', F), legend({m['vendor'] for m in rows}),
         '<div class="row hd c4"><span>%s</span><span>%s</span><span class="v">%s</span><span class="x">%s</span></div>' % tuple(hd)]
    for m in rows:
        c = m['scores'][k]; pi, po = price_pair(m['price']) if 'price' in m else ('—', '—')
        tip = L('%s：%s %s。%s', '%s: %s %s. %s') % (m['name'], F['label'], c['d'], c['note']) + ui('api_price', pin=pi, pout=po)
        h.append('<div class="row c4" data-key="%s"%s><span class="nm noterm">%s</span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], att('data-tip', tip), TX(m['name']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), TX(c['d']), po))
    h.append('<div class="row ax c4">%s</div></figure>' % ticks(a, 2))
    return ''.join(h)
def f32():
    F = D['figures']['f32']; k = F['bench']; rows = ranked(k)
    a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-2')
    hd = [TX(subst(x, a)) for x in F['head']]
    h = [fig_head('f32', F), legend({m['vendor'] for m in rows}),
         '<div class="row hd c4"><span>%s</span><span>%s</span><span class="v">%s</span><span class="x">%s</span></div>' % tuple(hd)]
    for m in rows:
        c = m['scores'][k]; note = bi(c['note'])
        cm = re.search(bi(UI['cost_re']).zh, note.zh); cme = re.search(bi(UI['cost_re']).en, note.en)
        if not cm: warn('图 3-2：%s 的 Vals note 里没有「每题成本 $X」' % bi(m['name']).zh)
        elif not cme or cme.group(1) != cm.group(1): warn('图 3-2：%s 的英文 note 里没有与中文一致的「cost per task $X」' % bi(m['name']).zh)
        tip = L('%s：%s %s%s。%s', '%s: %s %s%s. %s') % (m['name'], F['label'], c['d'], BK[k]['unit'], c['note'])
        h.append('<div class="row c4" data-key="%s"%s><span class="nm noterm">%s</span><span class="track d%d"><span class="mark dot" style="left:%s%%"></span></span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], att('data-tip', tip), TX(m['name']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), TX(c['d']), cm.group(1) if cm else '—'))
    h.append('<div class="row ax c4">%s</div></figure>' % ticks(a, 2))
    return ''.join(h)
def f33():
    F = D['figures']['f33']
    panels = [p for p in F['panels'] if ranked(p['bench'])]
    keys = {m['vendor'] for p in panels for m in ranked(p['bench'])}
    h = [fig_head('f33', F), legend(keys), '<div class="sm">']
    for p in panels:
        k = p['bench']; rows = ranked(k); a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-3 ' + bi(p['title']).zh)
        h.append('<div class="panel"><div class="pt noterm">%s<span class="pn">%s</span></div>' % (TX(p['title'], apos), TX(p['sub'], apos)))
        for m in rows:
            c = m['scores'][k]
            tip = L('%s：%s %s%s。%s', '%s: %s %s%s. %s') % (m['name'], p['title'], c['d'], BK[k]['unit'], c['note'])   # 用面板标题，不用 bench.name
            h.append('<div class="row c3" data-key="%s"%s><span class="nm noterm">%s</span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span></div>' % (
                m['vendor'], att('data-tip', tip), TX(m['short']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), TX(c['d'])))
        h.append('<div class="row ax c3">%s</div></div>' % ticks(a, 1))
    h.append('</div></figure>')
    return ''.join(h)

# ------------------------------------------------------------------ 顶栏 / 首屏 / 附录 / 新厂商 CSS
HOME_URL = 'https://charlesliuyx.github.io/Token-Economy-Tracker/'   # TET 主页；链接由页面 JS 按当前语言补 ?lang=zh|en
def topbar():
    home = '<a id="home" href="%s?lang=zh" data-base="%s"%s>%s</a>' % (HOME_URL, HOME_URL, att('data-tip', ui('home_tip')), TX(ui('home_label')))
    return home + '<span class="tt">%s</span>' % TX(L('%s · %s %s', '%s · %s %s') % (D['meta']['title'], ui('snapshot'), SNAP))
def h1(): return '<h1>%s</h1>' % TX(D['meta']['title'])
def meta_line():
    npub = sum(1 for m in MODELS if m['status'] != 'internal')
    inn = [m for m in MODELS if m['status'] == 'internal']
    ivs = sorted({m['vendor'] for m in inn})
    s = L('%s｜%s %s｜%s', '%s | %s %s | %s') % (D['meta']['meta_prefix'], ui('snapshot'), SNAP, ui('published', n=npub))
    if inn: s = s + (ui('internal_one', n=len(inn), vendor=VK[ivs[0]]['name']) if len(ivs) == 1 else ui('internal_many', n=len(inn)))
    return '<p class="meta">%s</p>' % TX(s)
def appendix(): return hints(D['meta']['appendix_hints'], {'snapshot': SNAP})
def vendor_css():
    used = {m['vendor'] for m in MODELS} | {l['vendor'] for l in VJ['timeline_lanes'] if any(e['lane'] == l['lane'] for e in D['timeline_events'])}
    new = [v for v in VEN if v['key'] in used and not v.get('builtin_css')]
    dn = set()
    for fid in ('f31', 'f32'):
        F = D['figures'][fid]; k = F['bench']; dn.add(axis_of(F, [m['scores'][k]['v'] for m in ranked(k)], {'f31': '图 3-1', 'f32': '图 3-2'}[fid])['n'])
    dn.add(axis_of(D['figures']['f33'], [], 'f33')['n'])
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
src = put(src, 'f31', f31())
src = put(src, 'f32', f32())
src = put(src, 'f33', f33())
src = put(src, 'appendix', appendix())
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
