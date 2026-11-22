#!/usr/bin/env python3
"""回归比对：改前 HTML vs 改后 HTML，去掉 <!--data:/compute:NAME:start/end--> 标记注释后逐字节比较；
不一致时再做 DOM 级比较（标签、属性集合、文本），把每处差异列出来。
用法：python3 qa/diff_check.py 改前.html 改后.html   退出码 0＝无差异。只用标准库。"""
import re, sys
from html.parser import HTMLParser
MARK = re.compile(r'(?:/\*)?<!--(?:data|compute):[a-z0-9_-]+:(?:start|end)-->(?:\*/)?')
a = open(sys.argv[1], encoding='utf-8').read(); b = open(sys.argv[2], encoding='utf-8').read()
a0, b0 = MARK.sub('', a), MARK.sub('', b)
print('标记注释：改前 %d 个，改后 %d 个' % (len(MARK.findall(a)), len(MARK.findall(b))))
if a0 == b0:
    print('去掉标记后逐字节一致（%d 字符）。差异 0 处。' % len(a0)); sys.exit(0)

class P(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.ev = []
    def handle_starttag(s, t, at): s.ev.append(('<', t, tuple(sorted((k, v or '') for k, v in at))))
    def handle_endtag(s, t): s.ev.append(('>', t))
    def handle_data(s, d):
        if d: s.ev.append(('t', d))
    def handle_comment(s, d): s.ev.append(('!', d))
def ev(x): p = P(); p.feed(x); p.close(); return p.ev
ea, eb = ev(a0), ev(b0)
import difflib
sm = difflib.SequenceMatcher(None, ea, eb, autojunk=False)
n = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal': continue
    n += 1
    if n <= 40: print('#%d %s\n  改前: %r\n  改后: %r' % (n, op, ea[i1:i2][:4], eb[j1:j2][:4]))
if n == 0:
    # DOM 等价但字节不同（例如属性顺序 / 引号 / 实体写法）
    i = next(k for k in range(min(len(a0), len(b0))) if a0[k] != b0[k])
    print('DOM 级一致，但字节不同；首个不同位置 %d：\n  改前 …%r…\n  改后 …%r…' % (i, a0[i-80:i+80], b0[i-80:i+80]))
    sys.exit(2)
print('DOM 级差异 %d 处' % n); sys.exit(1)
