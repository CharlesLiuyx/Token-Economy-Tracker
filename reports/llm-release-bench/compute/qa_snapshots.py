#!/usr/bin/env python3
"""磁吸 / 直接悬停 / 吸顶 三种状态截图。用法：python3 qa_snapshots.py 报告.html 输出目录 [chrome]"""
import sys, os
from playwright.sync_api import sync_playwright
F, OUT = os.path.abspath(sys.argv[1]), sys.argv[2]; CH = sys.argv[3] if len(sys.argv) > 3 else None
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); pg.goto('file://' + F); pg.wait_for_timeout(500)
    pg.evaluate("()=>{const f=document.getElementById('f21');window.scrollTo(0,f.getBoundingClientRect().top+scrollY-40)}"); pg.wait_for_timeout(100)
    d = pg.evaluate("()=>{const p=[...document.querySelectorAll('#f21 .hl-track[data-lane=openai] .pin')].find(p=>p.style.left==='92.857%').querySelector('.pd').getBoundingClientRect();"
                    "const t=document.querySelector('#f21 .hl-track[data-lane=internal]').getBoundingClientRect();return [p.left+p.width/2,t.top+t.height-4]}")
    pg.mouse.move(d[0] - 3, d[1]); pg.wait_for_timeout(120)
    fr = pg.evaluate("()=>{const r=document.getElementById('f21').getBoundingClientRect();return [r.left,r.top,r.width,r.height]}")
    pg.screenshot(path=os.path.join(OUT, 'snap-magnet.png'), clip={'x': fr[0] + fr[2] * 0.45, 'y': max(0, fr[1]), 'width': fr[2] * 0.55, 'height': min(900 - max(0, fr[1]), fr[3])})
    pl = pg.evaluate("()=>{const r=[...document.querySelectorAll('#f21 .hl-track[data-lane=cmp-nvidia] .pin')][1].querySelector('.pl').getBoundingClientRect();return [r.left+r.width*0.6,r.top+r.height/2]}")
    pg.mouse.move(pl[0], pl[1]); pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(OUT, 'snap-direct.png'), clip={'x': fr[0] + fr[2] * 0.45, 'y': max(0, fr[1]), 'width': fr[2] * 0.55, 'height': min(900 - max(0, fr[1]), fr[3])})
    seg = pg.evaluate("()=>{const s=[...document.querySelectorAll('#f21 .hl-track[data-lane=cmp-nvidia] .mb')][4].querySelector('.sg.c-r200').getBoundingClientRect();return [s.left+s.width/2,s.top+s.height/2]}")
    pg.mouse.move(5, 300); pg.wait_for_timeout(400); pg.mouse.move(seg[0], seg[1]); pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(OUT, 'snap-segment-tip.png'), clip={'x': fr[0], 'y': max(0, fr[1]), 'width': fr[2], 'height': min(900 - max(0, fr[1]), fr[3] + 120)})
    pg.mouse.move(5, 5)
    pg.evaluate("()=>{const f=document.getElementById('f21');window.scrollTo(0,f.getBoundingClientRect().top+scrollY+330)}"); pg.wait_for_timeout(100)
    pg.mouse.move(d[0] - 200, 300); pg.wait_for_timeout(120)
    pg.screenshot(path=os.path.join(OUT, 'snap-sticky.png'), clip={'x': 250, 'y': 0, 'width': 1190, 'height': 520})
    b.close()
