#!/usr/bin/env python3
"""浏览器自检（无头 Chromium + playwright）：3 种窗口宽 × 3 档字号 × 深浅主题截图，并断言布局、磁吸、切换与数值。
用法：python3 qa_browser.py 报告.html 截图目录 [chrome 路径] [--lang zh|en] [--data 数据目录]
横轴月份与快照日从 data/models.json 推导（与构建脚本同一个函数）；--lang en 时按英文写法核对柱顶数字。"""
import sys, json, os, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from bilingual import axis
args = sys.argv[1:]
LANG = 'zh'
if '--lang' in args:
    i = args.index('--lang'); LANG = args[i + 1]; del args[i:i + 2]
DATA = os.path.join(os.path.dirname(HERE), 'data')
if '--data' in args:
    i = args.index('--data'); DATA = args[i + 1]; del args[i:i + 2]
F, OUT = os.path.abspath(args[0]), args[1]
CHROME = args[2] if len(args) > 2 else None
M = json.load(open(os.path.join(HERE, 'model.json'), encoding='utf-8'))
SNAP = json.load(open(os.path.join(DATA, 'models.json'), encoding='utf-8'))['meta']['snapshot']
os.makedirs(OUT, exist_ok=True)
WIN = ['%d-%02d' % (d.year, d.month) for d in axis(SNAP)[2]]
def jround(x): return int(math.floor(x + 0.5))        # 与 JS 的 Math.round 一致
def exp_full(v):                                       # 图 2-1 柱顶（不含单位）
    if LANG == 'zh':
        w = v / 1e4; return ('%d' % jround(w)) if w >= 100 else ('%.1f' % w)
    if v >= 999500 or jround(v / 1e3) >= 1000:
        m = v / 1e6; return ('%.1fM' % m) if m >= 10 else ('%.2fM' % m)
    return ('%dK' % jround(v / 1e3)) if v >= 1e3 else str(jround(v))
def exp_axis(v):                                       # 图 2-2 柱顶（单位在轴上）
    if LANG == 'zh':
        w = v / 1e4; return ('%d' % jround(w)) if w >= 100 else ('%.1f' % w)
    m = v / 1e6; return ('%.1f' % m) if m >= 10 else ('%.2f' % m)
MON = {r['month']: r for r in M['arrive_monthly']}
LAYOUT_JS = r'''() => {
 const R=[],tr=(e)=>e.getBoundingClientRect(),fig=document.querySelector('#f21');
 const out=(a,b,t=1)=>a.left<b.left-t||a.right>b.right+t;
 document.querySelectorAll('#f21 .hl-track').forEach((L,i)=>{
   const lr=tr(L),ps=[...L.querySelectorAll('.pin')].map(p=>tr(p));
   ps.forEach((a,j)=>{ if(out(a,lr,2)) R.push('pin 越界 lane'+i+' #'+j);
     ps.slice(j+1).forEach((b,k)=>{ if(a.left<b.right-1&&b.left<a.right-1&&a.top<b.bottom-1&&b.top<a.bottom-1) R.push('pin 重叠 lane'+i+' #'+j+'/'+(j+k+1)); });
     if(a.bottom>lr.bottom+1) R.push('pin 超出泳道底 lane'+i);});
   const cb=L.querySelector('.cbars');
   if(cb){ const cr=tr(cb); if(cr.bottom>lr.bottom+1||cr.top<lr.top-1) R.push('柱区越界 lane'+i);
     ps.forEach((a,j)=>{ if(a.bottom>cr.top+1) R.push('节点压到柱区 lane'+i+' #'+j); });
     L.querySelectorAll('.mb').forEach((m,k)=>{const r=tr(m); if(out(r,lr,1)) R.push('柱越界 lane'+i+' m'+k);});
     L.querySelectorAll('.tot').forEach((t,k)=>{const r=tr(t); if(r.top<cr.top-1) R.push('柱顶数字越出柱区 lane'+i+' m'+k);}); }
 });
 for(const id of ['f21','f22','f23']){const f=document.getElementById(id); if(f.scrollWidth>f.clientWidth+1) R.push(id+' 横向溢出 '+f.scrollWidth+'>'+f.clientWidth);
   const fr=tr(f); f.querySelectorAll('.tot,.qx,.cv,.cbar,.qb').forEach(e=>{const r=tr(e); if(r.right>fr.right+1||r.left<fr.left-1) R.push(id+' 元素越出图框 '+e.className);});}
 /* fig 2-2: bar-top labels must not collide within a group */
 document.querySelectorAll('#f22 .qg').forEach((g,gi)=>{const ts=[...g.querySelectorAll('.tot')].map(tr); for(let i=0;i+1<ts.length;i++){ if(ts[i].right>ts[i+1].left+1 && Math.abs(ts[i].top-ts[i+1].top)<12) R.push('f22 柱顶数字重叠 g'+gi+' '+i);} });
 if(document.documentElement.scrollWidth>document.documentElement.clientWidth+1) R.push('页面横向溢出');
 /* fig 2-2 lane names: text boxes must not overlap each other */
 const tb=e=>{const r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect()};
 const qs=[...document.querySelectorAll('#f22 .qln i')].map(tb);
 for(let i=0;i+1<qs.length;i++){const a=qs[i],b=qs[i+1]; if(a.right>b.left+0.5&&a.bottom>b.top+0.5&&b.bottom>a.top+0.5) R.push('f22 柱下名称重叠 '+i);}
 /* fig 2-1 bottom axis: snapshot label vs 11 月 */
 const vm=document.querySelector('#f21 .hl-axis:not(.top) .mt.vm'); if(vm){const a=tb(vm.previousElementSibling),b=tb(vm),c=vm.parentNode.getBoundingClientRect(); if(b.left<a.right+1||b.right>c.right+1) R.push('快照标签与 11 月重叠或越界');}
 /* fig 2-3: names not truncated, height */
 document.querySelectorAll('#f23 .cn').forEach(e=>{ if(e.scrollWidth>e.clientWidth+1) R.push('f23 型号名被截断 '+e.textContent);});
 window.__f23h=document.getElementById('f23').getBoundingClientRect().height;
 return R;}'''
def run_layout(pg): return pg.evaluate(LAYOUT_JS)

def values_check(pg, mode):
    got = pg.evaluate('''(m)=>{const r={};document.querySelectorAll('#f21 .hl-track.cmp').forEach(L=>{const ln=L.getAttribute('data-lane').slice(4);const i={h8:0,h4:1,units:2}[m];
       r[ln]=[...L.querySelectorAll('.mb')].map(mb=>{let s=0;mb.querySelectorAll('.sg').forEach(g=>s+=+g.getAttribute('data-cv').split(',')[i]);
         const tot=mb.querySelector('.tot').textContent; return [s,tot,mb.querySelector('.sg:last-of-type')?parseFloat(mb.querySelector('.tot').style.bottom):0];});});
       r.btn=[...document.querySelectorAll('#f21 [data-cmode].on,#f22 [data-cmode].on')].map(b=>b.getAttribute('data-cmode'));
       r.f22=[...document.querySelectorAll('#f22 .tot')].slice(0,3).map(t=>t.textContent);r.unit=document.querySelector('#f22 .qc-unit').textContent;
       r.small=document.querySelector('#f21 [data-cmsum]').textContent;return r}''', mode)
    bad = []
    for ln in ('nvidia', 'tpu', 'other'):
        for j, m in enumerate(WIN):
            exp = MON[m]['lanes'][ln]['total'][mode]
            s, tot, _ = got[ln][j]
            txt = exp_full(exp)
            if s != exp or not tot.startswith(txt): bad.append((ln, m, s, exp, tot))
    q0 = M['arrive_quarterly'][0]['lanes']
    exp22 = [q0[l]['total'][mode] for l in ('nvidia', 'tpu', 'other')]
    for t, e in zip(got['f22'], exp22):
        txt = exp_axis(e)
        if t != txt: bad.append(('f22', t, txt))
    if set(got['btn']) != {mode} or len(got['btn']) != 2: bad.append(('按钮不同步', got['btn']))
    return bad, got

MAG_JS = r'''async ()=>{
 const R={},hl=document.querySelector('#f21 .hl'),tracks=[...hl.querySelectorAll('.hl-track')],cur=hl.querySelector('.hl-cur'),lab=hl.querySelector('.hl-date'),tip=document.getElementById('tip');
 const raf=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const mv=async(x,y,el)=>{(el||document.elementFromPoint(x,y)||hl).dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,bubbles:true}));await raf();};
 const curX=()=>cur.getBoundingClientRect().left, st=()=>({cur:Math.round(curX()*10)/10,lab:lab.textContent,shown:cur.style.display,snap:cur.classList.contains('snap'),nsnap:hl.querySelectorAll('.pin.snap').length,tip:getComputedStyle(tip).display,lr:lab.getBoundingClientRect(),row:hl.querySelector('.hl-axis.top').getBoundingClientRect()});
 /* target: 11/17 pins (OpenAI lane + Nvidia lane, same day) */
 const pin=[...hl.querySelectorAll('.hl-track[data-lane=openai] .pin')].find(p=>(p.getAttribute('data-tip')||'').startsWith('2026-11-17')), dot=pin.querySelector('.pd').getBoundingClientRect(), cx=dot.left+dot.width/2;
 const otr=hl.querySelector('.hl-track[data-lane=internal]').getBoundingClientRect();
 // 1 empty spot (6/20 area, internal lane)
 const tr0=tracks[0].getBoundingClientRect(); await mv(tr0.left+tr0.width*0.10, otr.top+otr.height-3); R.empty=st();
 // 2 3px left of the node (11/18 sits 1 day to the right), in its own lane row
 await mv(cx-3, dot.top+dot.height/2, hl); R.near=st(); R.dotx=cx;
 // 3 other lane, same x (internal lane bottom)
 await mv(cx-3, otr.top+otr.height-3, hl); R.other=st();
 // 4 move away 20px
 await mv(cx+20, otr.top+otr.height-3, hl); R.away=st();
 // 5 direct hover on the pin label (far right of dot)
 const pl=pin.querySelector('.pl').getBoundingClientRect(); const px=pl.left+pl.width*0.7, py=pl.top+pl.height/2;
 pin.querySelector('.pl').dispatchEvent(new PointerEvent('pointerover',{clientX:px,clientY:py,bubbles:true}));
 await mv(px,py,pin.querySelector('.pl')); await new Promise(r=>setTimeout(r,200)); R.direct=st(); R.directBg=getComputedStyle(pin).backgroundColor;
 document.body.dispatchEvent(new PointerEvent('pointerover',{clientX:5,clientY:5,bubbles:true}));
 // 6 edges
 await mv(tr0.left+1, otr.top+otr.height-3, hl); R.left=st(); await mv(tr0.right-1, otr.top+otr.height-3, hl); R.right=st();
 // 7 leave
 hl.dispatchEvent(new PointerEvent('pointerleave',{bubbles:false})); await raf(); R.leave=st();
 return R;}'''

def mag_check(pg):
    pg.evaluate("()=>{const f=document.getElementById('f21');window.scrollTo(0,f.getBoundingClientRect().top+scrollY-60)}")
    pg.wait_for_timeout(150)
    R = pg.evaluate(MAG_JS)
    bad = []
    if R['empty']['snap'] or R['empty']['nsnap']: bad.append('空位误吸')
    if not (R['empty']['row']['left'] - 1 <= R['empty']['lr']['left'] and R['empty']['lr']['right'] <= R['empty']['row']['right'] + 1): bad.append('空位：日期不在刻度行内')
    n = R['near']
    if not (n['snap'] and abs(n['cur'] - R['dotx']) <= 1 and n['lab'] == '2026-11-17' and n['nsnap'] >= 2 and n['tip'] == 'none'): bad.append(('离节点 3px 未吸上', n, R['dotx']))
    o = R['other']
    if not (o['snap'] and abs(o['cur'] - R['dotx']) <= 1 and o['lab'] == '2026-11-17'): bad.append(('别的泳道未吸上', o))
    if R['away']['snap'] or R['away']['nsnap']: bad.append('移开后未松开')
    d = R['direct']
    if d['snap'] or d['nsnap'] or abs(d['cur'] - R['dotx']) > 1 or d['tip'] == 'none': bad.append(('直接悬停状态不对', d))
    for k in ('left', 'right'):
        e = R[k]
        if not (e['row']['left'] - 1 <= e['lr']['left'] and e['lr']['right'] <= e['row']['right'] + 1): bad.append(k + ' 边缘日期出界')
    if R['leave']['shown'] != 'none' or R['leave']['nsnap']: bad.append('移出后未消失')
    return bad, R

def sticky_check(pg):
    return pg.evaluate('''()=>{const f=document.getElementById('f21'),top=f.querySelector('.hl-axis.top'),tb=document.getElementById('topbar');
      const y=f.getBoundingClientRect().top+scrollY+f.offsetHeight*0.55; window.scrollTo(0,y-200); 
      return new Promise(r=>requestAnimationFrame(()=>{const a=top.getBoundingClientRect(),b=tb.getBoundingClientRect(),el=document.elementFromPoint(a.left+a.width/2,a.top+a.height/2);
        const lab=f.querySelector('.hl-track.cmp .lab-in')?f.querySelector('.hl-lab.cmpl'):null;
        r({topRow:a.top,barBottom:b.bottom,onTop:top.contains(el)})}))}''')

def t23_check(pg):
    return pg.evaluate('''()=>{const t=document.getElementById('t23');window.scrollTo(0,t.getBoundingClientRect().top+scrollY+t.offsetHeight*0.5-200);
      return new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>{const c=[...document.querySelectorAll('.sthead')].filter(x=>getComputedStyle(x).visibility==='visible');
       r({clones:c.length,txt:c.length?c[0].textContent.slice(0,20):'',top:c.length?c[0].getBoundingClientRect().top:null,tb:document.getElementById('topbar').getBoundingClientRect().bottom})})))}''')

def main():
    res = {'cases': []}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox']) if CHROME else p.chromium.launch()
        for W in (1440, 1100, 800):
            for fs in ('m', 's', 'l'):
                for th in ('light', 'dark'):
                    pg = b.new_page(viewport={'width': W, 'height': 900})
                    errs = []
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-fs','%s');localStorage.setItem('mdl-theme','%s');localStorage.setItem('mdl-lang','%s')}catch(e){}" % (fs, th, LANG))
                    pg.goto('file://' + F); pg.wait_for_timeout(500)
                    case = {'w': W, 'fs': fs, 'theme': th}
                    case['layout'] = run_layout(pg)
                    case['f23h'] = round(pg.evaluate('window.__f23h'))
                    case['snaptxt'] = pg.evaluate("document.querySelector('#f21 .hl-axis:not(.top) .mt.vm').textContent")
                    case['stag'] = pg.evaluate("document.querySelector('#f22 .qc').classList.contains('stag')")
                    tag = 'w%d-%s-%s-%s' % (W, fs, th, LANG)
                    for sel in ('#f21', '#f22', '#f23', '#t23'):
                        el = pg.query_selector(sel); el.scroll_into_view_if_needed(); pg.wait_for_timeout(60)
                        el.screenshot(path=os.path.join(OUT, '%s-%s.png' % (tag, sel[1:])))
                    if fs == 'm':
                        case['magnet'] = mag_check(pg)[0]
                        pg.screenshot(path=os.path.join(OUT, '%s-snap.png' % tag), clip=None)
                        s = sticky_check(pg); case['sticky'] = s
                        case['sticky_ok'] = abs(s['topRow'] - s['barBottom']) <= 1 and s['onTop']
                        pg.screenshot(path=os.path.join(OUT, '%s-sticky.png' % tag))
                        case['t23'] = t23_check(pg)
                        vals = {}
                        for mode in ('h4', 'units', 'h8'):
                            pg.click('#f22 [data-cmode=%s]' % mode if mode != 'h8' else '#f21 [data-cmode=h8]'); pg.wait_for_timeout(50)
                            bad, got = values_check(pg, mode); vals[mode] = bad
                            if W == 1440 and th == 'light' and mode != 'h8':
                                for sel in ('#f21', '#f22'):
                                    el = pg.query_selector(sel); el.scroll_into_view_if_needed(); el.screenshot(path=os.path.join(OUT, '%s-%s-%s.png' % (tag, sel[1:], mode)))
                            lay = run_layout(pg)
                            if lay: vals[mode + '_layout'] = lay
                        case['values'] = vals
                    case['errors'] = errs
                    res['cases'].append(case); pg.close()
                    flag = 'OK' if not (case['layout'] or errs or case.get('magnet') or (fs == 'm' and not case['sticky_ok']) or any(v for v in case.get('values', {}).values())) else 'FAIL'
                    print(tag, flag, 'f23h=%s' % case['f23h'], case['snaptxt'], 'stag' if case['stag'] else '', case['layout'][:3], errs[:2], case.get('magnet'), case.get('sticky'), case.get('t23'), {k: v for k, v in case.get('values', {}).items() if v})
        b.close()
    json.dump(res, open(os.path.join(OUT, 'qa.json'), 'w'), ensure_ascii=False, indent=1)
main()
