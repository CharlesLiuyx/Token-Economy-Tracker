#!/usr/bin/env python3
# 留档：2026-11-22 从手写版报告反抽数据用的一次性脚本，依赖当时的 HTML 结构，以后不要再跑。
"""一次性：从手写版报告 HTML 反抽 data/models.json 与 data/vendors.json。
用法：python3 extract.py 报告.html 输出目录
抽完由 build_tables.py 重建，再由 qa/diff_check.py 证明重建结果与原文逐字节一致。"""
import json, os, re, sys
from bs4 import BeautifulSoup

SRC, OUT = sys.argv[1], sys.argv[2]
s = open(SRC, encoding='utf-8').read()

def seg(start, end_tag):
    i = s.index(start); j = s.index(end_tag, i) + len(end_tag); return s[i:j]

def soup(h): return BeautifulSoup(h, 'html.parser')
def inner(el): return el.decode_contents().replace('<br/>', '<br>')
def cls(el): return el.get('class') or []
def wv(el):
    m = re.search(r'--w:([0-9.]+)%', el.get('style') or ''); return float(m.group(1)) if m else None
def num(d):
    t = re.sub(r'<[^>]+>.*', '', d).replace(',', '')
    try: return float(t)
    except ValueError: return None

# ------------------------------------------------------------------ vendors
VENDORS = [
    # key, 显示名, 组, CSS 变量, 浅色, 深色, 图 3-x 图例提示, 表 2-2 单元格类
    ('google', 'Google', '前沿', '--g', '#2a78d6', '#3987e5', 'Google Gemini 4 系列。悬停只看这一家。', 'vg', True),
    ('anthropic', 'Anthropic', '前沿', '--a', '#eb6834', '#d95926', 'Anthropic Claude 系列。悬停只看这一家。', 'va', True),
    ('openai', 'OpenAI', '前沿', '--o', '#1baf7a', '#199e70', 'OpenAI GPT 系列。悬停只看这一家。', 'vo', True),
]

# ------------------------------------------------------------------ t21
t21h = seg('<div class="tblwrap wide" id="t21"', '</table></div>')
T = soup(t21h)
cols = [c['style'] for c in T.find_all('col')]
ths1 = T.find('thead').find_all('tr')[0].find_all('th')
ths2 = T.find('thead').find_all('tr')[1].find_all('th')
groups = []
for th in ths1[1:]:
    groups.append({'label': inner(th), 'tip': th.get('data-tip'), 'span': int(th['colspan'])})
GKEYS = ['basic', 'indep', 'general', 'cyber', 'life']
KEYS = ['release', 'price_in', 'price_out', 'aa', 'vals', 'tb4_vals', 'fc2', 'ale', 'tbsci', 'osw', 'chart', 'auto',
        'tb4_vendor', 'aeci', 'cve', 'cysb', 'binexp', 'exgym', 'exbench', 'binder', 'protdes', 'scb', 'protoc',
        'domain', 'mutattr', 'medchem', 'morph', 'bioimg', 'vct']
assert len(KEYS) == len(ths2), len(ths2)
gof = []
for gk, g in zip(GKEYS, groups): gof += [gk] * g['span']
basic, benches = {}, []
for k, th, gk in zip(KEYS, ths2, gof):
    tip = th.get('data-tip')
    if gk == 'basic':
        basic[k] = {'label': inner(th), 'tip': tip}
        continue
    m = re.match(r'^(.*) 有分数的模型：(\d+) 个。$', tip, re.S)
    benches.append({'key': k, 'label': inner(th), 'group': gk, 'desc': m.group(1), '_count': int(m.group(2))})
BK = [b['key'] for b in benches]

rows = T.find('tbody').find_all('tr', recursive=False)
models, order_vendor = [], []
vendor = None
for tr in rows:
    if 'grp' in cls(tr):
        vendor = tr.find('span', class_='sw')['class'][1][2:]; order_vendor.append(vendor); continue
    tds = tr.find_all('td', recursive=False)
    c0 = tds[0]
    tag = c0.find('span', class_='tag')
    name = ''.join(t for t in c0.find_all(string=True, recursive=False)).strip()
    m = {'id': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'), 'name': name, 'vendor': vendor}
    if tag:
        m['tag'] = {'text': tag.get_text(), 'tip': tag.get('data-tip')}
        m['status'] = 'internal' if tag.get_text() == '内部代号' else 'restricted'
    else:
        m['status'] = 'public'
    # release
    r = tds[1]
    if 'na' in cls(r):
        m['trained'] = {'label': r.get_text(), 'tip': r.get('data-tip')}
    else:
        disp = inner(r)
        m['release'] = '2026-' + re.match(r'\d\d-\d\d', disp).group(0)
        if '<sup>*</sup>' in disp: m['release_star'] = True
        if r.get('data-tip'): m['release_tip'] = r.get('data-tip')
        m['_release_w'] = wv(r)
    # price
    pi, po = tds[2], tds[3]
    if not ('na' in cls(pi)):
        def pp(td):
            d = inner(td); mm = re.match(r'\$([0-9.]+)(?:<small>→\$([0-9.]+)</small>)?$', d)
            return float(mm.group(1)), (float(mm.group(2)) if mm.group(2) else None), d
        a, an, ad = pp(pi); b, bn, bd = pp(po)
        price = {'in': a, 'out': b}
        if an is not None: price['in_next'] = an
        if bn is not None: price['out_next'] = bn
        assert pi.get('data-tip') == po.get('data-tip')
        if pi.get('data-tip'): price['tip'] = pi.get('data-tip')
        price['_disp'] = (ad, bd); price['_w'] = (wv(pi), wv(po)); price['_over'] = ('over' in cls(pi), 'over' in cls(po))
        m['price'] = price
    else:
        m['_price_na'] = (pi.get('data-tip'), po.get('data-tip'))
    m['scores'] = {}; m['blank'] = {}
    for k, td in zip(BK, tds[4:]):
        c = cls(td)
        if 'na' in c:
            if td.get('data-tip') or inner(td) != '—':
                m['blank'][k] = {'d': inner(td), 'tip': td.get('data-tip')}
            continue
        d = inner(td)
        rk = [int(x[1]) for x in c if re.fullmatch(r'r[123]', x)]
        m['scores'][k] = {'d': d, 'tip': td.get('data-tip'), '_rank': rk[0] if rk else None, '_w': wv(td)}
    if not m['blank']: del m['blank']
    models.append(m)

# per-bench name / unit from tip heads
for b in benches:
    names, units = {}, {}
    for m in models:
        c = m['scores'].get(b['key'])
        if not c: continue
        mm = re.match(r'^(.*?)：' + re.escape(c['d']) + r'([^。]*)。', c['tip'])
        assert mm, (b['key'], c['tip'])
        names[mm.group(1)] = names.get(mm.group(1), 0) + 1; units[mm.group(2)] = units.get(mm.group(2), 0) + 1
    assert len(names) == 1 and len(units) == 1, (b['key'], names, units)
    b['name'] = next(iter(names)); b['unit'] = next(iter(units))
B = {b['key']: b for b in benches}
for m in models:
    for k, c in m['scores'].items():
        head = '%s：%s%s。' % (B[k]['name'], c['d'], B[k]['unit'])
        t = c.pop('tip'); assert t.startswith(head), t
        rest = t[len(head):]
        if c['_rank']:
            rs = '本列第 %d 名。' % c['_rank']; assert rest.startswith(rs), (m['name'], k, rest); rest = rest[len(rs):]
        c['note'] = rest
        c['v'] = num(c['d'])

# ------------------------------------------------------------------ figures 3-x
def fig(fid):
    h = seg('<figure id="%s"' % fid, '</figure>'); return h, soup(h)
f31h, F31 = fig('f31'); f32h, F32 = fig('f32'); f33h, F33 = fig('f33')
byname = {m['name']: m for m in models}
# f31/f32: tips confirm notes; we also learn f32 per-task cost text; f33 gives short names + panel subtitles
def check_rows(F, key, label):
    out = []
    for row in F.find_all('div', class_='row'):
        if 'hd' in cls(row) or 'ax' in cls(row): continue
        nm = row.find('span', class_='nm').get_text()
        out.append((nm, row.get('data-tip'), row.find('span', class_='v').get_text(), row.find('span', class_='x').get_text() if row.find('span', class_='x') else None))
    return out
f31rows = check_rows(F31, 'aa', 'AA 指数'); f32rows = check_rows(F32, 'vals', 'Vals Index')
panels = []
short = {}
for p in F33.find_all('div', class_='panel'):
    pt = p.find('div', class_='pt'); sub = pt.find('span', class_='pn').get_text()
    title = ''.join(pt.find_all(string=True, recursive=False))
    prow = []
    for row in p.find_all('div', class_='row'):
        if 'ax' in cls(row): continue
        tip = row.get('data-tip'); full = tip.split('：', 1)[0]
        short[full] = row.find('span', class_='nm').get_text(); prow.append(full)
    kk = [b['key'] for b in benches if B[b['key']]['group'] == 'general' and title.startswith(B[b['key']]['name'].split('（')[0])]
    panels.append({'bench': kk[0], 'title': title, 'sub': sub})
for m in models:
    if m['name'] in short: m['short'] = short[m['name']]
    else: m['short'] = re.sub(r'^(Claude |Gemini 4 )', '', m['name'])

f31cap = F31.find('span', class_='hint')['data-tiph']; f32cap = F32.find('span', class_='hint')['data-tiph']; f33cap = F33.find('span', class_='hint')['data-tiph']
figures = {
    'f31': {'bench': 'aa', 'caption': F31.find('figcaption').contents[0].strip(), 'source_tip': f31cap.replace('2026-11-19', '{snapshot}'),
            'label': 'AA 指数', 'axis': {'min': 0, 'max': 70, 'step': 10}, 'head': ['模型', 'AA 指数（0–{max}）', '分', '输出价 / 百万 token'], 'mark': 'bar'},
    'f32': {'bench': 'vals', 'caption': F32.find('figcaption').contents[0].strip(), 'source_tip': f32cap,
            'label': 'Vals Index', 'axis': {'min': 50, 'max': 75, 'step': 5}, 'head': ['模型', 'Vals Index（横轴从 {min}% 起）', '%', '每题成本'], 'mark': 'dot'},
    'f33': {'caption': F33.find('figcaption').contents[0].strip(), 'source_tip': f33cap, 'axis': {'min': 0, 'max': 100, 'step': 25}, 'panels': panels},
}

# ------------------------------------------------------------------ t22
t22h = seg('<div class="tblwrap wide" id="t22"', '</table></div>')
T2 = soup(t22h)
h1 = T2.find('thead').find_all('tr')[0].find_all('th'); h2 = T2.find('thead').find_all('tr')[1].find_all('th')
gv = []
for th in h1[1:]:
    gv += [th.find('span', class_='sw')['class'][1][2:]] * int(th['colspan'])
t22cols = []
for th, v in zip(h2, gv):
    lab = inner(th)
    t22cols.append({'label': lab, 'vendor': v, 'tip': th.get('data-tip')})
t22 = {'c0': {'label': inner(h1[0]), 'tip': h1[0].get('data-tip')}, 'columns': t22cols, 'sections': []}
for tr in T2.find('tbody').find_all('tr', recursive=False):
    tds = tr.find_all('td', recursive=False)
    if 'grp' in cls(tr):
        t22['sections'].append({'label': tr.get_text(), 'rows': []}); continue
    name = inner(tds[0]); row = {'name': name, 'tip': tds[0].get('data-tip'), 'cells': []}
    units = set()
    for col, td in zip(t22cols, tds[1:]):
        c = cls(td)
        if 'na' in c:
            if td.get('data-tip') or inner(td) != '—':
                row['cells'].append({'blank': True, 'd': inner(td), 'tip': td.get('data-tip')})
            else: row['cells'].append(None)
            continue
        d = inner(td); dag = d.endswith('<sup>†</sup>'); d0 = d[:-len('<sup>†</sup>')] if dag else d
        tip = td.get('data-tip'); lab = re.sub(r'<br>.*', '', col['label'])
        mm = re.match(r'^' + re.escape(lab) + ' · ' + re.escape(name) + '：' + re.escape(d0) + r'([^。]*)。', tip)
        assert mm, (lab, name, tip)
        units.add(mm.group(1)); rest = tip[mm.end():]
        rk = [int(x[1]) for x in c if re.fullmatch(r'r[123]', x)]
        if rk:
            rs = '本行第 %d 名。' % rk[0]; assert rest.startswith(rs), rest; rest = rest[len(rs):]
        cell = {'d': d0, 'v': num(d0), 'note': rest, '_rank': rk[0] if rk else None, '_w': wv(td)}
        if dag: cell['dagger'] = True
        row['cells'].append(cell)
    assert len(units) <= 1, units
    row['unit'] = units.pop() if units else ''
    t22['sections'][-1]['rows'].append(row)

# ------------------------------------------------------------------ timeline (model lanes)
a = s.index('<!--compute:hltop:end-->') + len('<!--compute:hltop:end-->'); b = s.index('<!--compute:lanes:start-->')
TL = soup(s[a:b])
events, lanes = [], []
for lab in TL.find_all('div', class_='hl-lab'):
    trk = lab.find_next_sibling('div')
    lane = trk['data-lane']; lanes.append({'lane': lane, 'label_html': inner(lab), 'key': lab['data-key'], 'tip': lab['data-tip']})
    for p in trk.find_all('span', class_='pin'):
        pl = p.find('span', class_='pl'); st = p['style']
        left = float(re.search(r'left:([0-9.]+)%', st).group(1))
        e = {'lane': lane, 'tip': p['data-tip']}
        if 'rng' in cls(p):
            width = float(re.search(r'width:([0-9.]+)%', st).group(1))
            e['_left'] = left; e['_width'] = width; e['label'] = inner(pl); e['range'] = True
        else:
            if 'mu' in cls(p): e['hollow'] = True
            sm = pl.find('small').extract().get_text()
            lab_h = inner(pl); assert lab_h.startswith(' ')
            lab_h = lab_h[1:]
            tg = re.search(r'<span class="tag">([^<]*)</span>$', lab_h)
            if tg: e['tag'] = tg.group(1); lab_h = lab_h[:tg.start()]
            e['label'] = lab_h; e['_left'] = left; e['_md'] = sm
        events.append(e)
import datetime as dt
T0 = dt.date(2026, 6, 1); SPAN = 182
for e in events:
    if e.get('range'):
        d0 = T0 + dt.timedelta(days=round(e['_left'] / 100 * SPAN)); d1 = d0 + dt.timedelta(days=round(e['_width'] / 100 * SPAN))
        e['date'] = d0.isoformat(); e['end'] = d1.isoformat()
    else:
        d0 = T0 + dt.timedelta(days=round(e['_left'] / 100 * SPAN)); e['date'] = d0.isoformat()
        assert '%d/%d' % (d0.month, d0.day) == e['_md'], (e, d0)
        assert e['tip'].startswith(d0.isoformat() + '：'), e['tip']; e['tip'] = e['tip'][len(d0.isoformat()) + 1:]

# ------------------------------------------------------------------ hints
def hints_of(start):
    h = seg(start, '</div>'); return h
t21_hints = soup(hints_of('<div class="hints"><span class="hint" data-tiph="&lt;b&gt;怎么读这张表'))
t22_hints = soup(hints_of('<div class="hints"><span>19 项测试'))
def hl(S):
    out = []
    for sp in S.find('div').find_all('span', recursive=False):
        if 'hint' in cls(sp):
            out.append({'label': ''.join(sp.find_all(string=True, recursive=False)), 'tip': sp['data-tiph']})
        else:
            out.append({'text': inner(sp)})
    return out

data = {
    '_readme': '表 2-1 / 表 2-2 / 图 2-1（模型泳道）/ 图 3-1~3-3 / 顶栏快照与模型计数的唯一数据源。改完跑 build_tables.py。字段说明见 MAINTAIN.md。',
    'meta': {'snapshot': '2026-11-19', 'meta_prefix': 'Bench 得分 · 价格 · 发布时间'},
    'timeline': {'t0': '2026-06-01', 'span_days': 182},
    'layout': {},
    't21': {'groups': [dict(key=k, **g) for k, g in zip(GKEYS, groups)], 'basic': basic, 'hints': hl(t21_hints)},
    'benches': benches, 'models': models, 'timeline_events': events, '_lanes_seen': lanes,
    't22': t22, 't22_hints': hl(t22_hints), 'figures': figures,
    '_cols': cols, '_f31': f31rows, '_f32': f32rows,
}
os.makedirs(OUT, exist_ok=True)
json.dump(data, open(os.path.join(OUT, 'raw_extract.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('models', len(models), 'benches', len(benches), 'events', len(events), 't22 rows', sum(len(x['rows']) for x in t22['sections']))
