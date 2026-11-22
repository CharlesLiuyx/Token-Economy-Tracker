#!/usr/bin/env python3
"""色条上的文字对比度检查（无头 Chromium + playwright）：深浅两种主题 × 中英两种语言，遍历页面里所有带色条（background-image 渐变）
且有文字的元素——表 2-1、2-2、2-3、3-1 的分数 / 价格 / 发布格，以及任何把文字压在色条上的地方——
取「文字色」和「文字下方实际底色」（往上找到的不透明底色 + 色条颜色 + 行悬停的 --hover，后两层都按浏览器的方式叠加），
断言 WCAG 对比度 ≥ 4.5:1。不看悬停时和悬停时各算一次，取较差的。色条宽度为 0 的格子跳过。
同时检查图 4-x：条形（.mark）上若压着文字也要 ≥ 4.5（现在文字都在条外，正常是 0 个）。
用法：python3 qa/contrast_check.py 报告.html [chrome 路径] [--min 4.5]   退出码 0＝全部通过。打印每种组合最差的 3 个格子。"""
import json, os, sys
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
MIN = 4.5
if '--min' in args:
    i = args.index('--min'); MIN = float(args[i + 1]); del args[i:i + 2]
F = os.path.abspath(args[0]); CH = args[1] if len(args) > 1 else None
JS = r'''(MIN)=>{
 const cv=document.createElement('canvas');cv.width=cv.height=1;const cx=cv.getContext('2d',{willReadFrequently:true});
 function paint(layers){cx.clearRect(0,0,1,1);for(const c of layers){if(!c)continue;cx.fillStyle='#000';cx.fillStyle=c;cx.fillRect(0,0,1,1)}const d=cx.getImageData(0,0,1,1).data;return [d[0],d[1],d[2]]}
 function lum(c){const f=x=>{x/=255;return x<=0.04045?x/12.92:Math.pow((x+0.055)/1.055,2.4)};return 0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2])}
 function ratio(a,b){const x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)}
 const root=getComputedStyle(document.documentElement),hover=root.getPropertyValue('--hover').trim();
 function under(el){let e=el.parentElement;while(e){const b=getComputedStyle(e).backgroundColor;if(b&&b!=='transparent'&&!/rgba\(0, 0, 0, 0\)/.test(b))return b;e=e.parentElement}return getComputedStyle(document.body).backgroundColor}
 const firstColor=s=>{const m=s.match(/(color\([^)]*\)|rgba?\([^)]*\)|#[0-9a-fA-F]{3,8})/);return m?m[1]:null};
 const out=[];let n=0;
 const els=[...document.querySelectorAll('main *')].filter(e=>{const s=getComputedStyle(e);return /gradient/.test(s.backgroundImage)&&e.getClientRects().length&&e.innerText&&e.innerText.trim()});
 for(const el of els){
   const s=getComputedStyle(el),bar=firstColor(s.backgroundImage);if(!bar)continue;
   const w=parseFloat((s.backgroundSize||'').split(' ')[0]);if(!(w>0)&&!/repeating/.test(s.backgroundImage))continue;
   const base=getComputedStyle(el).backgroundColor,bg=(base&&!/rgba\(0, 0, 0, 0\)/.test(base))?base:under(el);
   const plain=paint([bg,bar]),hov=paint([bg,bar,hover]);
   /* every visible text node inside: its own color */
   const tw=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null);let t;
   while((t=tw.nextNode())){
     if(!t.nodeValue.trim())continue;const p=t.parentElement;if(!p.getClientRects().length)continue;
     const fc=paint([bg,getComputedStyle(p).color]);
     const r=Math.min(ratio(fc,plain),ratio(fc,hov));n++;
     const tb=el.closest('table'),wrap=el.closest('[id]'),tr=el.closest('tr'),mn=tr&&tr.querySelector('.mn');
     out.push({r:Math.round(r*100)/100,txt:t.nodeValue.trim().slice(0,12),where:(wrap?wrap.id:'?'),row:mn?mn.innerText.trim().slice(0,30):'',cls:el.className,bar:bar,bg:plain.join(',')});
   }
 }
 /* figures: text sitting on a bar mark */
 let onMark=0;
 document.querySelectorAll('main figure .mark').forEach(m=>{if(m.innerText&&m.innerText.trim())onMark++});
 out.sort((a,b)=>a.r-b.r);
 return {n:n,bad:out.filter(o=>o.r<MIN),worst:out.slice(0,3),onMark:onMark};
}'''
bad = 0; summary = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch(args=['--no-sandbox'])
    for theme in ('light', 'dark'):
        for lang in ('zh', 'en'):
            pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-theme','%s');localStorage.setItem('mdl-lang','%s')}catch(e){}" % (theme, lang))
            pg.goto('file://' + F); pg.wait_for_timeout(800)
            pg.evaluate("()=>document.querySelectorAll('section.collapsed').forEach(s=>s.classList.remove('collapsed'))")
            r = pg.evaluate(JS, MIN); pg.close()
            tag = '%s-%s' % (theme, lang)
            ok = not r['bad'] and not errs and r['onMark'] == 0
            bad += not ok; summary[tag] = r
            print('%s %s：%d 段文字压在色条上，低于 %.1f 的 %d 段；最差：%s' % (tag, 'OK' if ok else 'FAIL', r['n'], MIN, len(r['bad']),
                  '；'.join('%s %s「%s」%.2f' % (w['where'], w['row'], w['txt'], w['r']) for w in r['worst'])))
            for x in r['bad'][:10]: print('   FAIL', x)
            if errs: print('   JS 报错', errs[:2])
    b.close()
print('全部通过' if not bad else '%d 种组合不通过' % bad)
sys.exit(1 if bad else 0)
