#!/usr/bin/env python3
"""结构自检：标签配平、section 父元素、id 唯一。用法：python3 qa_struct.py 报告.html"""
import sys,re
from html.parser import HTMLParser
VOID={'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True);s.st=[];s.err=[];s.sec=[];s.ids={}
    def handle_starttag(s,t,a):
        a=dict(a)
        if 'id' in a: s.ids[a['id']]=s.ids.get(a['id'],0)+1
        if t=='section': s.sec.append((a.get('id'),s.st[-1][0] if s.st else None))
        if t not in VOID: s.st.append((t,self_line(s)))
    def handle_endtag(s,t):
        if t in VOID: return
        if not s.st or s.st[-1][0]!=t:
            s.err.append(('mismatch',t,s.getpos(),s.st[-3:])); 
            for i in range(len(s.st)-1,-1,-1):
                if s.st[i][0]==t: del s.st[i:]; break
        else: s.st.pop()
def self_line(s): return s.getpos()[0]
p=P();p.feed(open(sys.argv[1],encoding='utf-8').read())
print('未闭合：',p.st if p.st else '无');print('错配：',p.err[:5] if p.err else '无')
print('section 父元素：',p.sec)
d=[k for k,v in p.ids.items() if v>1];print('重复 id：',d if d else '无')
sys.exit(1 if (p.st or p.err or d or any(x[1]!='main' for x in p.sec)) else 0)
