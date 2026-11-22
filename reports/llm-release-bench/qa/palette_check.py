#!/usr/bin/env python3
"""厂商配色报告（官方品牌色版，2026-11-22 第三版）：调用 Skill dataviz 自带的 validate_palette.py 计算色差（必须用它，不要目测）。
规则：「官方色优先，撞了取官方辅色，最后才派生」，候选色只来自 research/2026-11-22-brand-colors.json 里各家自己的官方色。
输出（深浅两种主题）：
  1 最终 8 色与每个颜色的出处类型（vendors.json 的 color_src / derived）
  2 8 家两两全部 28 对的正常视力 ΔE 与 CVD ΔE（min(protan, deutan)），按最差排序；正常 <12 或 CVD <6 的标「撞色」——
    这些对靠图里每行的「品牌色小方块 + 名字」区分（第 4 章图、散点标签、表 2-1 / 3-1、图例）
  3 与算力泳道三色（Nvidia 灰、TPU＝Google 蓝、其他品红）的正常视力 ΔE（不同图，同一页）
  4 dataviz 校验器原样输出（相邻对 / 全部对），仅供参考：官方色多为黑白蓝，门槛不再作为硬要求
用法：python3 qa/palette_check.py [validate_palette.py 所在目录]；结果写进 qa/palette_report.txt（要提交）。"""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATAVIZ_SCRIPTS', ''))
import validate_palette as V
VJ = json.load(open(os.path.join(HERE, '..', 'data', 'vendors.json'), encoding='utf-8'))
VEN = VJ['vendors']; REF = {r['key']: r for r in VJ['reference_colors']}; SURF = VJ['surfaces']
def cvd(a, b): return min(V.deltaE(a, b, 'protan'), V.deltaE(a, b, 'deutan'))
out = ['规则：官方色优先，撞了取官方辅色，最后才派生（research/2026-11-22-brand-colors.json）。撞色判定：正常视力 ΔE <12 或 CVD ΔE <6。', '']
out.append('1 最终 8 色')
out.append('   %-9s %-9s %-9s %s' % ('厂商', '浅色', '深色', '出处（浅 / 深）'))
for v in VEN:
    s = v.get('color_src', {})
    l, d = s.get('light', {}).get('zh', ''), s.get('dark', {}).get('zh', '')
    out.append('   %-9s %-9s %-9s %s%s' % (v['key'], v['light'], v['dark'], ('［派生］' if v.get('derived') else '［官方］'), l + ('' if d == l else ' ／ 深色：' + d)))
for mode in ('light', 'dark'):
    out.append(''); out.append('==== %s（底色 %s）' % (mode, SURF[mode]))
    rs = []
    for a, b in itertools.combinations(VEN, 2):
        n, c = V.deltaE(a[mode], b[mode]), cvd(a[mode], b[mode]); rs.append((min(n / 12, c / 6), a['key'], b['key'], n, c))
    rs.sort()
    bad = [r for r in rs if r[3] < 12 or r[4] < 6]
    out.append('2 8 家两两全部 %d 对；撞色 %d 对（靠「品牌色小方块 + 名字」区分）。最差 10 对：' % (len(rs), len(bad)))
    for _, ka, kb, n, c in rs[:10]:
        out.append('   %-9s ↔ %-9s 正常 %5.1f  CVD %5.1f  %s' % (ka, kb, n, c, '撞色' if (n < 12 or c < 6) else 'ok'))
    out.append('3 与算力泳道三色的正常视力 ΔE（低于 10 的列出）：')
    low = [(v['key'], k, V.deltaE(v[mode], REF[k][mode])) for v in VEN for k in ('nvidia', 'tpu', 'other') if not (v['key'] == 'google' and k == 'tpu')]
    low = [x for x in low if x[2] < 10]
    out.append('   ' + ('无' if not low else '；'.join('%s ↔ %s %.1f' % x for x in low)) + '（TPU 与 Google 同色是有意的：同一家）')
    out.append('4 dataviz 校验器（参考）：')
    for pairs in ('adjacent', 'all'):
        rep, ok = V.validate([v[mode] for v in VEN], mode, SURF[mode], pairs)
        for name, st, msg in rep: out.append('   [%s %s] %s：%s' % (pairs, st if isinstance(st, str) else ('pass' if st else 'FAIL'), name, msg))
txt = '\n'.join(out); print(txt)
open(os.path.join(HERE, 'palette_report.txt'), 'w', encoding='utf-8').write(txt + '\n')
