#!/usr/bin/env python3
# 留档：2026-11-22 从手写版报告反抽数据用的一次性脚本，依赖当时的 HTML 结构，以后不要再跑。
"""一次性：raw_extract.json → data/models.json + data/vendors.json（去掉诊断字段，补出处 / 可信度元数据）。"""
import json, re, sys, os
raw = json.load(open(sys.argv[1], encoding='utf-8')); OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

def src_kind(bench, note):
    if bench == 'aa': return 'artificial_analysis'
    if bench in ('vals', 'tb4_vals'): return 'vals_ai'
    if 'System Card' in note or '补充卡' in note: return 'system_card'
    if '模型卡' in note: return 'model_card'
    if '官方榜' in note: return 'leaderboard'
    if '发布表' in note: return 'release_table'
    if '自报' in note or '自测' in note: return 'vendor_self_report'
    return 'other'

GROUP_SHORT = {'basic': '基本', 'indep': '独立榜单', 'general': '通用能力', 'cyber': '网络安全', 'life': '生命科学'}
CF = {'indep': '高', 'general': '中', 'cyber': '中', 'life': '中'}
benches = []
for b in raw['benches']:
    nb = {'key': b['key'], 'label': b['label'], 'name': b['name'], 'unit': b['unit'], 'group': b['group'],
          'direction': 'higher', 'bar': 'auto', 'desc': b['desc']}
    benches.append(nb)
BG = {b['key']: b['group'] for b in benches}

models = []
END = {'Model 4': '2026-10-31', 'Model 3': '2026-09-30', 'Model 2': '2026-07-31'}
for m in raw['models']:
    o = {'id': m['id'], 'name': m['name'], 'short': m['short'], 'vendor': m['vendor'], 'status': m['status']}
    if 'tag' in m: o['tag'] = m['tag']
    if 'release' in m:
        o['release'] = m['release']
        if m.get('release_star'): o['release_star'] = True
        if 'release_tip' in m: o['release_tip'] = m['release_tip']
    if 'trained' in m:
        o['trained'] = dict(m['trained'], end=END[m['name']])
    if 'price' in m:
        p = {k: v for k, v in m['price'].items() if not k.startswith('_')}
        for k in ('in', 'out', 'in_next', 'out_next'):
            if k in p and p[k] == int(p[k]): p[k] = int(p[k])
        o['price'] = p
    sc = {}
    for k, c in m['scores'].items():
        v = c['v']
        if v is not None and v == int(v) and '.' not in c['d']: v = int(v)
        if k == 'vct':   # VCT 色条与名次按更精确的百分比算（note 里写的 61.80% / 55.34%）；显示仍是两位小数
            pm = re.findall(r'([0-9]+\.[0-9]+)%', c['note'])
            if pm: v = round(float(pm[-1]) / 100, 4)
        sc[k] = {'d': c['d'], 'v': v, 'note': c['note'], 'src': src_kind(k, c['note']), 'cf': CF[BG[k]]}
    o['scores'] = sc
    if m.get('blank'): o['blank'] = m['blank']
    models.append(o)

# t22
t22 = raw['t22']
cols = []
for c in t22['columns']:
    lab = c['label']; base = re.sub(r'<br>.*', '', lab)
    cid = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
    cols.append({'id': cid, 'label': lab, 'vendor': c['vendor'], 'tip': c['tip']})
secs = []
for s in t22['sections']:
    rows = []
    for r in s['rows']:
        cells = {}
        for col, c in zip(cols, r['cells']):
            if c is None: continue
            if c.get('blank'): cells[col['id']] = {'blank': True, 'd': c['d'], 'tip': c['tip']}; continue
            v = c['v']
            if r['name'].startswith('VCT'):
                pm = re.findall(r'([0-9]+\.[0-9]+)%', c['note'])
                if pm: v = round(float(pm[0]) / 100, 4)
            nc = {'d': c['d'], 'v': v, 'note': c['note']}
            if c.get('dagger'): nc['dagger'] = True
            cells[col['id']] = nc
        rows.append({'name': r['name'], 'tip': r['tip'], 'unit': r['unit'], 'cells': cells})
    secs.append({'label': s['label'], 'rows': rows})

# hints → templates
def tpl_t21(h):
    t = h.get('tip')
    if t:
        t = t.replace('分数 26 列，分四组：独立榜单、通用能力、网络安全、生命科学。', '分数 {n_bench} 列，分{n_groups_zh}组：{group_names}。')
        t = t.replace('（输入 $10，输出 $50）', '（输入 {price_in_max}，输出 {price_out_max}）')
        h = dict(h, tip=t)
    return h
def tpl_t22(h):
    if 'text' in h: return {'text': h['text'].replace('19 项测试 × 16 个对照模型', '{n_rows} 项测试 × {n_cmp} 个对照模型')}
    return dict(h, tip=h['tip'].replace('对照分数共 79 个', '对照分数共 {n_cmp_scores} 个'))
basic = raw['t21']['basic']
basic['price_in']['tip'] = basic['price_in']['tip'].replace('色条按 0 到 $10（', '色条按 0 到 {max}（')
basic['price_out']['tip'] = basic['price_out']['tip'].replace('色条按 0 到 $50（', '色条按 0 到 {max}（')

ev = []
for e in raw['timeline_events']:
    o = {'lane': e['lane'], 'date': e['date']}
    if e.get('range'): o['end'] = e['end']
    if e.get('hollow'): o['hollow'] = True
    o['label'] = e['label']
    if e.get('tag'): o['tag'] = e['tag']
    o['tip'] = e['tip']
    ev.append(o)

figs = raw['figures']
figs['f31']['toc'] = '图 3-1 AA 指数排名'; figs['f32']['toc'] = '图 3-2 Vals Index 排名'; figs['f33']['toc'] = '图 3-3 厂商自报的六项测试'

data = {
    '_readme': '表 2-1、表 2-2、图 2-1 模型泳道、图 3-1~3-3、顶栏快照与模型计数的唯一数据源。改完跑 build_tables.py。字段说明见 ../MAINTAIN.md。',
    'meta': {
        'snapshot': '2026-11-19',
        'title': '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM',
        'meta_prefix': 'Bench 得分 · 价格 · 发布时间',
        'appendix_hints': [{'label': '核对方式', 'tip': '<b>核对方式</b>快照日期 {snapshot}。<br>发布日和价格至少用两个来源核对过；受限模型除外。'}],
    },
    'timeline': {'t0': '2026-06-01', 'span_days': 182},
    'layout': {
        '_readme': '列宽（em）。原表由浏览器实测得出；新增列沿用同组宽度。build_tables.py 会估算新内容所需宽度，超出时打印警告，需人工调大这里的值。',
        't21': {'model': 14.419, 'release': 4.34106, 'price_in': 4.496, 'price_out': 5.891, 'bench': 5.27135},
        't22': {'test': 14.574, 'model': 4.34106},
    },
    't21': {
        'toc': '表 2-1 模型总表',
        'c0': {'label': '模型', 'tip': '厂商色块 + 模型名。「受限」＝只对通过审核的机构开放。'},
        'groups': [{'key': g['key'], 'label': g['label'], 'short': GROUP_SHORT[g['key']], 'tip': g['tip']} for g in raw['t21']['groups']],
        'basic': basic,
        'hints': [tpl_t21(h) for h in raw['t21']['hints']],
    },
    'benches': benches,
    'models': models,
    'timeline_events': ev,
    't22': {'toc': '表 2-2 Mythos 5.2 专项分数与对照模型', 'c0': t22['c0'], 'columns': cols, 'sections': secs,
            'hints': [tpl_t22(h) for h in raw['t22_hints']]},
    'figures': figs,
}
# ---------------------------------------------------------------- 双语结构：读者可见的文字字段一律 {"zh": …, "en": ""}
def L(x): return {'zh': x, 'en': ''} if isinstance(x, str) else x
def wrap_keys(o, keys):
    for k in keys:
        if k in o and isinstance(o[k], str): o[k] = L(o[k])
def wrap_hint(h): wrap_keys(h, ('label', 'tip', 'text'))
mt = data['meta']; wrap_keys(mt, ('title', 'meta_prefix')); [wrap_hint(h) for h in mt['appendix_hints']]
t1 = data['t21']; wrap_keys(t1, ('toc',)); wrap_keys(t1['c0'], ('label', 'tip'))
for g in t1['groups']: wrap_keys(g, ('label', 'short', 'tip'))
for v in t1['basic'].values(): wrap_keys(v, ('label', 'tip'))
for h in t1['hints']: wrap_hint(h)
for b in data['benches']: wrap_keys(b, ('label', 'name', 'unit', 'desc'))
for m in data['models']:
    if 'tag' in m: wrap_keys(m['tag'], ('text', 'tip'))
    wrap_keys(m, ('release_tip',))
    if 'trained' in m: wrap_keys(m['trained'], ('label', 'tip'))
    if 'price' in m: wrap_keys(m['price'], ('tip',))
    for c in m['scores'].values(): wrap_keys(c, ('note',))
    for c in m.get('blank', {}).values(): wrap_keys(c, ('d', 'tip'))
for e in data['timeline_events']: wrap_keys(e, ('label', 'tag', 'tip'))
t2 = data['t22']; wrap_keys(t2, ('toc',)); wrap_keys(t2['c0'], ('label', 'tip'))
for c in t2['columns']: wrap_keys(c, ('label', 'tip'))
for h in t2['hints']: wrap_hint(h)
for sct in t2['sections']:
    wrap_keys(sct, ('label',))
    for r in sct['rows']:
        wrap_keys(r, ('name', 'tip', 'unit'))
        for c in r['cells'].values(): wrap_keys(c, ('note', 'd', 'tip') if c.get('blank') else ('note',))
for fk, F in data['figures'].items():
    wrap_keys(F, ('caption', 'source_tip', 'label', 'toc'))
    if 'head' in F: F['head'] = [L(x) for x in F['head']]
    for p in F.get('panels', []): wrap_keys(p, ('title', 'sub'))
# 构建脚本里拼句用的固定字词也放进数据，方便以后只改输出层
data['ui'] = {k: L(v) for k, v in {
    'rank_col': '本列第 {n} 名。', 'rank_row': '本行第 {n} 名。', 'count_suffix': ' 有分数的模型：{n} 个。',
    'lane_tip': '悬停只看 {name}。', 'snapshot': '快照', 'published': '{n} 个已发布模型', 'internal_one': ' + {n} 个 {vendor} 内部代号模型',
    'internal_many': ' + {n} 个内部代号模型', 'source': '来源', 'api_price': ' API 价 输入 {pin} / 输出 {pout}。', 'cost_re': '每题成本 (\\$[0-9.,]+)',
    'month': '{m} 月', 'snap_tip': '本报告的快照日期。', 'snap_label': '{m}/{d} 快照',
    'restricted_tip': '只对通过审核的机构开放，普通开发者不能直接调用。', 'groups_zh_digits': '零一二三四五六七八九十'}.items()}
json.dump(data, open(os.path.join(OUT, 'models.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(models))
