#!/usr/bin/env python3
"""无头 Chromium 检查（playwright）：3 种窗口宽 × 深浅主题 × 中英两种语言，每种都断言并截图。
断言：JS 报错、页面横向溢出、图内元素越出图框、宽表吸顶克隆与原表头逐列对齐（表 2-1 / 2-2 / 2-3）、
     时间轴（图 2-1）节点互不重叠且不越出泳道、图 3-4 散点标签互不重叠且不压别的点、不出绘图区、
     语言切换后 <html lang> 正确、表 2-1 行列数、图 3-x 行数、顶栏标签筛选（只开「开源」后表 2-1 / 图 2-1 / 图 3-1 只剩开源厂商，恢复后行数还原）。
截图：每种组合存 top（首屏，含顶栏、筛选器与语言按钮）、f21、t21（滚到表中间、表头吸顶）、f41、f44、f45、flt（只开「开源」时的表 2-1）。
用法：python3 qa/browser_check.py 报告.html 截图目录 [chrome 路径] [--widths 1440,1100,800]
VM 里没有浏览器时：把报告 stage 到容器里跑（容器有 playwright + google-chrome）。"""
import json, os, sys
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
WIDTHS = [1440, 1100, 800]
if '--widths' in args:
    i = args.index('--widths'); WIDTHS = [int(x) for x in args[i + 1].split(',')]; del args[i:i + 2]
F, OUT = os.path.abspath(args[0]), args[1]; CH = args[2] if len(args) > 2 else None
os.makedirs(OUT, exist_ok=True)
JS = r'''() => {
 const q=(s)=>document.querySelectorAll(s), r={}, R=[], tr=e=>e.getBoundingClientRect();
 r.lang=document.documentElement.lang; r.title=document.title.slice(0,40);
 r.t21_rows=q('#t21 tbody tr[class^="v-"]').length; r.t21_cols=q('#t21 colgroup col').length; r.t21_th2=q('#t21 thead tr.h2 th').length;
 r.t22_rows=q('#t22 tbody tr:not(.grp)').length;
 r.f21_lanes=[...q('#f21 .hl-track')].map(e=>e.getAttribute('data-lane'));
 r.f41_rows=q('#f41 .row[data-key]').length; r.f42_rows=q('#f42 .row[data-key]').length; r.f43_rows=q('#f43 .row[data-key]').length;
 r.f44_pts=q('#f44 .spt').length; r.f44_hidden=[...q('#f44 .spt .pl.hid')].map(e=>e.textContent); r.f45_rows=q('#f45 .row[data-key]').length;
 if(document.documentElement.scrollWidth>document.documentElement.clientWidth+1) R.push('页面横向溢出 '+document.documentElement.scrollWidth);
 q('figure').forEach(f=>{ if(f.scrollWidth>f.clientWidth+1) R.push(f.id+' 图内横向溢出'); });
 /* 图 2-1：节点不重叠、不越出泳道 */
 q('#f21 .hl-track').forEach((L,i)=>{const lr=tr(L),ps=[...L.querySelectorAll('.pin')].map(tr);
   ps.forEach((a,j)=>{ if(a.left<lr.left-2||a.right>lr.right+2) R.push('节点越出泳道 '+L.getAttribute('data-lane')+' #'+j);
     ps.slice(j+1).forEach((b,k)=>{ if(a.left<b.right-1&&b.left<a.right-1&&a.top<b.bottom-1&&b.top<a.bottom-1) R.push('节点重叠 '+L.getAttribute('data-lane')+' #'+j+'/'+(j+k+1)); });});});
 /* 图 4-4：可见标签互不重叠、不压别的点、不出绘图区；点不出绘图区 */
 const pl=document.querySelector('#f44 .sc-plot');
 if(pl){const pr=tr(pl),P=[...pl.querySelectorAll('.spt')],D=P.map(p=>tr(p.querySelector('.mark'))),Lb=P.map(p=>p.querySelector('.pl'));
   const ov=(a,b,m)=>a.left<b.right-m&&b.left<a.right-m&&a.top<b.bottom-m&&b.top<a.bottom-m;
   D.forEach((d,i)=>{ if(d.left<pr.left-6||d.right>pr.right+6||d.top<pr.top-6||d.bottom>pr.bottom+6) R.push('散点出绘图区 '+Lb[i].textContent); });
   Lb.forEach((l,i)=>{ if(l.classList.contains('hid'))return; const a=tr(l);
     if(a.left<pr.left||a.right>pr.right||a.top<pr.top||a.bottom>pr.bottom) R.push('散点标签出绘图区 '+l.textContent);
     D.forEach((d,j)=>{ if(j!==i&&ov(a,d,0.5)) R.push('散点标签压到别的点 '+l.textContent+' / '+Lb[j].textContent); });
     Lb.forEach((m,j)=>{ if(j>i&&!m.classList.contains('hid')&&ov(a,tr(m),0.5)) R.push('散点标签重叠 '+l.textContent+' / '+m.textContent); }); });}
 /* 第 3 章（section#s4）：模型名不截断（允许折行） */
 q('#s4 .row .nm').forEach(e=>{ if(e.scrollWidth>e.clientWidth+1) R.push('图 3-x 模型名被截断 '+e.textContent); });
 /* 目录、提示框里的语言 */
 const en=document.documentElement.getAttribute('data-lang')==='en';
 if((document.documentElement.lang==='en')!==en) R.push('<html lang> 与 data-lang 不一致');
 r.errors_layout=R; return r;}'''
ALIGN = r'''(id)=>{const t=document.getElementById(id);window.scrollTo(0,t.getBoundingClientRect().top+scrollY+Math.min(300,t.offsetHeight/2));
  return new Promise(res=>requestAnimationFrame(()=>requestAnimationFrame(()=>{
   const c=[...document.querySelectorAll('.sthead')].find(x=>getComputedStyle(x).visibility==='visible');
   if(!c)return res({visible:false});
   const o=[...t.querySelectorAll('thead th')], k=[...c.querySelectorAll('thead th')];
   let m=0;o.forEach((th,i)=>{if(!k[i])return;const a=th.getBoundingClientRect(),b=k[i].getBoundingClientRect();m=Math.max(m,Math.abs(a.left-b.left),Math.abs(a.width-b.width))});
   res({visible:true,maxdx:Math.round(m*10)/10,top:Math.round(c.getBoundingClientRect().top),bar:Math.round(document.getElementById('topbar').getBoundingClientRect().bottom)})})))}'''
VJ = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'vendors.json'), encoding='utf-8'))
OPEN = {v['key'] for v in VJ['vendors'] if 'open' in v.get('tags', [v['group']])}
FLT = r'''() => {const vis=e=>e.getClientRects().length>0,q=s=>[...document.querySelectorAll(s)].filter(vis);
 const R=[];if(document.documentElement.scrollWidth>document.documentElement.clientWidth+1)R.push('筛选后页面横向溢出');
 return {off:document.documentElement.getAttribute('data-off'),
  t21:[...new Set(q('#t21 tr[class^="v-"]').map(e=>e.className.slice(2)))], nrows:q('#t21 tr[class^="v-"]').length,
  lanes:[...new Set(q('#f21 .hl-lab[data-tags]').map(e=>e.getAttribute('data-key')))],
  f41:[...new Set(q('#f41 .row[data-key]').map(e=>e.getAttribute('data-key')))], err:R};}'''
out = {}; bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch(args=['--no-sandbox'])
    for W in WIDTHS:
        for theme in ('light', 'dark'):
            for lang in ('zh', 'en'):
                tag = '%s-%s-%d' % (lang, theme, W)
                pg = b.new_page(viewport={'width': W, 'height': 900}); errs = []
                pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
                pg.on('console', lambda m: errs.append('console.%s: %s' % (m.type, m.text)) if m.type in ('error', 'warning') else None)
                pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-theme','%s');localStorage.setItem('mdl-lang','%s')}catch(e){}" % (theme, lang))
                pg.goto('file://' + F); pg.wait_for_timeout(700)
                r = pg.evaluate(JS); r['errors'] = errs
                pg.screenshot(path=os.path.join(OUT, '%s-top.png' % tag))
                for sel in ('#f21', '#f41', '#f44', '#f45'):
                    el = pg.query_selector(sel); el.scroll_into_view_if_needed(); pg.wait_for_timeout(80)
                    el.screenshot(path=os.path.join(OUT, '%s-%s.png' % (tag, sel[1:])))
                r['sticky'] = {t: pg.evaluate(ALIGN, t) for t in ('t21', 't22', 't23')}
                pg.evaluate(ALIGN, 't21'); pg.wait_for_timeout(80)
                pg.screenshot(path=os.path.join(OUT, '%s-t21.png' % tag))
                # 顶栏标签筛选：Shift 点「开源」＝只看开源；表 2-1、图 2-1 模型泳道、图 3-1 只剩开源厂商；再点「前沿」「大厂」恢复
                pg.click('#flt [data-flt=open]', modifiers=['Shift']); pg.wait_for_timeout(150)
                r['flt'] = pg.evaluate(FLT)
                pg.evaluate(ALIGN, 't21'); pg.wait_for_timeout(80)
                pg.screenshot(path=os.path.join(OUT, '%s-flt.png' % tag))
                pg.click('#flt [data-flt=frontier]'); pg.click('#flt [data-flt=bigtech]'); pg.wait_for_timeout(150)
                r['flt_back'] = pg.evaluate(FLT)
                # 语言按钮：切到另一种语言再切回，<html lang> 跟着变、无报错
                other = 'en' if lang == 'zh' else 'zh'
                pg.click('#lang [data-set="lang:%s"]' % other); pg.wait_for_timeout(120)
                r['switch'] = pg.evaluate("[document.documentElement.lang,document.documentElement.getAttribute('data-lang'),localStorage.getItem('mdl-lang')]")
                pg.click('#lang [data-set="lang:%s"]' % lang); pg.wait_for_timeout(120)
                r['switch_back'] = pg.evaluate("document.documentElement.getAttribute('data-lang')")
                st_bad = [t for t, v in r['sticky'].items() if not v.get('visible') or v['maxdx'] > 0.5 or abs(v['top'] - v['bar']) > 1]
                fl, fb = r['flt'], r['flt_back']
                flt_bad = (fl['off'] != 'frontier bigtech' or set(fl['t21']) != OPEN or set(fl['lanes']) - OPEN or set(fl['f41']) != OPEN
                           or fb['off'] is not None or fb['nrows'] != r['t21_rows'] or fb['err'] or fl['err'])
                ok = not (r['errors'] or r['errors_layout'] or st_bad or flt_bad or r['switch'][1] != other or r['switch_back'] != lang)
                bad += not ok
                print(tag, 'OK' if ok else 'FAIL', r['lang'], 'rows=%d cols=%d f44=%d 隐藏标签=%s 筛选=%s' % (r['t21_rows'], r['t21_cols'], r['f44_pts'], r['f44_hidden'], 'FAIL' if flt_bad else 'ok'), r['errors_layout'][:3], errs[:2], 'sticky:', {t: (v.get('maxdx'), v.get('top'), v.get('bar')) for t, v in r['sticky'].items()}, r['switch'])
                out[tag] = r; pg.close()
    b.close()
json.dump(out, open(os.path.join(OUT, 'browser.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('全部通过' if not bad else '%d 种组合不通过' % bad)
sys.exit(1 if bad else 0)
