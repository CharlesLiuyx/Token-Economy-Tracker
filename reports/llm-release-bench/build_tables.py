#!/usr/bin/env python3
"""把 data/models.json + data/vendors.json 写进报告 HTML：
  顶栏与首屏的快照日期 / 模型计数、表 2-1、表 2-2、图 2-1 的模型泳道（Google / Anthropic / 内部代号 / OpenAI / 新厂商）、
  图 3-1 / 3-2 / 3-3、附录「核对方式」、新厂商的配色 CSS。
算力三条泳道、图 2-2 / 2-3、表 2-3 归 compute/build.py 管（标记 <!--compute:…-->），本脚本只认 <!--data:…-->，互不覆盖。

幂等：每块包在 <!--data:NAME:start--> … <!--data:NAME:end--> 里。第一次运行按原文锚点找到原块并包上标记；
之后只替换标记之间的内容。重复跑结果逐字节一致。

用法：python3 build_tables.py [报告路径] [--data 数据目录] [--check]
  报告路径默认＝构建目录上一级的正式报告；--data 默认＝本脚本旁的 data/；--check 只校验不写盘。
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
  · 泳道顺序＝vendors.json 的 timeline_lanes；没有事件的泳道不出。left＝（日期 − t0）/ span_days × 100，3 位小数。
    区间节点（有 end）：left 取 date，width＝（end − date）/ span_days × 100。
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
WARN = []
def warn(msg):
    if msg not in WARN: WARN.append(msg)

LANG = 'zh'   # 目前只输出中文；英文版由输出层另做（数据里每个文字字段都已是 {"zh": …, "en": …}）
def t(field, lang=None):
    """取文字：field 是 {"zh": …, "en": …} 就按语言取，是普通字符串（品牌名、数字、日期）就原样返回。"""
    if isinstance(field, dict) and 'zh' in field:
        return field.get(lang or LANG) or field['zh']
    return field
def H(s): return t(s).replace("'", '&#x27;')                    # 显示文字：字段本身是 HTML 片段（可含 <br>、<small>），只把 ' 写成 &#x27;（原文如此）
def A(s): return html.escape(t(s), quote=True)                     # 属性转义（' → &#x27;）
def f1(x): return '%.1f' % x
def f3(x): return '%.3f' % x
def t2(x):                                                        # 2 位小数、去掉末尾 0（92.86 / 83.4 / 40）
    s = '%.2f' % x
    return s.rstrip('0').rstrip('.') if '.' in s else s
def day(s): return dt.date.fromisoformat(s)
def subst(x, mp):
    for k, v in mp.items(): x = x.replace('{%s}' % k, str(v))
    return x

VEN = VJ['vendors']; VK = {v['key']: v for v in VEN}; VORD = [v['key'] for v in VEN]
BEN = D['benches']; BK = {b['key']: b for b in BEN}
MODELS = D['models']
for m in MODELS:
    assert m['vendor'] in VK, ('vendors.json 里没有这个厂商', m['vendor'], m['name'])
    for k in m.get('scores', {}): assert k in BK, ('models.json 里没有这个 bench', k, m['name'])
SNAP = D['meta']['snapshot']
UI = D['ui']
def ui(k, **kw): return subst(t(UI[k]), kw)
T0 = day(D['timeline']['t0']); SPAN = D['timeline']['span_days']
def zh(n):
    digits = t(UI['groups_zh_digits']); return digits[n] if n < len(digits) else str(n)

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


# ------------------------------------------------------------------ text-width estimate (列宽告警用)
def est_em(text, fs=1.0):
    t = re.sub(r'<[^>]+>', '', html.unescape(text)); w = 0.0
    for ch in t: w += 1.0 if ord(ch) > 0x2e80 else 0.56
    return w * fs + 0.9   # 左右内边距约 0.45em × 2

# ------------------------------------------------------------------ 表 2-1
def t21():
    L = D['layout']['t21']
    pin_max, pout_max = price_max('in'), price_max('out')
    rel = [day(m['release']) for m in MODELS if 'release' in m]
    rmin, rmax = min(rel), max(rel)
    # column stats
    colv = {k: [m['scores'][k]['v'] for m in FLAT if k in m.get('scores', {})] for k in BENCH_ORDER}
    ranks = {k: dense_rank(colv[k], BK[k]['direction'] == 'lower') for k in BENCH_ORDER}
    first = set(ks[0] for g, ks in GROUPS)
    widths = [L['model'], L['release'], L['price_in'], L['price_out']] + [L['bench']] * len(BENCH_ORDER)
    ncol = len(widths)
    h = ['<div class="tblwrap wide" id="t21" data-toc="%s"><table style="width:%sem"><colgroup>' % (A(t(D['t21']['toc'])), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    c0 = D['t21']['c0']
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0" data-tip="%s">%s</th>' % (A(t(c0['tip'])), t(c0['label'])))
    for g, ks in GROUPS:
        h.append('<th colspan="%d" class="gh gs" data-tip="%s">%s</th>' % (len(ks), A(t(g['tip'])), t(g['label'])))
    h.append('</tr><tr class="h2">')
    bs = D['t21']['basic']
    h.append('<th class="num gs" data-tip="%s">%s</th>' % (A(t(bs['release']['tip'])), t(bs['release']['label'])))
    h.append('<th class="num" data-tip="%s">%s</th>' % (A(subst(t(bs['price_in']['tip']), {'max': price_plain(pin_max)})), t(bs['price_in']['label'])))
    h.append('<th class="num" data-tip="%s">%s</th>' % (A(subst(t(bs['price_out']['tip']), {'max': price_plain(pout_max)})), t(bs['price_out']['label'])))
    for k in BENCH_ORDER:
        b = BK[k]
        h.append('<th class="num%s" data-tip="%s">%s</th>' % (' gs' if k in first else '', A(t(b['desc']) + ui('count_suffix', n=len(colv[k]))), t(b['label'])))
        if est_em(t(b['label']), 0.93) > L['bench']: warn('表 2-1 列「%s」表头可能放不下（估 %.2fem > %.3fem）' % (t(b['label']), est_em(t(b['label']), .93), L['bench']))
    h.append('</tr></thead><tbody>')
    for vk, ms in ROWS:
        v = VK[vk]
        h.append('<tr class="grp"><td colspan="%d"><span class="gl"><span class="sw k-%s"></span>%s</span></td></tr>' % (ncol, vk, t(v['name'])))
        for m in ms:
            tag = m.get('tag')
            nm = t(m['name']) + ('<span class="tag" data-tip="%s">%s</span>' % (A(t(tag['tip'])), t(tag['text'])) if tag else '')
            if est_em(t(m['name']) + (t(tag['text']) if tag else '')) + 1.0 > L['model']: warn('表 2-1 模型名「%s」可能放不下模型列' % t(m['name']))
            h.append('<tr class="v-%s"><td class="mn c0 noterm"><span class="sw k-%s"></span>%s</td>' % (vk, vk, nm))
            # release
            if 'release' in m:
                d = day(m['release']); w = 8 + 92 * (d - rmin).days / ((rmax - rmin).days or 1)
                tip = (' data-tip="%s"' % A(m['release_tip'])) if m.get('release_tip') else ''
                h.append('<td class="num cb nb gs"%s style="--w:%s%%">%s%s</td>' % (tip, f1(w), m['release'][5:], '<sup>*</sup>' if m.get('release_star') else ''))
            else:
                tr = m['trained']
                h.append('<td class="num na gs" data-tip="%s">%s</td>' % (A(t(tr['tip'])), t(tr['label'])))
            # prices
            p = m.get('price')
            for side, mx in (('in', pin_max), ('out', pout_max)):
                if not p:
                    bl = m.get('blank', {}).get('price_' + side)
                    h.append('<td class="num na"%s>%s</td>' % ((' data-tip="%s"' % A(t(bl['tip']))) if bl and bl.get('tip') else '', t(bl['d']) if bl else '—'))
                    continue
                tip = (' data-tip="%s"' % A(t(p['tip']))) if p.get('tip') else ''
                txt = price_txt(p[side], p.get(side + '_next'))
                if p[side] > mx:
                    if m['status'] == 'public': warn('公开模型 %s 的价格超过最高价？' % t(m['name']))
                    h.append('<td class="num cb nb over"%s>%s</td>' % (tip, txt))
                else:
                    h.append('<td class="num cb nb"%s style="--w:%s%%">%s</td>' % (tip, f1(max(1.5, p[side] / mx * 100)), txt))   # 最短 1.5%，免得 $0.10 看不见
            # scores
            for k in BENCH_ORDER:
                b = BK[k]; gs = ' gs' if k in first else ''
                c = m.get('scores', {}).get(k)
                if c is None:
                    bl = m.get('blank', {}).get(k)
                    if bl:
                        h.append('<td class="num na%s"%s>%s</td>' % (gs, (' data-tip="%s"' % A(t(bl['tip']))) if bl.get('tip') else '', t(bl['d'])))
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
                tip = '%s：%s%s。%s%s' % (t(b['name']), t(c['d']), t(b['unit']), ui('rank_col', n=r) if r else '', t(c['note']))
                h.append('<td class="num cb%s%s" style="--w:%s%%" data-tip="%s">%s</td>' % ((' r%d' % r) if r else '', gs, f1(w), A(tip), t(c['d'])))
            h.append('</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def hints(items, mp):
    out = ['<div class="hints">']
    for it in items:
        if 'text' in it: out.append('<span>%s</span>' % subst(t(it['text']), mp))
        else: out.append('<span class="hint" data-tiph="%s">%s<i>?</i></span>' % (A(subst(t(it['tip']), mp)), t(it['label'])))
    out.append('</div>')
    return ''.join(out)

def t21_hints():
    names = [t(g['short']) for g, ks in GROUPS if g['key'] != 'basic']
    return hints(D['t21']['hints'], {'n_bench': len(BENCH_ORDER), 'n_groups_zh': zh(len(names)), 'group_names': '、'.join(names),
                                     'price_in_max': price_plain(price_max('in')), 'price_out_max': price_plain(price_max('out'))})

# ------------------------------------------------------------------ 表 2-2
def t22():
    T = D['t22']; L = D['layout']['t22']; cols = T['columns']
    runs = []
    for c in cols:
        if runs and runs[-1][0] == c['vendor']: runs[-1][1].append(c)
        else: runs.append((c['vendor'], [c]))
    first = set(r[1][0]['id'] for r in runs)
    widths = [L['test']] + [L['model']] * len(cols)
    h = ['<div class="tblwrap wide" id="t22" data-toc="%s"><table style="width:%sem"><colgroup>' % (A(t(T['toc'])), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0" data-tip="%s">%s</th>' % (A(t(T['c0']['tip'])), t(T['c0']['label'])))
    for vk, cs in runs:
        h.append('<th colspan="%d" class="gh gs"><span class="sw k-%s"></span>%s</th>' % (len(cs), vk, t(VK[vk]['name'])))
    h.append('</tr><tr class="h2">')
    for c in cols:
        h.append('<th class="num wrapok%s" data-tip="%s">%s</th>' % (' gs' if c['id'] in first else '', A(t(c['tip'])), t(c['label'])))
    h.append('</tr></thead><tbody>')
    for s in T['sections']:
        h.append('<tr class="grp"><td colspan="%d"><span class="gl">%s</span></td></tr>' % (len(cols) + 1, t(s['label'])))
        for r in s['rows']:
            h.append('<tr><td class="c0 noterm" data-tip="%s">%s</td>' % (A(t(r['tip'])), t(r['name'])))
            vals = [c['v'] for c in r['cells'].values() if not c.get('blank')]
            hi = max(vals) if vals else 1; rk = dense_rank(vals)
            for c in cols:
                gs = ' gs' if c['id'] in first else ''
                x = r['cells'].get(c['id'])
                if x is None: h.append('<td class="num na%s">—</td>' % gs); continue
                if x.get('blank'):
                    h.append('<td class="num na%s"%s>%s</td>' % (gs, (' data-tip="%s"' % A(t(x['tip']))) if x.get('tip') else '', t(x['d']))); continue
                n = rk.get(x['v']); lab = re.sub(r'<br>.*', '', t(c['label']))
                tip = '%s · %s：%s%s。%s%s' % (lab, t(r['name']), t(x['d']), t(r['unit']), ui('rank_row', n=n) if n else '', t(x['note']))
                h.append('<td class="num cb %s%s%s" style="--w:%s%%" data-tip="%s">%s%s</td>' % (
                    VK[c['vendor']]['t22_class'], (' r%d' % n) if n else '', gs, f1(x['v'] / hi * 100), A(tip), t(x['d']), '<sup>†</sup>' if x.get('dagger') else ''))
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
def f21_lanes():
    months = []
    y, mo = T0.year, T0.month
    while True:
        mo += 1
        if mo > 12: y, mo = y + 1, 1
        d = dt.date(y, mo, 1)
        if (d - T0).days >= SPAN: break
        months.append(d)
    lines = ''.join('<i class="ml" style="left:%s%%"></i>' % f3((d - T0).days / SPAN * 100) for d in months)
    lines += '<i class="vl" style="left:%s%%"></i>' % f3(pos(SNAP))
    out = []
    evs = D['timeline_events']
    for ln in VJ['timeline_lanes']:
        es = [e for e in evs if e['lane'] == ln['lane']]
        if not es: continue
        es = sorted(es, key=lambda e: day(e['date']))
        vk = ln['vendor']; v = VK[vk]
        sw = ('<span class="sw ho-%s"></span>' if ln.get('hollow_swatch') else '<span class="sw k-%s"></span>') % vk
        out.append('<div class="hl-lab li" data-key="%s" data-tip="%s">%s%s</div>' % (vk, A(ui('lane_tip', name=t(v['name']))), sw, t(ln.get('label', v['name']))))
        out.append('<div class="hl-track" data-lane="%s">%s' % (ln['lane'], lines))
        for e in es:
            if not (0 <= pos(e['date']) <= 100): warn('图 2-1 节点超出时间轴：%s %s' % (e['date'], t(e['label'])))
            if 'end' in e:
                out.append('<span class="pin rng" data-key="%s" style="left:%s%%;width:%s%%" data-tip="%s"><span class="pl noterm">%s</span></span>' % (
                    vk, f3(pos(e['date'])), f3((day(e['end']) - day(e['date'])).days / SPAN * 100), A(t(e['tip'])), t(e['label'])))
            else:
                d = day(e['date'])
                out.append('<span class="pin%s" data-key="%s" style="left:%s%%" data-tip="%s"><i class="pd"></i><span class="pl noterm"><small>%d/%d</small> %s%s</span></span>' % (
                    ' mu' if e.get('hollow') else '', vk, f3(pos(e['date'])), A('%s：%s' % (e['date'], t(e['tip']))), d.month, d.day, t(e['label']),
                    ('<span class="tag">%s</span>' % t(e['tag'])) if e.get('tag') else ''))
        out.append('</div>')
    for e in evs:
        assert any(l['lane'] == e['lane'] for l in VJ['timeline_lanes']), ('vendors.json 的 timeline_lanes 里没有这条泳道', e['lane'])
    return ''.join(out)

def f21_axis():
    """图 2-1 底部刻度行：每月 1 日一个刻度（含 t0），快照日一个「M/D 快照」标签（fl 类由页面 JS 再按是否重叠调整）。"""
    out = ['<div class="hl-axis">']
    d = T0
    while (d - T0).days < SPAN:
        out.append('<i class="mt" style="left:%s%%">%s</i>' % (f3((d - T0).days / SPAN * 100), ui('month', m=d.month)))
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    sd = day(SNAP)
    out.append('<i class="mt vm fl" style="left:%s%%" data-tip="%s">%s</i></div>' % (f3(pos(SNAP)), A(ui('snap_tip')), ui('snap_label', m=sd.month, d=sd.day)))
    return ''.join(out)

# ------------------------------------------------------------------ 图 3-x
def legend(keys):
    return '<div class="legend">' + ''.join('<span class="li" data-key="%s" data-tip="%s"><i class="sw k-%s"></i>%s</span>' % (
        k, A(t(VK[k]['legend_tip'])), k, t(VK[k]['name'])) for k in VORD if k in keys) + '</div>'
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
    return '<figure id="%s" data-toc="%s"><figcaption>%s<span class="hint" data-tiph="%s">%s<i>?</i></span></figcaption>' % (
        fid, A(t(F['toc'])), t(F['caption']), A(subst(t(F['source_tip']), {'snapshot': SNAP})), ui('source'))
def f31():
    F = D['figures']['f31']; k = F['bench']; rows = ranked(k)
    a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-1')
    hd = [subst(t(x), a) for x in F['head']]
    h = [fig_head('f31', F), legend({m['vendor'] for m in rows}),
         '<div class="row hd c4"><span>%s</span><span>%s</span><span class="v">%s</span><span class="x">%s</span></div>' % tuple(hd)]
    for m in rows:
        c = m['scores'][k]; pi, po = price_pair(m['price']) if 'price' in m else ('—', '—')
        tip = '%s：%s %s。%s' % (t(m['name']), t(F['label']), t(c['d']), t(c['note'])) + ui('api_price', pin=pi, pout=po)
        h.append('<div class="row c4" data-key="%s" data-tip="%s"><span class="nm noterm">%s</span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], A(tip), t(m['name']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), t(c['d']), po))
    h.append('<div class="row ax c4">%s</div></figure>' % ticks(a, 2))
    return ''.join(h)
def f32():
    F = D['figures']['f32']; k = F['bench']; rows = ranked(k)
    a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-2')
    hd = [subst(t(x), a) for x in F['head']]
    h = [fig_head('f32', F), legend({m['vendor'] for m in rows}),
         '<div class="row hd c4"><span>%s</span><span>%s</span><span class="v">%s</span><span class="x">%s</span></div>' % tuple(hd)]
    for m in rows:
        c = m['scores'][k]
        cm = re.search(t(UI['cost_re']), t(c['note']))
        if not cm: warn('图 3-2：%s 的 Vals note 里没有「每题成本 $X」' % t(m['name']))
        tip = '%s：%s %s%s。%s' % (t(m['name']), t(F['label']), t(c['d']), t(BK[k]['unit']), t(c['note']))
        h.append('<div class="row c4" data-key="%s" data-tip="%s"><span class="nm noterm">%s</span><span class="track d%d"><span class="mark dot" style="left:%s%%"></span></span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], A(tip), t(m['name']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), t(c['d']), cm.group(1) if cm else '—'))
    h.append('<div class="row ax c4">%s</div></figure>' % ticks(a, 2))
    return ''.join(h)
def f33():
    F = D['figures']['f33']
    panels = [p for p in F['panels'] if ranked(p['bench'])]
    keys = {m['vendor'] for p in panels for m in ranked(p['bench'])}
    h = [fig_head('f33', F), legend(keys), '<div class="sm">']
    for p in panels:
        k = p['bench']; rows = ranked(k); a = axis_of(F, [m['scores'][k]['v'] for m in rows], '图 3-3 ' + t(p['title']))
        h.append('<div class="panel"><div class="pt noterm">%s<span class="pn">%s</span></div>' % (H(p['title']), H(p['sub'])))
        for m in rows:
            c = m['scores'][k]
            tip = '%s：%s %s%s。%s' % (t(m['name']), t(p['title']), t(c['d']), t(BK[k]['unit']), t(c['note']))   # 用面板标题，不用 bench.name
            h.append('<div class="row c3" data-key="%s" data-tip="%s"><span class="nm noterm">%s</span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span></div>' % (
                m['vendor'], A(tip), t(m['short']), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), t(c['d'])))
        h.append('<div class="row ax c3">%s</div></div>' % ticks(a, 1))
    h.append('</div></figure>')
    return ''.join(h)

# ------------------------------------------------------------------ 顶栏 / 首屏 / 附录 / 新厂商 CSS
def topbar(): return '<span class="tt">%s · %s %s</span>' % (t(D['meta']['title']), ui('snapshot'), SNAP)
def meta_line():
    npub = sum(1 for m in MODELS if m['status'] != 'internal')
    inn = [m for m in MODELS if m['status'] == 'internal']
    ivs = sorted({m['vendor'] for m in inn})
    s = '<p class="meta">%s｜%s %s｜%s' % (t(D['meta']['meta_prefix']), ui('snapshot'), SNAP, ui('published', n=npub))
    if inn: s += ui('internal_one', n=len(inn), vendor=t(VK[ivs[0]]['name'])) if len(ivs) == 1 else ui('internal_many', n=len(inn))
    return s + '</p>'
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

# ------------------------------------------------------------------ splice
def region(name): return '<!--data:%s:start-->' % name, '<!--data:%s:end-->' % name
def put(src, name, content, first):
    st, en = region(name); block = st + content + en
    if st in src:
        assert src.count(st) == 1 and src.count(en) == 1, name
        a = src.index(st); b = src.index(en, a) + len(en)
        return src[:a] + block + src[b:]
    return first(src, block)
def once(src, anchor, start=0):
    n = src.count(anchor, start); assert n >= 1, ('找不到锚点', anchor[:80]); return src.index(anchor, start)
def wrap(start_anchor, end_anchor, after=None):
    """第一次运行：把从 start_anchor 到其后第一个 end_anchor（含）的原块替换成带标记的新块。"""
    def f(src, block):
        base = once(src, after) if after else 0
        a = once(src, start_anchor, base); b = src.index(end_anchor, a) + len(end_anchor)
        return src[:a] + block + src[b:]
    return f
def between(left, right):
    def f(src, block):
        a = once(src, left) + len(left); b = once(src, right, a); return src[:a] + block + src[b:]
    return f
def after(anchor):
    def f(src, block):
        a = once(src, anchor) + len(anchor); return src[:a] + block + src[a:]
    return f

src = open(REPORT, encoding='utf-8').read()
before = src
src = put(src, 'vcss', vendor_css(), after('<!--compute:css:end-->'))
src = put(src, 'topbar', topbar(), wrap('<span class="tt">', '</span>', after='<div id="topbar">'))
src = put(src, 'meta', meta_line(), wrap('<p class="meta">', '</p>'))
src = put(src, 't21hints', t21_hints(), wrap('<div class="hints"><span class="hint" data-tiph="&lt;b&gt;怎么读这张表', '</div>'))
src = put(src, 't21', t21(), wrap('<div class="tblwrap wide" id="t21"', '</table></div>'))
src = put(src, 'f21lanes', f21_lanes(), between('<!--compute:hltop:end-->', '<!--compute:lanes:start-->'))
src = put(src, 'f21axis', f21_axis(), wrap('<div class="hl-axis">', '</div>', after='<!--compute:lanes:end-->'))
src = put(src, 't22hints', t22_hints(), wrap('<div class="hints"><span>', '</div>', after='<h3 id="h22">'))
src = put(src, 't22', t22(), wrap('<div class="tblwrap wide" id="t22"', '</table></div>'))
src = put(src, 'f31', f31(), wrap('<figure id="f31"', '</figure>'))
src = put(src, 'f32', f32(), wrap('<figure id="f32"', '</figure>'))
src = put(src, 'f33', f33(), wrap('<figure id="f33"', '</figure>'))
src = put(src, 'appendix', appendix(), wrap('<div class="hints">', '</div>', after='<h2 id="h5">'))

# 与 compute/build.py 的快照日核对：算力泳道里的快照竖线（vl）和页面 JS 里的「快照」提示是 compute/build.py 写死的
for m in re.finditer(r'<div class="hl-track cmp"[^>]*>.*?<i class="vl" style="left:([0-9.]+)%"', src):
    if abs(float(m.group(1)) - pos(SNAP)) > 0.01:
        warn('图 2-1 算力泳道的快照竖线在 %s%%（compute/build.py 第 89 行写死），与 models.json 的快照日 %s（%s%%）不一致：去改 compute/build.py 的 93.956%% 和 JS 里的 2026-11-19' % (m.group(1), SNAP, f3(pos(SNAP)))); break
if SNAP not in src[src.find('<!--compute:cjs:start-->'):src.find('<!--compute:cjs:end-->')]:
    warn('compute/build.py 页面 JS 里「快照」提示的日期不是 %s：去改 compute/build.py 里的 2026-11-19' % SNAP)
for w in WARN: print('提示：' + w)
if CHECK:
    print('check only:', 'would change' if src != before else 'no change'); sys.exit(0)
if src != before: open(REPORT, 'w', encoding='utf-8').write(src)
print('wrote' if src != before else 'unchanged', REPORT, len(before), '->', len(src), 'chars')
