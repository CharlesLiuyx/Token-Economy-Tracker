#!/usr/bin/env python3
"""加模型 / 加 Bench / 加厂商演练（不碰正式文件）：
复制 data/ 与报告到 qa/rehearsal/（不进 git），在副本里：
  1 加虚构 Bench 列「TestB」（表 2-1 的「通用能力」组）并给两个前沿模型打分；
  2 加虚构模型「TEST Model」（vendor=xai，大厂组 → 应进表 3-1、图 3-2、第 4 章，不进表 2-1、图 2-1）；
  3 加虚构新厂商「TestLab」（vendors.json 新条目，group=open，带颜色和泳道）和它的模型「TEST Open」。
重建两遍（第二遍必须 unchanged），再把结构断言写到 qa/rehearsal/result.json。浏览器检查另跑 qa/browser_check.py qa/rehearsal/after.html。
用法：python3 qa/rehearsal.py [正式报告路径]"""
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html')
OUT = os.path.join(HERE, 'rehearsal'); os.makedirs(OUT, exist_ok=True)
DD = os.path.join(OUT, 'data'); os.makedirs(DD, exist_ok=True)
for f in ('models.json', 'vendors.json'): shutil.copyfile(os.path.join(ROOT, 'data', f), os.path.join(DD, f))
before = os.path.join(OUT, 'before.html'); after = os.path.join(OUT, 'after.html')
shutil.copyfile(REPORT, before); shutil.copyfile(REPORT, after)
def L(s): return {'zh': s, 'en': s if not re.search(r'[一-鿿]', s) else 'Rehearsal data.'}   # 演练数据也中英都填（英文用占位句）
D = json.load(open(os.path.join(DD, 'models.json'), encoding='utf-8'))
V = json.load(open(os.path.join(DD, 'vendors.json'), encoding='utf-8'))
# 1) 新 Bench 列：放在「通用能力」组末尾
i = max(j for j, b in enumerate(D['benches']) if b['group'] == 'general')
D['benches'].insert(i + 1, {'key': 'testb', 'label': L('TestB'), 'name': L('TEST Bench 1.0'), 'unit': L('%'), 'group': 'general',
                            'direction': 'higher', 'bar': 'auto', 'desc': L('TEST Bench 1.0，单位 %。演练用的虚构测试列。分数来自各厂商自己的发布表。〔低〕')})
byname = {m['name']: m for m in D['models']}
byname['Claude Fable 5.2']['scores']['testb'] = {'d': '80.0', 'v': 80.0, 'note': L('演练数据。Anthropic 发布表。'), 'src': 'release_table', 'cf': '低'}
byname['GPT-6.2 Astra']['scores']['testb'] = {'d': '75.5', 'v': 75.5, 'note': L('演练数据。OpenAI 发布表。'), 'src': 'release_table', 'cf': '低'}
# 2) 大厂组的新模型
D['models'].append({'id': 'test-model', 'name': 'TEST Model', 'short': 'TEST Model', 'vendor': 'xai', 'status': 'public', 'open_weights': False,
    'release': '2026-11-21', 'price': {'in': 5, 'out': 25, 'tip': L('演练数据：API 标准价。')},
    'license': {'d': L('否'), 'tip': L('演练数据。')}, 'params': {'d': '1T / 50B', 'tip': L('演练数据。')}, 'row_tip': L('演练用虚构模型。'),
    'scores': {
        'aa': {'d': '72', 'v': 72, 'note': L('演练数据。推理强度 max。'), 'src': 'artificial_analysis', 'cf': '高'},
        'vals': {'d': '72.50', 'v': 72.5, 'note': L('演练数据。每题成本 $5.00。'), 'src': 'vals_ai', 'cf': '高'},
        'tb4_vals': {'d': '66.00', 'v': 66.0, 'note': L('演练数据。每题成本 $3.00。'), 'src': 'vals_ai', 'cf': '高'},
        'osw': {'d': '88.0', 'v': 88.0, 'note': L('演练数据。xAI 发布表。'), 'src': 'release_table', 'cf': '低'},
        'deepswe': {'d': '88.0', 'v': 88.0, 'note': L('演练数据。xAI 发布表。'), 'src': 'release_table', 'cf': '低'}}})
D['timeline_events'].append({'lane': 'xai', 'date': '2026-11-21', 'label': L('TEST Model'), 'tip': L('TEST Model（演练用虚构模型）。$5 / $25。')})
# 3) 新厂商（开源组）
V['vendors'].append({'key': 'testv', 'name': 'TestLab', 'product': 'Test', 'group': 'open', 'css_var': '--tv', 'light': '#6b8f00', 'dark': '#8fb31a',
                     'legend_tip': L('TestLab 演练用虚构厂商。悬停只看这一家。'), 't22_class': 'vt', 'builtin_css': False})
V['timeline_lanes'].append({'lane': 'testv', 'vendor': 'testv'})
D['models'].append({'id': 'test-open', 'name': 'TEST Open', 'short': 'TEST Open', 'vendor': 'testv', 'status': 'public', 'open_weights': True,
    'release': '2026-11-01', 'price': {'in': 0.2, 'out': 0.8, 'tip': L('演练数据。')},
    'license': {'d': L('MIT'), 'tip': L('演练数据。')}, 'params': {'d': '100B / 10B', 'tip': L('演练数据。')},
    'scores': {'aa': {'d': '30', 'v': 30, 'note': L('演练数据。'), 'src': 'artificial_analysis', 'cf': '高'},
               'tb4_vals': {'d': '20.00', 'v': 20.0, 'note': L('演练数据。每题成本 $0.50。'), 'src': 'vals_ai', 'cf': '高'}}})
D['timeline_events'].append({'lane': 'testv', 'date': '2026-11-01', 'label': L('TEST Open'), 'tip': L('TEST Open（演练用虚构模型）。')})
# 新模型必须填 open_weights（开源 / 闭源标签的唯一来源；内部代号模型不填）
missing_ow = [m['name'] for m in D['models'] if m['status'] != 'internal' and 'open_weights' not in m]
json.dump(D, open(os.path.join(DD, 'models.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(V, open(os.path.join(DD, 'vendors.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
py = sys.executable; comp = os.path.join(ROOT, 'compute', 'build.py')
last = {}
for rnd in (1, 2):
    for cmd in ([os.path.join(ROOT, 'build_tables.py'), after, '--data', DD, '--no-ch1-check'], [comp, after, '--data', DD]):
        log = subprocess.run([py] + cmd, capture_output=True, text=True)
        if log.returncode: print(log.stdout, log.stderr); sys.exit(1)
        if rnd == 1: print(log.stdout.strip())
        last[cmd[0]] = log.stdout.strip().splitlines()[-1]
idem = all('unchanged' in v for v in last.values())

def tbl(src, tid):
    a = src.index('<div class="tblwrap wide" id="%s"' % tid); b = src.index('</table></div>', a); return src[a:b]
def fig(src, fid):
    a = src.index('<figure id="%s"' % fid); b = src.index('</figure>', a); return src[a:b]
B, A = open(before, encoding='utf-8').read(), open(after, encoding='utf-8').read()
def rows(x): return len(re.findall(r'<tr class="v-', x))
def cols(x): return len(re.findall(r'<col ', x))
def cell(x, model, idx):
    tr = re.search(r'<tr class="v-[a-z]+"><td class="mn c0 noterm"[^>]*><span class="sw k-[a-z]+"></span>' + re.escape(model) + r'(?:<span|</td>).*?</tr>', x).group(0)
    return re.findall(r'<td[^>]*>.*?</td>', tr)[idx]
t21b, t21a, t31a = tbl(B, 't21'), tbl(A, 't21'), tbl(A, 't31')
res = {
    'idempotent': idem,
    't21_rows': [rows(t21b), rows(t21a)], 't21_cols': [cols(t21b), cols(t21a)],
    't21_has_xai_or_testv': ('k-xai' in t21a) or ('k-testv' in t21a),
    'testb_header': re.search(r'<th class="num"[^>]*>TestB</th>', t21a) is not None,
    'testb_cells': re.findall(r'<td class="num cb ?(r\d)?[^"]*" style="--w:([0-9.]+)%" data-tip="TEST Bench 1\.0：([0-9.]+)', t21a),
    't31_rows': [rows(tbl(B, 't31')), rows(t31a)], 't31_testv_group': '<span class="sw k-testv"></span>TestLab<small class="gk"' in t31a,
    't31_test_model_aa': cell(t31a, 'TEST Model', 6),
    'f21_lanes_same': re.findall(r'data-lane="([a-z]+)"', fig(B, 'f21')) == re.findall(r'data-lane="([a-z]+)"', fig(A, 'f21')),
    'f32_lanes': re.findall(r'<div class="hl-track" data-lane="([a-z]+)"', fig(A, 'f32')),
    'testv_css': '--tv:#6b8f00' in A and '.sc .spt[data-key=testv]' in A,
    'f41_legend_testv_in_open_group': re.search(r'<span class="lgg"><span class="lgn"[^>]*>(?:<span class="lz">开源</span>).*?data-key="testv"', fig(A, 'f41')) is not None,
    'f41_axis': re.search(r'AA 指数（0–(\d+)）', fig(A, 'f41')).group(1),
    'f44_points': [len(re.findall(r'class="spt', fig(B, 'f44'))), len(re.findall(r'class="spt', fig(A, 'f44')))],
    'meta': re.search(r'<p class="meta">.*?</p>', A).group(0),
    'missing_open_weights': missing_ow,
    'test_model_closed_tag': re.search(r'TEST Model<span class="tag ow-c"', t31a) is not None,
    'test_open_open_tag': re.search(r'TEST Open<span class="tag ow-o"', t31a) is not None,
}
ok = (idem and res['t21_rows'][1] == res['t21_rows'][0] and res['t21_cols'][1] == res['t21_cols'][0] + 1 and not res['t21_has_xai_or_testv'] and res['testb_header']
      and len(res['testb_cells']) == 2 and res['t31_rows'][1] == res['t31_rows'][0] + 2 and res['t31_testv_group'] and '>72<' in res['t31_test_model_aa']
      and res['f21_lanes_same'] and 'testv' in res['f32_lanes'] and res['testv_css'] and res['f41_legend_testv_in_open_group'] and res['f44_points'][1] == res['f44_points'][0] + 2
      and not missing_ow and res['test_model_closed_tag'] and res['test_open_open_tag'])
res['ok'] = ok
json.dump(res, open(os.path.join(OUT, 'result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
print('演练通过' if ok else '演练不通过')
sys.exit(0 if ok else 1)
