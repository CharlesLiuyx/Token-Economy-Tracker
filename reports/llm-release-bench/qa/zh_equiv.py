#!/usr/bin/env python3
"""中文模式等价检查：双语改造后，「中文模式下读者看到的内容」应与改造前一致。
做法：两份 HTML 各自解析成事件流；新版去掉英文节点（class 含 le 的元素整棵）、拆掉中文包裹（class 恰为 lz 的元素只留内容）、
去掉 *-en 属性；两版都去掉 <!--data:/compute:--> 标记注释；<script> / <style> 只比是否存在、不比内容（代码改动另列）。
然后逐事件比较，列出全部差异。--allow 文件（每行一个正则，匹配差异描述）用来登记「有意的改动」。
用法：python3 qa/zh_equiv.py 改造前.html 改造后.html [--allow qa/zh_equiv_allow.txt]   只用标准库。退出码 0＝除登记的有意改动外无差异。"""
import difflib, re, sys
from html.parser import HTMLParser
args = sys.argv[1:]
allow = []
if '--allow' in args:
    i = args.index('--allow'); allow = [re.compile(l.strip()) for l in open(args[i + 1], encoding='utf-8') if l.strip() and not l.startswith('#')]; del args[i:i + 2]
A, B = args
MARK = re.compile(r'(/\*)?<!--(?:data|compute):[a-z0-9_-]+:(?:start|end)-->(\*/)?')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

class P(HTMLParser):
    def __init__(s, new):
        super().__init__(convert_charrefs=True); s.new = new; s.ev = []; s.stack = []; s.skip = 0; s.raw = None
    def handle_starttag(s, t, at):
        at = dict(at); cls = (at.get('class') or '').split()
        if s.skip:
            if t not in VOID: s.stack.append(('skip', t)); s.skip += 1
            return
        if s.new and ('le' in cls or at.get('id') == 'lang'):
            if t not in VOID: s.stack.append(('skip', t)); s.skip = 1
            return
        if s.new and cls == ['lz']:
            s.stack.append(('unwrap', t)); return
        if t in ('script', 'style'): s.raw = t
        keep = tuple(sorted((k, v or '') for k, v in at.items() if not (s.new and (k.endswith('-en') or k in ('data-i18n-skip',)))))
        s.ev.append(('<', t, keep))
        if t not in VOID: s.stack.append(('keep', t))
    def handle_endtag(s, t):
        if t in VOID: return
        if not s.stack: return
        kind, tt = s.stack.pop()
        if kind == 'skip':
            s.skip -= 1; return
        if kind == 'unwrap': return
        if t in ('script', 'style'): s.raw = None
        s.ev.append(('>', t))
    def handle_data(s, d):
        if s.skip or not d: return
        if s.raw: s.ev.append(('raw', s.raw)); return
        if s.ev and s.ev[-1][0] == 't': s.ev[-1] = ('t', s.ev[-1][1] + d)
        else: s.ev.append(('t', d))
    def handle_comment(s, d): pass
def ev(path, new):
    x = MARK.sub('', open(path, encoding='utf-8').read()); p = P(new); p.feed(x); p.close()
    out = []
    for e in p.ev:   # 合并相邻 raw
        if e[0] == 'raw' and out and out[-1] == e: continue
        out.append(e)
    return out
ea, eb = ev(A, False), ev(B, True)
sm = difflib.SequenceMatcher(None, ea, eb, autojunk=False)
diffs = []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal': continue
    diffs.append('%s 改前=%r 改后=%r' % (op, ea[i1:i2][:6], eb[j1:j2][:6]))
ok, bad = [], []
for d in diffs: (ok if any(r.search(d) for r in allow) else bad).append(d)
print('中文模式事件数：改前 %d，改后 %d；差异 %d 处（其中登记为有意改动 %d 处）' % (len(ea), len(eb), len(diffs), len(ok)))
for d in ok: print('  [有意] ' + d[:300])
for d in bad: print('  [未登记] ' + d[:600])
sys.exit(1 if bad else 0)
