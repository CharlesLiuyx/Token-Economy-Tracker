#!/usr/bin/env python3
"""换快照日演练（不碰正式文件）：把整个工程复制到临时目录，改副本 data/models.json 的 meta.snapshot，
跑两个构建脚本两遍（第二遍必须 unchanged），再用无头 Chromium 检查图 2-1 并截图。
检查：横轴第一个刻度＝快照月往前 5 个月、最后一根算力柱＝快照月；节点、柱子不越出泳道，节点互不重叠；快照竖线在快照日；底部快照标签不压月份；无 JS 报错。
用法：python3 qa/rehearse_snapshot.py 2026-12-05 截图目录 [chrome 路径]"""
import json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from bilingual import axis, MONTH_EN
SNAP, OUT = sys.argv[1], os.path.abspath(sys.argv[2]); CH = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
tmp = tempfile.mkdtemp(prefix='rehearse-')
shutil.copytree(ROOT, os.path.join(tmp, 'r'), ignore=shutil.ignore_patterns('*.png', 'qa', '__pycache__', '.git'))
W = os.path.join(tmp, 'r'); R = os.path.join(W, REPORT_NAME)
D = json.load(open(os.path.join(W, 'data', 'models.json'), encoding='utf-8')); D['meta']['snapshot'] = SNAP
json.dump(D, open(os.path.join(W, 'data', 'models.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
py = sys.executable
for rnd in (1, 2):
    for cmd in (['build_tables.py'], ['compute/build.py']):
        r = subprocess.run([py, os.path.join(W, *cmd[0].split('/'))], capture_output=True, text=True)
        if r.returncode: print(r.stdout, r.stderr); sys.exit(1)
        last = r.stdout.strip().splitlines()[-1]
        if rnd == 1: print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('提示：')))
        if rnd == 2 and 'unchanged' not in last: print('不幂等：', cmd, last); sys.exit(1)
t0, span, months = axis(SNAP)
print('快照 %s → 横轴 %s 起 %d 天，月份 %s' % (SNAP, t0, span, ', '.join(MONTH_EN[m.month - 1] for m in months)))
from playwright.sync_api import sync_playwright
LAYOUT = r'''() => {
 const R=[],tr=e=>e.getBoundingClientRect();
 document.querySelectorAll('#f21 .hl-track').forEach((L,i)=>{const lr=tr(L),ps=[...L.querySelectorAll('.pin')].map(tr);
   ps.forEach((a,j)=>{ if(a.left<lr.left-2||a.right>lr.right+2) R.push('节点越界 '+L.getAttribute('data-lane')+' #'+j);
     ps.slice(j+1).forEach((b,k)=>{ if(a.left<b.right-1&&b.left<a.right-1&&a.top<b.bottom-1&&b.top<a.bottom-1) R.push('节点重叠 '+L.getAttribute('data-lane')); });});
   L.querySelectorAll('.mb').forEach((m,k)=>{const r=tr(m); if(r.left<lr.left-1||r.right>lr.right+1) R.push('柱越界 '+L.getAttribute('data-lane')+' '+k);});});
 const f=document.getElementById('f21'); if(f.scrollWidth>f.clientWidth+1) R.push('图 2-1 横向溢出');
 const vm=document.querySelector('#f21 .hl-axis:not(.top) .mt.vm'),rg=document.createRange(),tb=e=>{rg.selectNodeContents(e);return rg.getBoundingClientRect()};
 if(vm){const a=tb(vm.previousElementSibling),b=tb(vm),c=vm.parentNode.getBoundingClientRect(); if(b.left<a.right+1||b.right>c.right+1) R.push('底部快照标签与月份重叠或越界');}
 const ticks=[...document.querySelectorAll('#f21 .hl-axis.top .mt')].map(e=>e.innerText.trim());
 const bars=[...document.querySelectorAll('#f21 .hl-track[data-lane=cmp-nvidia] .mb .tot')].map(e=>e.getAttribute('data-tiph-en')||'');
 const vl=document.querySelector('#f21 .hl-track.cmp .vl').style.left;
 return {errors:R,ticks:ticks,lastBar:bars.length?bars[bars.length-1].match(/arrivals, ([A-Z][a-z]{2} \d{4})/)[1]:'',nbars:bars.length,vl:vl};}'''
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch(args=['--no-sandbox'])
    for lang in ('zh', 'en'):
        for w in (1440, 800):
            pg = b.new_page(viewport={'width': w, 'height': 900}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-lang','%s')}catch(e){}" % lang)
            pg.goto('file://' + R); pg.wait_for_timeout(700)
            r = pg.evaluate(LAYOUT)
            exp_first = MONTH_EN[months[0].month - 1]; exp_last = '%s %d' % (MONTH_EN[months[-1].month - 1], months[-1].year)
            exp_vl = '%.3f%%' % ((__import__('datetime').date.fromisoformat(SNAP) - t0).days / span * 100)
            first_ok = (r['ticks'][0] == ('%d 月' % months[0].month if lang == 'zh' else exp_first))
            ok = not errs and not r['errors'] and first_ok and r['lastBar'] == exp_last and r['nbars'] == 6 and abs(float(r['vl'].rstrip('%')) - float(exp_vl.rstrip('%'))) < 0.001
            bad += not ok
            print('%s %d %s 刻度=%s 最后一根柱=%s 竖线=%s %s %s' % (lang, w, 'OK' if ok else 'FAIL', r['ticks'], r['lastBar'], r['vl'], r['errors'][:3], errs[:2]))
            el = pg.query_selector('#f21'); el.scroll_into_view_if_needed(); pg.wait_for_timeout(80)
            el.screenshot(path=os.path.join(OUT, 'snapshot-%s-%s-%d-f21.png' % (SNAP, lang, w)))
            pg.close()
    b.close()
shutil.rmtree(tmp)
print('演练通过（正式文件未改动）' if not bad else '演练有 %d 项不通过' % bad)
sys.exit(1 if bad else 0)
