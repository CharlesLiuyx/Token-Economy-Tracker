#!/usr/bin/env python3
"""加模型 / 加 Bench 演练（不碰正式文件）：
复制 data/ 与报告到 qa/rehearsal/（不进 git），往副本 JSON 里加虚构模型「TEST Model」（vendor=xai）和虚构 Bench 列「TestB」，
重建，再把结构断言写到 qa/rehearsal/result.json。浏览器检查另跑 qa/browser_check.py。
用法：python3 qa/rehearsal.py [正式报告路径]"""
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html')
OUT = os.path.join(HERE, 'rehearsal'); os.makedirs(OUT, exist_ok=True)
DD = os.path.join(OUT, 'data'); os.makedirs(DD, exist_ok=True)
for f in ('models.json', 'vendors.json'): shutil.copyfile(os.path.join(ROOT, 'data', f), os.path.join(DD, f))
before = os.path.join(OUT, 'before.html'); after = os.path.join(OUT, 'after.html')
shutil.copyfile(REPORT, before); shutil.copyfile(REPORT, after)
def L(s): return {'zh': s, 'en': s if not re.search(r'[\u4e00-\u9fff]', s) else 'Rehearsal data.'}   # 演练数据也中英都填（英文用占位句）
D = json.load(open(os.path.join(DD, 'models.json'), encoding='utf-8'))
# 1) 新 Bench 列：放在「通用能力」组末尾
i = max(j for j, b in enumerate(D['benches']) if b['group'] == 'general')
D['benches'].insert(i + 1, {'key': 'testb', 'label': L('TestB'), 'name': L('TEST Bench 1.0'), 'unit': L('%'), 'group': 'general',
                            'direction': 'higher', 'bar': 'auto', 'desc': L('TEST Bench 1.0，单位 %。演练用的虚构测试列。分数来自各厂商自己的发布表。〔低〕')})
byname = {m['name']: m for m in D['models']}
byname['Claude Fable 5.2']['scores']['testb'] = {'d': '80.0', 'v': 80.0, 'note': L('演练数据。Anthropic 发布表。'), 'src': 'release_table', 'cf': '低'}
byname['GPT-6.2 Astra']['scores']['testb'] = {'d': '75.5', 'v': 75.5, 'note': L('演练数据。OpenAI 发布表。'), 'src': 'release_table', 'cf': '低'}
# 2) 新模型：xAI 第一次出现
D['models'].append({'id': 'test-model', 'name': 'TEST Model', 'short': 'TEST Model', 'vendor': 'xai', 'status': 'public',
    'release': '2026-11-21', 'price': {'in': 5, 'out': 25, 'tip': L('演练数据：API 标准价。')},
    'scores': {
        'aa': {'d': '72', 'v': 72, 'note': L('演练数据。推理强度 max。'), 'src': 'artificial_analysis', 'cf': '高'},
        'vals': {'d': '72.50', 'v': 72.5, 'note': L('演练数据。每题成本 $5.00。'), 'src': 'vals_ai', 'cf': '高'},
        'tb4_vals': {'d': '66.00', 'v': 66.0, 'note': L('演练数据。每题成本 $3.00。'), 'src': 'vals_ai', 'cf': '高'},
        'osw': {'d': '88.0', 'v': 88.0, 'note': L('演练数据。xAI 发布表。'), 'src': 'release_table', 'cf': '低'},
        'testb': {'d': '88.0', 'v': 88.0, 'note': L('演练数据。xAI 发布表。'), 'src': 'release_table', 'cf': '低'}}})
D['timeline_events'].append({'lane': 'xai', 'date': '2026-11-21', 'label': L('TEST Model'), 'tip': L('TEST Model（演练用虚构模型）。$5 / $25。')})
json.dump(D, open(os.path.join(DD, 'models.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
py = sys.executable
log = subprocess.run([py, os.path.join(ROOT, 'build_tables.py'), after, '--data', DD], capture_output=True, text=True)
print(log.stdout, log.stderr)
comp = os.path.join(ROOT, 'compute', 'build.py')
if os.path.exists(comp):
    log2 = subprocess.run([py, comp, after, '--data', DD], capture_output=True, text=True); print(log2.stdout, log2.stderr)

def t21(src):
    a = src.index('<div class="tblwrap wide" id="t21"'); b = src.index('</table></div>', a); return src[a:b]
b0, a0 = t21(open(before, encoding='utf-8').read()), t21(open(after, encoding='utf-8').read())
A = open(after, encoding='utf-8').read()
def rows(x): return len(re.findall(r'<tr class="v-', x))
def cols(x): return len(re.findall(r'<col ', x))
def cell(x, model, idx):
    tr = re.search(r'<tr class="v-[a-z]+"><td class="mn c0 noterm"><span class="sw k-[a-z]+"></span>' + re.escape(model) + r'(?:<span|</td>).*?</tr>', x).group(0)
    return re.findall(r'<td[^>]*>.*?</td>', tr)[idx]
res = {
    'rows_before': rows(b0), 'rows_after': rows(a0), 'cols_before': cols(b0), 'cols_after': cols(a0),
    'xai_group_row': '<span class="sw k-xai"></span>xAI</span></td></tr>' in a0,
    'aa_test': cell(a0, 'TEST Model', 4), 'aa_fable52': cell(a0, 'Claude Fable 5.2', 4), 'aa_astra': cell(a0, 'GPT-6.2 Astra', 4),
    'testb_header': re.search(r'<th class="num"[^>]*>TestB</th>', a0) is not None,
    'testb_cells': re.findall(r'<td class="num cb ?(r\d)?[^"]*" style="--w:([0-9.]+)%" data-tip="TEST Bench 1\.0：([0-9.]+)', a0),
    'xai_lane': 'data-lane="xai"' in A, 'xai_css': '<style id="data-css">' in A and '--xa:' in A,
    'f31_legend_xai': re.search(r'<figure id="f31".*?<span class="li" data-key="xai"', A, re.S) is not None,
    'f31_axis': re.search(r'<figure id="f31".*?AA 指数（0–(\d+)）', A, re.S).group(1),
    'meta': re.search(r'<p class="meta">.*?</p>', A).group(0),
}
json.dump(res, open(os.path.join(OUT, 'result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
