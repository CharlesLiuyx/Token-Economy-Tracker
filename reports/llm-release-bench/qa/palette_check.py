#!/usr/bin/env python3
"""厂商配色校验：调用 Skill dataviz 自带的 validate_palette.py（必须用它，不要目测）。
三组检查 × 深浅两种主题：
  A. 厂商顺序相邻对（表 2-1 分组、图 3-x 图例的顺序）——dataviz 的标准相邻检查（亮度带 / 彩度 / CVD / 正常视力 / 对比度）
  B. 图 2-1 泳道顺序相邻对：厂商泳道 → Nvidia → TPU → Trainium+AMD（算力三色来自 compute，只算 CVD / 正常视力）
  C. 全部两两对（含算力三色）：列出每一对低于 CVD 8 或正常视力 15 的组合
  D. 8 家厂商两两全部（图 4-1、4-4 里 8 家同框，任意两家都可能挨着）：目标正常视力 ΔE ≥12、CVD ΔE ≥6，逐对列出最差的 8 对并给出判定
用法：python3 qa/palette_check.py [validate_palette.py 所在目录]  （VM 里没有 dataviz skill 时在容器里跑）"""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATAVIZ_SCRIPTS', ''))
import validate_palette as V
VJ = json.load(open(os.path.join(HERE, '..', 'data', 'vendors.json'), encoding='utf-8'))
VEN = VJ['vendors']; REF = {r['key']: r for r in VJ['reference_colors']}; SURF = VJ['surfaces']
def cvd(a, b): return min(V.deltaE(a, b, 'protan'), V.deltaE(a, b, 'deutan'))
out = []
for mode in ('light', 'dark'):
    out.append('==== %s（底色 %s）' % (mode, SURF[mode]))
    pal = [v[mode] for v in VEN]
    rep, ok = V.validate(pal, mode, SURF[mode], 'adjacent')
    out.append('A. 厂商顺序相邻对：' + ' → '.join('%s %s' % (v['key'], v[mode]) for v in VEN))
    for name, st, msg in rep: out.append('   [%s] %s：%s' % (st if isinstance(st, str) else ('pass' if st else 'FAIL'), name, msg))
    seq = [(v['key'], v[mode]) for v in VEN] + [(k, REF[k][mode]) for k in ('nvidia', 'tpu', 'other')]
    out.append('B. 图 2-1 泳道顺序相邻对：')
    for (ka, a), (kb, b) in zip(seq, seq[1:]):
        c, n = cvd(a, b), V.deltaE(a, b)
        out.append('   %-9s %s ↔ %-9s %s  CVD %.1f  正常 %.1f  %s' % (ka, a, kb, b, c, n, 'pass' if c >= 8 and n >= 15 else ('floor(需文字标签)' if c >= 6 and n >= 15 else 'FAIL')))
    allc = [(v['key'], v[mode]) for v in VEN] + [('nvidia', REF['nvidia'][mode]), ('other', REF['other'][mode])]
    bad = []
    for (ka, a), (kb, b) in itertools.combinations(allc, 2):
        c, n = cvd(a, b), V.deltaE(a, b)
        if c < 8 or n < 15: bad.append((min(c, n), ka, kb, c, n))
    out.append('C. 全部两两对（%d 色，%d 对）里低于门槛的：' % (len(allc), len(allc) * (len(allc) - 1) // 2))
    for _, ka, kb, c, n in sorted(bad):
        new = ka not in ('google', 'anthropic', 'openai', 'nvidia', 'other') or kb not in ('google', 'anthropic', 'openai', 'nvidia', 'other')
        out.append('   %-9s ↔ %-9s CVD %.1f  正常 %.1f  %s' % (ka, kb, c, n, '新厂商相关' if new else '原有配色之间'))
for mode in ('light', 'dark'):
    rs = []
    for a, b in itertools.combinations(VEN, 2):
        c, n = cvd(a[mode], b[mode]), V.deltaE(a[mode], b[mode]); rs.append((min(n / 12, c / 6), a['key'], b['key'], c, n))
    rs.sort(); bad = [r for r in rs if r[0] < 1]
    out.append('D. %s：8 家两两全部 %d 对，目标正常 ≥12、CVD ≥6：%s；最差 8 对：' % (mode, len(rs), '全部达标' if not bad else '%d 对不达标' % len(bad)))
    for _, ka, kb, c, n in rs[:8]: out.append('   %-9s ↔ %-9s CVD %.1f  正常 %.1f  %s' % (ka, kb, c, n, 'pass' if c >= 6 and n >= 12 else 'FAIL'))
    rep, ok = V.validate([v[mode] for v in VEN], mode, SURF[mode], 'all')
    for name, st, msg in rep: out.append('   [all-pairs %s] %s：%s' % (st if isinstance(st, str) else ('pass' if st else 'FAIL'), name, msg))
out.append('说明：dataviz 的 all-pairs 正常视力门槛是 15、彩度下限 0.10；本报告按主控裁定用 12 / 6 作为两两目标，xAI 的石墨灰故意低于彩度下限。')
txt = '\n'.join(out); print(txt)
open(os.path.join(HERE, 'palette_report.txt'), 'w', encoding='utf-8').write(txt + '\n')
