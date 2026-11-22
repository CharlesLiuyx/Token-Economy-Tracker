#!/usr/bin/env python3
"""双语检查。三层：
  1 数据：data/models.json、data/vendors.json、i18n/static.json、compute/model.json 里每个 {zh, en} 字段——zh 非空时 en 必须非空、
    英文里不能有汉字（白名单除外）；static.json 的 TERMS 每条都要有英文名和释义。
  2 HTML（静态，只用标准库）：
    · 每个 .lz（中文）后面紧跟一个 .le（英文），两边都有文字；
    · 不在 .lz / .le 里的可见文本节点（两种语言共用）不能有汉字——否则英文模式会漏出中文；
    · 属性：data-tip / data-tiph / data-toc / data-short / data-short-tip / aria-label 含汉字时，必须有对应的英文属性（-en，aria-label 是 data-aria-en），
      且英文属性里没有汉字；.le 里的属性不能有汉字；
    · <script> 里 TERMS 每条都有 ne / de；I18N.en 不含汉字。
  3 浏览器（--browser，需要 playwright）：英文模式下 document.body.innerText、<title>、所有提示框（data-tip / data-tiph / 术语）按英文取值后都没有汉字；
    中文模式下每个 .lz 都可见、.le 都不可见。
白名单：qa/i18n_whitelist.json 的 "allow"（允许在英文模式出现的含汉字字符串，例如模型原名、来源原题；目前为空），
        以及带 data-i18n-skip 属性的元素（语言切换按钮「中文」本来就该写中文）。
用法：python3 qa/i18n_check.py [报告.html] [--browser] [--chrome /usr/bin/google-chrome]   退出码 0＝全部通过。
"""
import json, os, re, sys
from html.parser import HTMLParser
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
args = sys.argv[1:]
BROWSER = '--browser' in args
if BROWSER: args.remove('--browser')
CHROME = None
if '--chrome' in args:
    i = args.index('--chrome'); CHROME = args[i + 1]; del args[i:i + 2]
F = os.path.abspath(args[0]) if args else os.path.join(ROOT, REPORT_NAME)
CJK = re.compile(r'[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]')
WL = json.load(open(os.path.join(HERE, 'i18n_whitelist.json'), encoding='utf-8'))['allow']
def has_cjk(s):
    for w in WL: s = s.replace(w, '')
    return bool(CJK.search(s))
ERR = []
def err(msg):
    ERR.append(msg)

# ---------------------------------------------------------------- 1 数据
def walk(x, path, f):
    if isinstance(x, dict):
        if 'zh' in x and set(x) <= {'zh', 'en'} and isinstance(x['zh'], str):
            zh, en = x['zh'], x.get('en', '')
            if zh and not en: err('%s %s：en 为空（zh＝%s）' % (f, path, zh[:50]))
            elif en and has_cjk(en): err('%s %s：en 里有汉字：%s' % (f, path, en[:60]))
            return 1
        return sum(walk(v, path + '.' + k, f) for k, v in x.items())
    if isinstance(x, list): return sum(walk(v, '%s[%d]' % (path, i), f) for i, v in enumerate(x))
    return 0
n_fields = 0
for rel in ('data/models.json', 'data/vendors.json', 'i18n/static.json', 'compute/model.json'):
    n_fields += walk(json.load(open(os.path.join(ROOT, rel), encoding='utf-8')), '', rel)
S = json.load(open(os.path.join(ROOT, 'i18n', 'static.json'), encoding='utf-8'))
for k, e in S['terms'].items():
    if not (e['n'].get('en') and e['d'].get('en')): err('static.json terms.%s 缺英文' % k)
for k in S['alias']['en'].values():
    if k not in S['terms'] and not re.search(r"\b%s:\{" % k, open(F, encoding='utf-8').read()): err('alias.en 指向不存在的术语 %s' % k)
print('1 数据：%d 个 {zh,en} 字段检查完' % n_fields)

# ---------------------------------------------------------------- 2 HTML
ATTRS = {'data-tip': 'data-tip-en', 'data-tiph': 'data-tiph-en', 'data-toc': 'data-toc-en', 'data-short': 'data-short-en',
         'data-short-tip': 'data-short-tip-en', 'aria-label': 'data-aria-en', 'title': None, 'alt': None, 'placeholder': None}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.st = []                 # (tag, kind) kind ∈ lz / le / skip / raw / ''
        s.pairs = 0; s.shared = 0; s.need_le = None
        s.script = []
    def ctx(s, k): return any(x[1] == k for x in s.st)
    def handle_starttag(s, t, a):
        at = dict(a); cls = (at.get('class') or '').split()
        kind = 'lz' if cls == ['lz'] else ('le' if cls == ['le'] else ('skip' if 'data-i18n-skip' in at else ('raw' if t in ('script', 'style', 'title') else '')))
        if s.need_le is not None:                 # .lz 之后的下一个兄弟元素必须是 .le
            if kind != 'le': err('%s：.lz 后面不是 .le（而是 <%s class=%r>）' % (s.need_le[1], t, at.get('class')))
            s.need_le = None
        in_lz, in_le, in_skip = s.ctx('lz') or kind == 'lz', s.ctx('le') or kind == 'le', s.ctx('skip') or kind == 'skip'
        for k, ek in ATTRS.items():
            v = at.get(k)
            if v is None: continue
            if in_le:
                if has_cjk(v): err('.le 里的属性 %s 有汉字：%s' % (k, v[:60]))
                continue
            if in_lz or in_skip or not has_cjk(v): continue
            ev = at.get(ek) if ek else None
            if ev is None: err('<%s> 属性 %s 含汉字但没有英文属性 %s：%s' % (t, k, ek, v[:60]))
            elif has_cjk(ev): err('<%s> 属性 %s 里有汉字：%s' % (t, ek, ev[:60]))
        if t in VOID: return
        s.st.append((t, kind, ['']) if kind in ('lz', 'le') else (t, kind))
    def handle_endtag(s, t):
        if t in VOID or not s.st: return
        if s.need_le is not None: err('%s：.lz 后面没有 .le' % s.need_le[1]); s.need_le = None
        x = s.st.pop()
        if x[1] == 'lz':
            s.pairs += 1
            if not x[2][0].strip(): err('空的 .lz')
            s.need_le = (len(s.st), x[2][0].strip()[:40])
        elif x[1] == 'le':
            if not x[2][0].strip(): err('空的 .le')
    def handle_data(s, d):
        if not s.st or not d.strip():
            for y in s.st[::-1]:
                if len(y) == 3: y[2][0] += d; break
            return
        if s.ctx('raw'):
            if s.st[-1][0] == 'script': s.script.append(d)
            return
        for y in s.st[::-1]:
            if len(y) == 3: y[2][0] += d; break
        if s.ctx('skip'): return
        if s.ctx('le'):
            if has_cjk(d): err('.le 里有汉字：%s' % d.strip()[:60])
        elif not s.ctx('lz'):
            s.shared += 1
            if has_cjk(d): err('两种语言共用的文本里有汉字（英文模式会漏出中文）：%s' % d.strip()[:60])
src = open(F, encoding='utf-8').read()
body = src[src.index('<body'):]
p = P(); p.feed(body); p.close()
js = '\n'.join(p.script)
for m in re.finditer(r"\n (\w+):\{n:(\"[^\"]*\"|'[^']*'),d:(\"[^\"]*\"|'[^']*')(,ne:(\"[^\"]*\"),de:(\"[^\"]*\"))?\}", js):
    if not m.group(4): err('TERMS.%s 没有 ne / de' % m.group(1))
    elif has_cjk(m.group(5) + m.group(6)): err('TERMS.%s 英文里有汉字' % m.group(1))
mi = re.search(r'var I18N=\{zh:(\{.*?\}),en:(\{.*?\})\};', js)
if not mi: err('找不到 var I18N')
elif has_cjk(mi.group(2)): err('I18N.en 里有汉字')
n_terms = len(re.findall(r"\n (\w+):\{n:", js))
print('2 HTML：%d 对 .lz/.le，%d 个共用文本节点，%d 个术语' % (p.pairs, p.shared, n_terms))

# ---------------------------------------------------------------- 3 浏览器
if BROWSER:
    from playwright.sync_api import sync_playwright
    JS = r'''() => {
      const CJK=/[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]/, WL=%s, R=[];
      const clean=s=>{for(const w of WL)s=s.split(w).join('');return s};
      const skipText=document.querySelectorAll('[data-i18n-skip]');
      skipText.forEach(e=>e.setAttribute('data-i18n-hide',e.style.display||''));
      skipText.forEach(e=>e.style.display='none');
      const txt=clean(document.body.innerText); skipText.forEach(e=>e.style.display=e.getAttribute('data-i18n-hide'));
      const m=txt.match(new RegExp(CJK.source+'.{0,30}','g')); if(m) R.push('页面文字：'+m.slice(0,8).join(' ｜ '));
      if(CJK.test(clean(document.title))) R.push('标题：'+document.title);
      const L=(el,n)=>{const v=el.getAttribute(n+'-en');return v!=null?v:el.getAttribute(n)};
      let nt=0;
      document.querySelectorAll('[data-tip],[data-tiph]').forEach(el=>{ if(el.closest('.lz,[data-i18n-skip]'))return; nt++;
        const v=el.hasAttribute('data-tiph')?L(el,'data-tiph'):L(el,'data-tip'); if(CJK.test(clean(v||''))) R.push('提示：'+v.slice(0,60)); });
      return {errors:R,tips:nt,terms:document.querySelectorAll('.term').length};}''' % json.dumps(WL, ensure_ascii=False)
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox']) if CHROME else pw.chromium.launch(args=['--no-sandbox'])
        for lang in ('en', 'zh'):
            pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.add_init_script("try{localStorage.clear();localStorage.setItem('mdl-lang','%s')}catch(e){}" % lang)
            pg.goto('file://' + F); pg.wait_for_timeout(900)
            pg.evaluate("()=>{document.querySelectorAll('section.collapsed').forEach(s=>s.classList.remove('collapsed'))}")   # 收起的附录也要查
            if errs: err('%s 模式 JS 报错：%s' % (lang, errs[:3]))
            if lang == 'en':
                r = pg.evaluate(JS)
                for e in r['errors']: err('英文模式 ' + e)
                # 术语：逐个悬停一种术语，读提示框
                keys = pg.evaluate("()=>{const s=new Set();document.querySelectorAll('.term').forEach(t=>s.add(t.getAttribute('data-term')));return [...s]}")
                bad_terms = []
                for k in keys:
                    txt = pg.evaluate("(k)=>{const t=[...document.querySelectorAll('.term')].find(x=>x.getAttribute('data-term')===k&&x.offsetParent);if(!t)return null;t.scrollIntoView({block:'center'});"
                                      "const r=t.getBoundingClientRect();t.dispatchEvent(new PointerEvent('pointerover',{bubbles:true,clientX:r.left+2,clientY:r.top+2}));return new Promise(res=>setTimeout(()=>res(document.getElementById('tip').innerText),140))}", k)
                    if txt is None: continue          # 这一种术语在英文模式里没有可见的出现处
                    if not txt or has_cjk(txt): bad_terms.append((k, txt[:40]))
                for k in bad_terms: err('英文模式术语提示有汉字或为空：%s' % (k,))
                print('3 浏览器（英文）：提示 %d 个，术语节点 %d 个、%d 种已逐种悬停' % (r['tips'], r['terms'], len(keys)))
            else:
                bad = pg.evaluate("()=>{let a=0,b=0;document.querySelectorAll('main .lz').forEach(e=>{if(e.closest('section.collapsed'))return;if(!e.getClientRects().length&&e.textContent.trim()&&e.parentElement.getClientRects().length)a++});document.querySelectorAll('.le').forEach(e=>{if(e.getClientRects().length)b++});return [a,b]}")
                if bad[0] or bad[1]: err('中文模式：%d 个 .lz 不可见，%d 个 .le 可见' % tuple(bad))
                print('3 浏览器（中文）：.lz 全可见、.le 全隐藏' if not (bad[0] or bad[1]) else '')
            pg.close()
        b.close()

for e in ERR[:60]: print('FAIL ' + e)
if len(ERR) > 60: print('…另有 %d 条' % (len(ERR) - 60))
print('通过' if not ERR else '不通过：%d 条' % len(ERR))
sys.exit(1 if ERR else 0)
