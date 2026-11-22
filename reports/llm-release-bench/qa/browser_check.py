#!/usr/bin/env python3
"""无头 Chromium 检查（playwright）：JS 报错、表 2-1 行列数、图 2-1 泳道、图 3-x 行数、吸顶表头克隆列数；并截图。
用法：python3 qa/browser_check.py 报告.html 截图目录 [chrome 路径]
VM 里没有浏览器时：把报告 stage 到容器里跑（容器有 playwright + google-chrome）。"""
import json, os, sys
from playwright.sync_api import sync_playwright
F, OUT = os.path.abspath(sys.argv[1]), sys.argv[2]; CH = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
JS = r'''() => {
 const q=(s)=>document.querySelectorAll(s), r={};
 r.t21_rows=q('#t21 tbody tr[class^="v-"]').length; r.t21_groups=[...q('#t21 tbody tr.grp')].map(e=>e.textContent);
 r.t21_cols=q('#t21 colgroup col').length; r.t21_th2=q('#t21 thead tr.h2 th').length;
 r.t21_r1=q('#t21 td.r1').length; r.t21_r2=q('#t21 td.r2').length; r.t21_r3=q('#t21 td.r3').length;
 r.t22_rows=q('#t22 tbody tr:not(.grp)').length;
 r.f21_lanes=[...q('#f21 .hl-track')].map(e=>e.getAttribute('data-lane'));
 r.f21_pins=q('#f21 .hl-track:not(.cmp) .pin').length;
 r.f31_rows=q('#f31 .row[data-key]').length; r.f32_rows=q('#f32 .row[data-key]').length; r.f33_rows=q('#f33 .row[data-key]').length;
 r.f31_legend=[...q('#f31 .legend .li')].map(e=>e.getAttribute('data-key'));
 const sw=document.querySelector('#t21 tr.v-xai .sw'); r.xai_swatch=sw?getComputedStyle(sw).backgroundColor:null;
 const tb=document.querySelector('#t21 table'); r.t21_overflow_x=tb? (tb.getBoundingClientRect().width) : null;
 r.page_overflow=document.documentElement.scrollWidth>document.documentElement.clientWidth+1;
 return r;}'''
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch(args=['--no-sandbox'])
    out = {}
    for theme in ('light', 'dark'):
        pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        pg.on('console', lambda m: errs.append('console.%s: %s' % (m.type, m.text)) if m.type in ('error', 'warning') else None)
        pg.goto('file://' + F); pg.wait_for_timeout(800)
        if theme == 'dark':
            pg.evaluate("document.documentElement.setAttribute('data-theme','dark')"); pg.wait_for_timeout(200)
        r = pg.evaluate(JS); r['errors'] = errs
        for sel, nm in (('#t21', 't21'), ('#f21', 'f21'), ('#f31', 'f31'), ('#f33', 'f33')):
            el = pg.query_selector(sel)
            if el: el.scroll_into_view_if_needed(); pg.wait_for_timeout(150); el.screenshot(path=os.path.join(OUT, '%s-%s.png' % (nm, theme)))
        # 吸顶表头：滚到表 2-1 中间，看克隆表头的列数
        pg.evaluate("(()=>{const t=document.querySelector('#t21');window.scrollTo(0,t.getBoundingClientRect().top+scrollY+300)})()"); pg.wait_for_timeout(400)
        r['sticky_clone'] = pg.evaluate("(()=>{const cs=[...document.querySelectorAll('.tblwrap.wide.sthead')];return cs.map(c=>({cols:c.querySelectorAll('col').length,th2:c.querySelectorAll('thead tr.h2 th').length,visible:getComputedStyle(c).visibility!=='hidden'&&getComputedStyle(c).display!=='none'}))})()")
        # 克隆表头与原表头逐列对齐（取第二行表头每个 th 的左缘差）
        r['sticky_align_maxdx'] = pg.evaluate("(()=>{const c=document.querySelector('.tblwrap.wide.sthead');const o=document.querySelectorAll('#t21 thead tr.h2 th');const k=c?c.querySelectorAll('thead tr.h2 th'):[];if(!k.length)return null;let m=0;o.forEach((t,i)=>{m=Math.max(m,Math.abs(t.getBoundingClientRect().width-k[i].getBoundingClientRect().width))});return m})()")
        pg.screenshot(path=os.path.join(OUT, 'sticky-%s.png' % theme))
        out[theme] = r; pg.close()
    b.close()
json.dump(out, open(os.path.join(OUT, 'browser.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
