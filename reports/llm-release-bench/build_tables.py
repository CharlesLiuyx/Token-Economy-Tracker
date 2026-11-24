#!/usr/bin/env python3
"""把 data/models.json + data/vendors.json 写进报告 HTML：
  顶栏（含「前沿 / 大厂 / 开源」标签筛选器）与首屏的快照日期 / 分组模型计数、第 2 章的表 2-1（全部模型）、表 2-2、
  图 2-1 的模型泳道（全部厂商）、第 3 章（全部模型）的图 3-1…3-5、附录「核对方式」与大厂 / 开源来源、
  新厂商的配色 CSS、样式块（c34css，含筛选 CSS）与页面脚本（c34js：散点标签避让、标签筛选）。
2026-11-24：原第 2 章（前沿）和第 3 章（大厂与开源）合并成第 2 章；原第 4、5 章改为第 3、4 章。
  HTML 里的 id 沿用旧名（section s4 / s5、h41…h45、f41…f45），只改可见编号，免得 compute 与 qa 的选择器跟着变。
标签：vendors.json 的 vendors[].tags（一家可多个，Google＝前沿＋大厂），group＝主分组（图例按它分组）。
  每个表行、组标题行、时间轴泳道、图 3-x 的行 / 点 / 图例项都带 data-tags="…"（按 groups 顺序、空格分隔）；
  顶栏筛选把关掉的标签写进 <html data-off="…">，flt_css() 生成的规则隐藏「全部标签都被关掉」的元素（标签之间是「或」）。
  表 2-2 与 2.3 节算力不带标签、不受筛选影响。名次与色条按全部模型算，不随筛选变。
算力三条泳道、图 2-2 / 2-3、表 2-3 归 compute/build.py 管（标记 <!--compute:…-->），本脚本只认 <!--data:…-->，互不覆盖。

幂等：每块包在 <!--data:NAME:start--> … <!--data:NAME:end--> 里，只替换标记之间的内容。重复跑结果逐字节一致。

另外输出 i18n/static.json 里的固定文字块（<!--data:s-NAME:…-->：顶栏控件与目录头、各章标题、第 1 章结论、
第 4 章（怎么读）、附录手写来源、图 2-1 图注与图例、TERMS 术语表与页面 JS 的界面字），以及 h1、图 2-1 的 <div class="hl">（横轴）。
所有文字都输出中英两份（见 bilingual.py 开头的约定），页面按 :root[data-lang] 显示其一。

用法：python3 build_tables.py [报告路径] [--data 数据目录] [--check] [--no-ch1-check]
  报告路径默认＝本脚本旁边的正式报告；--data 默认＝本脚本旁的 data/；--check 只校验不写盘；
  --no-ch1-check 跳过第 1 章新增结论的数字核对（只给 qa/rehearsal.py 这类虚构数据的演练用）。
只用 Python 标准库。

====================================================================== 规则
表 2-1（全部模型；2026-11-24 由原表 2-1 与表 3-1 合并）
  · 行序：厂商按 vendors.json 的顺序分组（没有模型的厂商不出组标题行）；组内先放已发布与受限模型，按发布日从新到旧，
    同日按 JSON 里的先后；再放内部代号模型，按训练完成日从新到旧（发布列写训练完成时间）。
    组标题行在厂商名后列出它的全部标签（前沿 / 大厂 / 开源）。
  · 列＝t21.groups[].cols 点名的列：基本列 release / price_in / price_out / license / params，其余是 benches 的 key；
    每个 bench 都必须在某组的 cols 里。一个分数都没有的 bench 列不出（打印提示），组里没有列时整组不出。
    分组表头＝每组一格，组的第一列加 gs（分组线）。列宽：layout.t21（模型列、各基本列；bench 列默认同宽，可按 key 单独设）。
  · 前三名 r1/r2/r3：每列按 v 去重后从高到低排（「密集名次」：并列同名次，下一名紧接），只给前三个不同的值；全部模型一起排。
    direction=lower 的列反过来排。名次写进格子 data-tip：「{测试名}：{显示值}{单位}。本列第 N 名。{note}」。
  · 分数色条 --w：bar=auto 时，本列有分数的模型 ≥5 个→ 8 + 92 ×（v − 最低）/（最高 − 最低）；<5 个→ v / 最高 × 100。
    bar=zero 总是从 0 画；bar=minmax 总是最低到最高。保留 1 位小数。
  · 发布列色条：8 + 92 ×（发布日 − 最早发布日）/（最晚 − 最早），按天算，所有有发布日的模型一起比。
  · 价格色条：价格 / 公开模型（status=public）里的最高价 × 100，最短 1.5%，1 位小数；受限模型价格超过这个最高价时不画长度，加 over（斜纹）。
    显示：整数 $3，非整数 $1.50；有 in_next / out_next 时写成 $2<small>→$4</small>。
  · 开放权重 / 参数：模型的 license / params（{d, tip}）；没写的闭源模型（前沿三家）显示「否」/「—」（ui.license_closed / params_na_tip）。
  · 模型名格子挂 row_tip（简介＋没填进表的分数）；格子显示值可带角标（<sup>AA</sup>），提示文字里去掉角标。
  · 表头 data-tip：desc + 「 有分数的模型：N 个。」。table 的 width＝各列之和，3 位小数。
表 2-2
  · 列＝t22.columns，按 vendor 连续合并成分组表头；每个分组第一列加 gs。行＝sections → rows。
  · 每行单独算：色条 v / 本行最高 × 100（1 位小数）；本行前三名同表 2-1 的密集名次。
  · 格子 data-tip：「{列名} · {测试名}：{显示值}{单位}。本行第 N 名。{note}」；dagger=true 时显示值后加 <sup>†</sup>。
  · 单元格厂商类：vendors.json 的 t22_class（va / vo / vg …）。
图 2-1（模型泳道，全部厂商；算力泳道归 compute）
  · 横轴由快照日推导（bilingual.axis）：快照日所在月往前 5 个月的月初 t0 → 快照月最后一天（落在 100%），span＝两者相差的天数。
    compute/build.py 用同一个函数，所以两边永远一致。
  · 泳道顺序＝vendors.json 的 timeline_lanes；没有（落在横轴内的）事件的泳道不出。left＝（日期 − t0）/ span × 100，3 位小数。
    落在横轴外的点节点不画（打印提示）；区间节点（有 end）裁到横轴内，整段在外就不画。
    区间节点：left 取 date，width＝（end − date）/ span × 100。
  · 每条泳道的竖线：每月 1 日（不含 t0）一条 ml；快照日一条 vl。泳道内节点按 date 排序（同日按 JSON 先后）。
  · 节点 data-tip：「YYYY-MM-DD：{tip}」；区间节点直接用 tip。hollow=true → 空心（mu，只是宣布）。
  · 事件 before=true 且早于横轴起点：不画节点，写在泳道名下的小字（← M/D 名称，悬停看全文）。
图 3-1 / 3-2 / 3-3（id f41 / f42 / f43）
  · 取对应 bench 有分数的全部模型，按 v 从高到低；同分按表 2-1 的行序。
  · mark＝bar：条长＝v / 轴最大值；mark＝dot：点位置＝（v − 轴最小值）/（轴最大 − 轴最小）。数值保留 2 位小数并去掉末尾 0。
    轴：figures.*.axis 的 min / max / step；数据超出时自动按 step 外扩并打印提示。刻度类 dN＝（max − min）/ step。
  · xcol＝price：第 4 列＝输出价；xcol＝cost：第 4 列＝note 里「每题成本 $X」的 $X（Vals 两列的 note 必须写这一句，中英一致）。
  · 行名一律用完整的 name（不自造缩写）；名字长的在窄屏折成两行，不截断。
图 3-4（散点，id f44）
  · 横轴＝输出价（对数，figures.f44.xaxis 的 min / max / ticks），纵轴＝AA（yaxis，超出自动外扩）。有 AA 但没有 price 的模型不画，列进图注。
  · 实心＝不开放权重，空心（.spt.ow）＝开放权重（license 不是「否」）。价格与 AA 都相同的点左右错开 12px（--dx）。
  · 点按 AA 从高到低排在 DOM 里，页面 JS fitScatter 依次给标签找位置（右、左、上、下、四角…），放不下就隐藏标签（悬停仍有提示）。
图 3-5（id f45）
  · 每个 panel 一个 bench，规则同 3-1，横轴 0–100；没有分数的模型不画，整个 panel 没有分数时不出。行名用完整 name，放不下折两行。
图例（图 3-x）：只列这张图里出现的厂商，按 vendors.json 的 groups（主分组）分组（组名在前），组内按 vendors.json 顺序。
计数：首屏「前沿 N 个 + 大厂与开源 M 个已发布模型」＝带 / 不带「前沿」标签的厂商里 status≠internal 的模型数；内部代号模型单独计。
第 1 章后 3 条结论：check_ch1() 用数据重算关键数字，与 i18n/static.json 的 blocks.ch1 对不上就构建失败。
"""
import datetime as dt, html, itertools, json, math, os, re, sys

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
TAGS = [g['key'] for g in VGROUPS]                                 # 顶栏筛选器的标签＝groups 的 key（前沿 / 大厂 / 开源）
for v in VEN:
    v.setdefault('tags', [v['group']])
    assert v['group'] in v['tags'] and all(t in GK for t in v['tags']), ('vendors.json：tags 必须含 group，且都在 groups 里', v['key'], v['tags'])
def tags_of(vk): return ' '.join(t for t in TAGS if t in VK[vk]['tags'])   # 按 groups 顺序，空格分隔（CSS 选择器用整串比较）
def dtags(vk): return ' data-tags="%s"' % tags_of(vk)
def is_frontier(vk): return 'frontier' in VK[vk]['tags']
BEN = D['benches']; BK = {b['key']: b for b in BEN}
ALLM = D['models']                                                # 全部模型（第 4 章）
for m in ALLM:
    assert m['vendor'] in VK, ('vendors.json 里没有这个厂商', m['vendor'], m['name'])
    for k in m.get('scores', {}): assert k in BK, ('models.json 里没有这个 bench', k, m['name'])
MODELS = [m for m in ALLM if is_frontier(m['vendor'])]           # 带「前沿」标签的厂商：首屏计数、第 1 章核对
M3 = [m for m in ALLM if not is_frontier(m['vendor'])]           # 其余（大厂与开源）：首屏计数、第 1 章核对
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
ROWS = row_order(ALLM)                                            # 表 2-1：全部模型，按厂商分组
FLAT_ALL = [m for _, ms in ROWS for m in ms]                      # 第 3 章（图 3-x）：同分时按表 2-1 的行序

def dense_rank(vals, lower=False):
    u = sorted(set(vals), reverse=not lower)[:3]
    return {v: i + 1 for i, v in enumerate(u)}

def price_txt(p, nxt):
    def one(x): return ('$%d' % x) if float(x) == int(x) else ('$%.2f' % x)
    return one(p) + ('<small>→%s</small>' % one(nxt) if nxt is not None else '')
def price_plain(p):
    return ('$%d' % p) if float(p) == int(p) else ('$%.2f' % p)

T21_BASIC = ('release', 'price_in', 'price_out', 'license', 'params')
T21_COLS = [k for g in D['t21']['groups'] for k in g['cols']]
for k in T21_COLS: assert k in T21_BASIC or k in BK, ('t21.groups[].cols 里有不认识的列', k)
for b in BEN: assert b['key'] in T21_COLS, ('bench 不在 t21.groups[].cols 里（表 2-1 不出这一列）', b['key'])

def price_max(side, models=None):
    v = [m['price'][side] for m in (ALLM if models is None else models) if m['status'] == 'public' and 'price' in m]
    return max(v)


# ------------------------------------------------------------------ text-width estimate (列宽告警用，两种语言都估)
def est_em(text, fs=1.0):
    t = re.sub(r'<[^>]+>', '', html.unescape(text)); w = 0.0
    for ch in t: w += 1.0 if ord(ch) > 0x2e80 else 0.56
    return w * fs + 0.9   # 左右内边距约 0.45em × 2
def est_bi(x, fs=1.0): b = bi(x); return max(est_em(b.zh, fs), est_em(b.en, fs))

# ------------------------------------------------------------------ 开源 / 闭源标签（models.json 的 open_weights；内部代号模型不加）
def ow_of(x):
    if x.get('status') == 'internal': return None
    if 'open_weights' not in x:
        warn('「%s」缺 open_weights 字段，按闭源处理（新模型必须填）' % bi(x.get('name', x.get('label', '?'))).zh); return False
    return bool(x['open_weights'])
def ow_tag(m):
    o = ow_of(m)
    if o is None: return ''
    return '<span class="tag ow-%s"%s>%s</span>' % ('o' if o else 'c', att('data-tip', ui('ow_open_tip' if o else 'ow_closed_tip')), TX(ui('ow_open' if o else 'ow_closed')))
def ow_suffix(x):
    """提示文字末尾补一句开源 / 闭源（时间轴节点、表 2-2 列头这类放不下标签的地方）。字段缺失时不补。"""
    if 'open_weights' not in x: return ''
    return ui('ow_tip_open' if x['open_weights'] else 'ow_tip_closed')

def hints(items, mp):
    out = ['<div class="hints">']
    for it in items:
        if 'text' in it: out.append('<span>%s</span>' % TX(subst(it['text'], mp)))
        else: out.append('<span class="hint"%s>%s<i>?</i></span>' % (att('data-tiph', subst(it['tip'], mp)), TX(it['label'])))
    out.append('</div>')
    return ''.join(out)

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
        h.append('<th class="num wrapok%s"%s>%s</th>' % (' gs' if c['id'] in first else '', att('data-tip', bi(c['tip']) + ow_suffix(c)), TX(c['label'])))
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
def lanes_html(snap, fig):
    """全部模型泳道（vendors.json 的 timeline_lanes 顺序）；snap＝该图的快照日（横轴、快照竖线都由它推导）。
    泳道名与轨道都带 data-tags（厂商标签），顶栏筛选器按它隐藏。"""
    t0, span, months = axis(snap)
    def ps(d): return (day(d) - t0).days / span * 100
    lines = ''.join('<i class="ml" style="left:%s%%"></i>' % f3((d - t0).days / span * 100) for d in months[1:])
    lines += '<i class="vl" style="left:%s%%"></i>' % f3(ps(snap))
    out = []
    evs = D['timeline_events']
    for e in evs:
        assert any(l['lane'] == e['lane'] for l in VJ['timeline_lanes']), ('vendors.json 的 timeline_lanes 里没有这条泳道', e['lane'])
    lanes = VJ['timeline_lanes']
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
        small = ''.join('<small class="pre noterm"%s>← %d/%d %s</small>' % (att('data-tip', L('%s：%s', '%s: %s') % (e['date'], e['tip']) + ow_suffix(e)), day(e['date']).month, day(e['date']).day, TX(e['label']))
                        for e in sorted(pre, key=lambda e: e['date']))
        out.append('<div class="hl-lab li" data-key="%s"%s%s>%s%s%s</div>' % (vk, dtags(vk), att('data-tip', ui('lane_tip', name=v['name'])), sw, TX(ln.get('label', v['name'])), small))
        out.append('<div class="hl-track" data-lane="%s"%s>%s' % (ln['lane'], dtags(vk), lines))
        for e in es:
            if 'end' in e:
                a, b = max(0.0, ps(e['date'])), min(100.0, ps(e['end']))   # 区间节点裁到横轴内
                out.append('<span class="pin rng" data-key="%s" style="left:%s%%;width:%s%%"%s><span class="pl noterm">%s</span></span>' % (
                    vk, f3(a), f3(b - a), att('data-tip', e['tip']), TX(e['label'])))
            else:
                d = day(e['date'])
                out.append('<span class="pin%s" data-key="%s" style="left:%s%%"%s><i class="pd"></i><span class="pl noterm"><small>%d/%d</small> %s%s</span></span>' % (
                    ' mu' if e.get('hollow') else '', vk, f3(ps(e['date'])), att('data-tip', L('%s：%s', '%s: %s') % (e['date'], e['tip']) + ow_suffix(e)), d.month, d.day, TX(e['label']),
                    ('<span class="tag">%s</span>' % TX(e['tag'])) if e.get('tag') else ''))
        out.append('</div>')
    return ''.join(out)
def f21_lanes(): return lanes_html(SNAP, '图 2-1')

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

# ------------------------------------------------------------------ 表 2-1（全部模型；2026-11-24 由原表 2-1、表 3-1 合并）
def dplain(d):
    """格子显示值去掉角标（<sup>AA</sup> 等），给提示文字用。"""
    return bi(d).map(lambda x: re.sub(r'<sup>.*?</sup>', '', x))
def t21_layout():
    """表 2-1 实际出的列：配置里点名的列，去掉一个分数都没有的 bench 列；组里没有列时整组不出。"""
    T = D['t21']; gs = []
    for g in T['groups']:
        ks = []
        for k in g['cols']:
            if k in T21_BASIC: ks.append(k); continue
            if not any(k in m.get('scores', {}) for m in FLAT_ALL):
                warn('表 2-1 列「%s」没有任何分数，不出（数据里有了分数会自动出现）' % bi(BK[k]['name']).zh); continue
            ks.append(k)
        if ks: gs.append((g, ks))
    return gs
GROUPS = t21_layout()
BENCH_ORDER = [k for g, ks in GROUPS for k in ks if k not in T21_BASIC]
def t21():
    T = D['t21']; L_ = D['layout']['t21']
    pin_max, pout_max = price_max('in'), price_max('out')
    rel = [day(m['release']) for m in ALLM if 'release' in m]
    rmin, rmax = min(rel), max(rel)
    colv = {k: [m['scores'][k]['v'] for m in FLAT_ALL if k in m.get('scores', {})] for k in BENCH_ORDER}
    ranks = {k: dense_rank(colv[k], BK[k]['direction'] == 'lower') for k in BENCH_ORDER}
    first = set(ks[0] for g, ks in GROUPS)
    order = [k for g, ks in GROUPS for k in ks]
    widths = [L_['model']] + [L_.get(k, L_['bench']) for k in order]
    ncol = len(widths)
    h = ['<div class="tblwrap wide" id="t21"%s><table style="width:%sem"><colgroup>' % (att('data-toc', T['toc']), f3(sum(widths)))]
    h += ['<col style="width:%sem">' % f3(w) for w in widths]
    h.append('</colgroup><thead><tr><th rowspan="2" class="c0"%s>%s</th>' % (att('data-tip', T['c0']['tip']), TX(T['c0']['label'])))
    for g, ks in GROUPS:
        h.append('<th colspan="%d" class="gh gs"%s>%s</th>' % (len(ks), att('data-tip', g['tip']), TX(g['label'])))
    h.append('</tr><tr class="h2">')
    bs = T['basic']
    for k in order:
        gs = ' gs' if k in first else ''
        if k in T21_BASIC:
            tip = subst(bs[k]['tip'], {'max': price_plain(pin_max if k == 'price_in' else pout_max)})
            h.append('<th class="num%s"%s>%s</th>' % (gs, att('data-tip', tip), TX(bs[k]['label'])))
        else:
            b = BK[k]
            h.append('<th class="num%s"%s>%s</th>' % (gs, att('data-tip', bi(b['desc']) + ui('count_suffix', n=len(colv[k]))), TX(b['label'])))
            if est_bi(b['label'], 0.93) > L_.get(k, L_['bench']): warn('表 2-1 列「%s」表头可能放不下（估 %.2fem > %.3fem）' % (bi(b['label']).zh, est_bi(b['label'], .93), L_.get(k, L_['bench'])))
    h.append('</tr></thead><tbody>')
    for vk, ms in ROWS:
        v = VK[vk]
        gk = ''.join('<small class="gk"%s>%s</small>' % (att('data-tip', GK[tg]['tip']), TX(GK[tg]['label'])) for tg in tags_of(vk).split())
        h.append('<tr class="grp"%s><td colspan="%d"><span class="gl"><span class="sw k-%s"></span>%s%s</span></td></tr>' % (dtags(vk), ncol, vk, TX(v['name']), gk))
        for m in ms:
            tag = m.get('tag')
            nm = TX(m['name']) + ('<span class="tag"%s>%s</span>' % (att('data-tip', tag['tip']), TX(tag['text'])) if tag else '') + ow_tag(m)
            if max(est_em(bi(m['name']).get(l)) + (est_em(bi(tag['text']).get(l), 0.78) if tag else 0) + (est_em(bi(ui('ow_closed')).get(l), 0.78) if ow_of(m) is not None else 0) for l in ('zh', 'en')) + 0.4 > L_['model']:
                warn('表 2-1 模型名「%s」可能放不下模型列' % bi(m['name']).zh)
            h.append('<tr class="v-%s"%s><td class="mn c0 noterm"%s><span class="sw k-%s"></span>%s</td>' % (vk, dtags(vk), att('data-tip', m['row_tip']) if m.get('row_tip') else '', vk, nm))
            for k in order:
                gs = ' gs' if k in first else ''
                if k == 'release' and 'release' not in m:          # 内部代号模型：发布列写训练完成时间
                    tr = m['trained']
                    h.append('<td class="num na%s"%s>%s</td>' % (gs, att('data-tip', tr['tip']), TX(tr['label'])))
                elif k == 'release':
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
                    if p[side] > mx:
                        if m['status'] == 'public': warn('公开模型 %s 的价格超过最高价？' % bi(m['name']).zh)
                        h.append('<td class="num cb nb over%s"%s>%s</td>' % (gs, tip, txt))
                    else: h.append('<td class="num cb nb%s"%s style="--w:%s%%">%s</td>' % (gs, tip, f1(max(1.5, p[side] / mx * 100)), txt))
                elif k in ('license', 'params'):
                    x = m.get(k)
                    if not x and m['status'] != 'internal':      # 没写 license / params 的闭源模型（前沿三家）：否 / 未公开
                        if k == 'license' and ow_of(m) is False: x = {'d': UI['license_closed'], 'tip': UI['license_closed_tip']}
                        elif k == 'params': h.append('<td class="num na%s"%s>—</td>' % (gs, att('data-tip', UI['params_na_tip']))); continue
                    if not x: h.append('<td class="num na%s">—</td>' % gs); continue
                    na = ' na' if (k == 'license' and bi(x['d']).en == 'No') or bi(x['d']).zh == '—' else ''
                    h.append('<td class="num%s%s"%s>%s</td>' % (na, gs, att('data-tip', x['tip']), TX(x['d'])))
                    if est_bi(x['d'], 1.0) > L_[k]: warn('表 2-1「%s」的%s「%s」可能放不下' % (bi(m['name']).zh, k, bi(x['d']).en))
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
def t21_hints():
    names = [bi(g['short']) for g, ks in GROUPS if g['key'] != 'basic']
    return hints(D['t21']['hints'], {'n_models': len(FLAT_ALL), 'n_bench': len(BENCH_ORDER), 'n_groups_zh': ndigit(len(names)), 'group_names': join(L('、', ', '), names),
                                     'price_in_max': price_plain(price_max('in')), 'price_out_max': price_plain(price_max('out'))})
# ------------------------------------------------------------------ 第 4 章：图 4-1…4-5（全部模型）
def legend(keys, extra=''):
    """图例按厂商分组（vendors.json 的 groups 顺序）：组名 + 组内厂商色块。只列这张图里出现的厂商。"""
    parts = []
    for g in VGROUPS:
        ks = [k for k in VORD if k in keys and VK[k]['group'] == g['key']]
        if not ks: continue
        gt = ' '.join(t for t in TAGS if any(t in VK[k]['tags'] for k in ks))    # 组内全部厂商都被筛掉时整组隐藏
        parts.append('<span class="lgg" data-tags="%s"><span class="lgn"%s>%s</span>%s</span>' % (gt, att('data-tip', g['tip']), TX(g['label']), ''.join(
            '<span class="li" data-key="%s"%s%s><i class="sw k-%s"></i>%s</span>' % (k, dtags(k), att('data-tip', VK[k]['legend_tip']), k, TX(VK[k]['name'])) for k in ks)))
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
    mp = {'snapshot': SNAP}
    if a: mp.update({'min': t2(a['min']), 'max': t2(a['max'])})
    return '<figure id="%s"%s><figcaption>%s<span class="hint"%s>%s<i>?</i></span></figcaption>' % (
        fid, att('data-toc', F['toc']), TX(F['caption']), att('data-tiph', subst(F['source_tip'], mp)), TX(ui('source')))
def fname(m): return m['name']                                   # 图里一律用完整模型名，不自造缩写
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
        h.append('<div class="row c4" data-key="%s"%s%s><span class="nm noterm"><i class="sw k-%s"></i><span>%s%s</span></span><span class="track d%d">%s</span><span class="v">%s</span><span class="x">%s</span></div>' % (
            m['vendor'], dtags(m['vendor']), att('data-tip', tip + ow_suffix(m)), m['vendor'], TX(fname(m)), ow_tag(m), a['n'], mark, TX(c['d']), x))
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
            h.append('<div class="row c3" data-key="%s"%s%s><span class="nm noterm"><i class="sw k-%s"></i><span>%s%s</span></span><span class="track d%d"><span class="mark bar" style="width:%s%%"></span></span><span class="v">%s</span></div>' % (
                m['vendor'], dtags(m['vendor']), att('data-tip', tip + ow_suffix(m)), m['vendor'], TX(fname(m)), ow_tag(m), a['n'], t2((c['v'] - a['min']) / (a['max'] - a['min']) * 100), TX(c['d'])))
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
        dots.append('<span class="spt%s" data-key="%s"%s style="left:%s%%;bottom:%s%%%s"%s><i class="mark"></i><span class="pl noterm">%s</span></span>' % (
            ' ow' if ow else '', m['vendor'], dtags(m['vendor']), f3(px(m['price']['out'])), f3(py(c['v'])), dx, att('data-tip', tip), TX(fname(m))))   # 标签只留文字：点本身就是同色方块
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
# ------------------------------------------------------------------ 格内色条的深浅上限（保证压在色条上的数字可读）
# 表 2-1 / 2-2 / 3-1 的分数格：色条＝厂商色以透明度 --al 叠在页面底色上（td.cb 的 --bc），数字照常用 --ink。
# 对每家、每个主题二分求「最深允许的透明度」A：底色混入色条、再叠上行悬停的 --hover 后，与 --ink 的对比度仍 ≥ 6.0（检查门槛 4.5；
# 4.5 刚好及格的深蓝 / 海军蓝底配黑字读起来仍吃力，所以构建时留到 6.0）。
# 名次分档在这个上限内按原比例缩放：r1＝min(74%, A)，r2、r3、普通格按 48 / 30 / 14 ÷ 74 同比缩小；A ≥ 74% 时保持原值。
THEME = {'light': {'bg': (255, 255, 255), 'ink': (0x14, 0x14, 0x13), 'hover': ((20, 20, 19), .05)},
         'dark': {'bg': (0x1a, 0x1a, 0x19), 'ink': (0xf0, 0xef, 0xec), 'hover': ((240, 239, 236), .07)}}
AL_DEFAULT = {'r1': 74, 'r2': 48, 'r3': 30, 'n': 14}
def _rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def _lum(c):
    def ch(x):
        x /= 255; return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in c); return 0.2126 * r + 0.7152 * g + 0.0722 * b
def _contrast(a, b):
    la, lb = _lum(a), _lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
def _mix(fg, bg, a): return tuple(a * f + (1 - a) * b for f, b in zip(fg, bg))
def bar_alpha_max(hexc, mode, target=6.0):
    T = THEME[mode]; vc = _rgb(hexc)
    def ok(a):
        c = _mix(vc, T['bg'], a); h = _mix(T['hover'][0], c, T['hover'][1])
        return min(_contrast(T['ink'], c), _contrast(T['ink'], h)) >= target
    if ok(1.0): return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if ok(mid): lo = mid
        else: hi = mid
    return lo
def bar_tiers(hexc, mode):
    A = math.floor(bar_alpha_max(hexc, mode) * 1000) / 10          # 百分比，向下取 0.1
    if A >= AL_DEFAULT['r1']: return dict(AL_DEFAULT), A
    return {k: math.floor(v / AL_DEFAULT['r1'] * A * 10) / 10 for k, v in AL_DEFAULT.items()}, A
def bar_alpha_css():
    out = ['/* 格内色条深浅上限：保证色条上的数字与文字色对比度 ≥ 4.5（build_tables.py 的 bar_alpha_max） */',
           '/* 色条格里的角标与小字（†、*、AA、→$4）原来是 --ink3，压在色条上不够 4.5，改用正文色，靠字号区分主次 */',
           'td.cb small,td.cb sup{color:var(--ink)}']
    for mode in ('light', 'dark'):
        pre = '' if mode == 'light' else ':root[data-theme=dark] '
        for v in VEN:
            t, A = bar_tiers(v[mode], mode)
            if t == AL_DEFAULT: continue
            k, c22 = v['key'], v['t22_class']
            for tier, cls in (('n', ''), ('r1', '.r1'), ('r2', '.r2'), ('r3', '.r3')):
                out.append('%str.v-%s>td.cb%s:not(.nb),%std.%s.cb%s{--al:%s%%}' % (pre, k, cls, pre, c22, cls, ('%g' % t[tier])))
    return '\n'.join(out)

def vendor_css():
    used = {m['vendor'] for m in ALLM} | {l['vendor'] for l in VJ['timeline_lanes'] if any(e['lane'] == l['lane'] for e in D['timeline_events'])}
    new = [v for v in VEN if v['key'] in used and not v.get('builtin_css')]
    dn = set()
    for fid in ('f41', 'f42', 'f43'):
        F = D['figures'][fid]; k = F['bench']; dn.add(axis_of(F, [m['scores'][k]['v'] for m in ranked(k)], '图 %s-%s' % (fid[1], fid[2]))['n'])
    dn.add(axis_of(D['figures']['f45'], [], 'f45')['n'])
    dn -= {4, 5, 7}                                    # 原文 CSS 已有 .track.d4 / d5 / d7

    c = ['<style id="data-css">', '/* build_tables.py 生成：全部厂商的品牌色（vendors.json；前沿三家与报告原 CSS 一致）、新厂商的配色规则与新刻度数 */']
    allv = [v for v in VEN if v['key'] in used]
    c.append(':root{%s}' % ''.join('%s:%s;' % (v['css_var'], v['light']) for v in allv))
    c.append(':root[data-theme=dark]{%s}' % ''.join('%s:%s;' % (v['css_var'], v['dark']) for v in allv))
    for v in new:
        k, cv = v['key'], v['css_var']
        c.append('tr.v-%s{--vc:var(%s)}\n.pin[data-key=%s]{--vc:var(%s)}\ntd.%s{--vc:var(%s)}\n.k-%s{background:var(%s)}\n.sw.ho-%s{background:transparent;box-shadow:inset 0 0 0 1.5px var(%s)}\n[data-key~=%s] .mark{background:var(%s)}' % (
            k, cv, k, cv, v['t22_class'], cv, k, cv, k, cv, k, cv))
        c.append('figure[data-hl=%s] [data-key]:not([data-key~=%s]){opacity:.3}\nfigure[data-hl=%s] [data-key~=%s] .mark{outline:1px solid var(--ink);outline-offset:1px}\nfigure[data-hl=%s] .li[data-key~=%s]{background:var(--hover);color:var(--ink)}' % (k, k, k, k, k, k))
    for n in sorted(dn): c.append('.track.d%d{background-size:calc(100%% / %d) 100%%}' % (n, n))
    c.append(bar_alpha_css())
    c.append('</style>')
    return '\n'.join(c)

# ------------------------------------------------------------------ 第 3、4 章的样式与页面脚本（表 3-1、图 3-2、分组图例、图 4-4 散点）
C34_CSS = """.tag.ow-o{border-color:var(--ink3);color:var(--ink2)}
.tag.ow-c{border-color:transparent;background:var(--soft);color:var(--ink3)}
tr.grp .gk{font-weight:400;color:var(--ink3);font-size:.9em;margin-left:8px;cursor:help}
.hl-lab small.pre{font-weight:400;color:var(--ink3);white-space:normal;line-height:1.25;cursor:help}
#f21 .hl-lab.li{display:block;white-space:normal;line-height:1.25}
#f21 .hl-lab.li small{display:block}
#flt{display:inline-flex;flex:none;border:1px solid var(--line);height:18px;line-height:16px;margin-right:6px}
#flt button{padding:0 6px;color:var(--ink2)}
#flt button+button{border-left:1px solid var(--line)}
#flt button.on{background:var(--ink);color:var(--bg)}
#flt button:not(.on){text-decoration:line-through;color:var(--ink3)}
#flt button:not(.on):hover,#flt button.on:hover{background:var(--hover);color:var(--ink)}
#s4 .row{height:auto;min-height:26px;padding-top:2px;padding-bottom:2px}
#s4 .row.hd{min-height:22px}#s4 .row.ax{min-height:18px;padding-top:0;padding-bottom:0}
#s4 .row .nm{white-space:normal;overflow:visible;text-overflow:clip;line-height:1.2;display:flex;align-items:baseline}
#s4 .row .nm .tag{font-size:11px;line-height:13px;padding:0 3px;margin-left:5px;vertical-align:1px}
#s4 .row .nm .sw{flex:none;width:9px;height:9px;margin-right:5px;vertical-align:0}
#s4 .row.c4{grid-template-columns:190px minmax(120px,1fr) 46px 124px}
#s4 .row.c3{grid-template-columns:minmax(0,170px) minmax(90px,1fr) 50px;min-height:25px}
@media (max-width:860px){#s4 .row.c4{grid-template-columns:132px minmax(90px,1fr) 44px 108px}}
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
def flt_css():
    """顶栏筛选：<html data-off="关掉的标签…">。元素的 data-tags 里每个标签都被关掉时隐藏（标签之间是「或」）。"""
    out = []
    for n in range(1, len(TAGS) + 1):
        for combo in itertools.combinations(TAGS, n):
            out.append(':root%s [data-tags="%s"]' % (''.join('[data-off~=%s]' % t for t in combo), ' '.join(combo)))
    return ',\n'.join(out) + '{display:none!important}'
def c34_css():
    ks = ''.join('.sc .spt[data-key=%s]{--vc:var(%s)}' % (v['key'], v['css_var']) for v in VEN)
    return '<style id="c34-css">\n/* build_tables.py 生成：表 2-1 组标题标签、图 2-1 泳道小字、顶栏标签筛选、图 3-x 分组图例、图 3-4 散点的样式 */\n%s\n%s\n%s\n</style>' % (C34_CSS, ks, flt_css())
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

/* ---- top-bar tag filter (Frontier / Big Tech / Open-weight): tags that are off go into <html data-off>; CSS hides every [data-tags] whose tags are all off.
   Click toggles one tag, Shift-click keeps only that tag; at least one tag stays on. Saved as mdl-off. ---- */
(function(){
  var box=$('#flt');if(!box)return;
  var ALL=$$('[data-flt]',box).map(function(b){return b.getAttribute('data-flt')});
  function cur(){return (R.getAttribute('data-off')||'').split(' ').filter(function(k){return ALL.indexOf(k)>=0})}
  function apply(off,init){
    if(off.length)R.setAttribute('data-off',off.join(' '));else R.removeAttribute('data-off');
    $$('[data-flt]',box).forEach(function(b){var on=off.indexOf(b.getAttribute('data-flt'))<0;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on?'true':'false')});
    if(!init){try{localStorage.setItem('mdl-off',off.join(' '))}catch(e){}hideTip();relayout()}
  }
  var off=[];try{off=(localStorage.getItem('mdl-off')||'').split(' ').filter(function(k){return ALL.indexOf(k)>=0})}catch(e){}
  if(off.length>=ALL.length)off=[];
  apply(off,true);if(off.length)relayout();
  box.addEventListener('click',function(e){
    var b=e.target.closest('[data-flt]');if(!b)return;
    var k=b.getAttribute('data-flt'),c=cur(),nx;
    if(e.shiftKey)nx=ALL.filter(function(x){return x!==k});
    else nx=c.indexOf(k)>=0?c.filter(function(x){return x!==k}):c.concat([k]);
    if(nx.length>=ALL.length)return;
    apply(nx);
  });
})();
"""

# ------------------------------------------------------------------ i18n/static.json 的固定文字块
STR = SJ['strings']
LANG_SWITCH = '<span id="lang" role="group" data-i18n-skip%s%s><button data-set="lang:zh" lang="zh-CN">中文</button><button data-set="lang:en" lang="en">EN</button></span>\n  '
def flt_html():
    """顶栏的标签筛选器：每个标签一个开关按钮（默认全开）。状态写在 <html data-off="…">，CSS 按它隐藏（c34css 的 flt_css）。"""
    bs = ''.join('<button data-flt="%s" class="on" aria-pressed="true">%s</button>' % (g['key'], TX(g['label'])) for g in VGROUPS)
    def who(l):
        sep, colon = ('、', '：') if l == 'zh' else (', ', ': ')
        return ''.join('<br><b>%s</b>%s%s' % (get(g['label'], l), colon, sep.join(get(v['name'], l) for v in VEN if g['key'] in v['tags'])) for g in VGROUPS)
    tip = by(lambda l: get(UI['flt_tip'], l) + who(l))
    return '<span id="flt" role="group"%s%s>%s</span>' % (att('aria-label', STR['flt_aria']), att('data-tiph', tip), bs)
def render_tpl(name):
    t = SJ['templates'][name]
    def tx(m):
        k = m.group(1); assert k in STR, ('static.json strings 缺键', k); return TX(STR[k])
    def at(m):
        k = m.group(2); assert k in STR, ('static.json strings 缺键', k); return att(m.group(1), STR[k])
    t = re.sub(r'\{\{t:([a-z0-9_]+)\}\}', tx, t)
    t = re.sub(r'\{\{a:([a-z-]+):([a-z0-9_]+)\}\}', at, t)
    if '{{flt}}' in t: t = t.replace('{{flt}}', flt_html())
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
for v in VEN:                                                     # 前沿三家的颜色也写在报告原 CSS 里，必须与 vendors.json 一致
    if v.get('builtin_css'):
        for mode, rx in (('light', r':root\{[^}]*%s:(#[0-9A-Fa-f]{6});'), ('dark', r':root\[data-theme=dark\]\{[^}]*%s:(#[0-9A-Fa-f]{6});')):
            m_ = re.search(rx % re.escape(v['css_var']), src)
            assert m_ and m_.group(1).lower() == v[mode].lower(), ('报告原 CSS 里 %s 的%s色与 vendors.json 不一致：改 <style> 开头的 :root' % (v['css_var'], mode), m_ and m_.group(1), v[mode])
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
