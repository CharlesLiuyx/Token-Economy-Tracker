#!/usr/bin/env python3
"""第 2 章（前沿模型）一致性检查：改前 / 改后两份报告的第 2 章（2.1–2.3：表 2-1、图 2-1、表 2-2、2.3 节算力）除章名外必须零差异。
两层：
  1 静态：<section id="s2"> 的 HTML 源码，去掉章名块 <!--data:s-hd-h2:…--> 后逐字节比较；章名块只允许标题文字不同。
  2 浏览器（--browser，需要 playwright）：中英两种语言 × 1440 / 800 两种宽度，各自打开两份报告、等脚本跑完（术语标注、节点打包、吸顶），
    取 section#s2 去掉 h2 后的 innerText 和 outerHTML 逐字比较。
比较前默认忽略三类「有意的全局改动」（加 --strict 则一律不忽略；--strict-color 是旧名，同义）：
  · 颜色值（#rrggbb / #rgb / rgb(…)）：厂商色是全局的（2026-11-22 改官方品牌色）；
  · 开源 / 闭源标签：模型名后的 <span class="tag ow-o|ow-c">，以及提示末尾补的「开源（开放权重）。/ 闭源（不开放权重）。」；
  · 表 2-1 模型列和整表的宽度（为放下开源 / 闭源标签加宽）。
用法：python3 qa/ch2_equiv.py 改前.html 改后.html [--browser] [--chrome /usr/bin/google-chrome] [--strict-color]   退出码 0＝一致。
改前版本：git show HEAD:"reports/llm-release-bench/<报告文件名>" > /tmp/prev.html"""
import difflib, re, sys
args = sys.argv[1:]
BROWSER = '--browser' in args
if BROWSER: args.remove('--browser')
STRICT = '--strict-color' in args or '--strict' in args
for a_ in ('--strict-color', '--strict'):
    if a_ in args: args.remove(a_)
COLOR = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)')
OWTAG = re.compile(r'<span class="tag ow-[oc]"[^>]*>(?:<span class="l[ze]"[^>]*>[^<]*</span>|[^<]*)*</span>')
OWTIP = [' 开源（开放权重）。', ' 闭源（不开放权重）。', ' Open weights.', ' Closed weights.']
T21W = re.compile(r'(id="t21"[^>]*><table style="width:)[0-9.]+(em"><colgroup><col style="width:)[0-9.]+em')
def nc(x):
    if STRICT: return x
    x = COLOR.sub('#COLOR', OWTAG.sub('', x))
    for t in OWTIP: x = x.replace(t, '')
    return T21W.sub(r'\1W\2W', x)
CH = None
if '--chrome' in args:
    i = args.index('--chrome'); CH = args[i + 1]; del args[i:i + 2]
OLD, NEW = args[0], args[1]
bad = 0
def sec(src):
    a = src.index('<section class="sec" id="s2">'); b = src.index('</section>', a) + len('</section>'); return src[a:b]
def split_h2(s):
    m = re.search(r'<!--data:s-hd-h2:start-->(.*?)<!--data:s-hd-h2:end-->', s, re.S)
    return s[:m.start()] + s[m.end():], m.group(1)
def first_diff(a, b, label):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != 'equal':
            print('  %s 差异 @%d：改前 %r → 改后 %r' % (label, i1, a[max(0, i1 - 40):i2 + 40][:160], b[max(0, j1 - 40):j2 + 40][:160])); return
o, n = open(OLD, encoding='utf-8').read(), open(NEW, encoding='utf-8').read()
so, h2o = split_h2(sec(o)); sn, h2n = split_h2(sec(n))
ncol = len(set(COLOR.findall(so)) ^ set(COLOR.findall(sn))); nown = len(OWTAG.findall(sn)) - len(OWTAG.findall(so))
so, sn = nc(so), nc(sn)
strip = lambda h: re.sub(r'<span class="(lz|le)"[^>]*>.*?</span>', '', h)
if so == sn: print('1 静态：第 2 章源码（去掉章名%s）逐字节一致，%d 字符%s' % ('' if STRICT else '、颜色值换成占位符', len(so), '' if STRICT else '；颜色值有 %d 个不同，新增开源 / 闭源标签 %d 个' % (ncol, nown)))
else: bad += 1; print('1 静态：第 2 章源码不一致'); first_diff(so, sn, '源码')
if strip(h2o) != strip(h2n): bad += 1; print('1 静态：章名块的结构变了（不只是标题文字）：%r → %r' % (h2o, h2n))
else: print('  章名：%s → %s' % (re.sub('<[^>]+>', ' ', h2o).split(), re.sub('<[^>]+>', ' ', h2n).split()))
if BROWSER:
    import os
    from playwright.sync_api import sync_playwright
    JS = r'''()=>{const s=document.getElementById('s2').cloneNode(true);s.querySelector('h2').remove();
      return {text:s.innerText,html:s.outerHTML,n:s.querySelectorAll('*').length}}'''
    TXT = r'''(strict)=>{const s=document.getElementById('s2'),h=s.querySelector('h2');const tg=strict?[]:[...s.querySelectorAll('.tag.ow-o,.tag.ow-c')];
      tg.forEach(e=>e.style.display='none');const t=s.innerText;tg.forEach(e=>e.style.display='');return t.slice(h.innerText.length)}'''
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CH, args=['--no-sandbox']) if CH else p.chromium.launch(args=['--no-sandbox'])
        for lang in ('zh', 'en'):
            for w in (1440, 800):
                got = []
                for f in (OLD, NEW):
                    pg = b.new_page(viewport={'width': w, 'height': 900}); errs = []
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-lang','%s')}catch(e){}" % lang)
                    pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(900)
                    r = pg.evaluate(JS); r['vis'] = pg.evaluate(TXT, STRICT); r['errs'] = errs; r['html'] = nc(r['html']); got.append(r); pg.close()
                a, c = got
                ok = a['html'] == c['html'] and a['vis'] == c['vis'] and not a['errs'] and not c['errs']
                bad += not ok
                print('2 浏览器 %s %d：%s（%d 个元素，可见文本 %d 字）' % (lang, w, '一致' if ok else '不一致', c['n'], len(c['vis'])))
                if not ok:
                    if a['vis'] != c['vis']: first_diff(a['vis'], c['vis'], '可见文本')
                    if a['html'] != c['html']: first_diff(a['html'], c['html'], 'DOM')
                    if a['errs'] or c['errs']: print('  JS 报错', a['errs'][:2], c['errs'][:2])
        b.close()
print('第 2 章一致（除章名）' if not bad else '第 2 章有 %d 处不一致' % bad)
sys.exit(1 if bad else 0)
