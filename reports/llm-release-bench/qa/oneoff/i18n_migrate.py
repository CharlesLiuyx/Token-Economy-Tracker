#!/usr/bin/env python3
"""一次性迁移（2026-11-22，双语改造）：留档，不要再跑。
把报告里手写的部分（顶栏 / 目录 / 标题 / 第 1、4 章 / 附录来源 / 图 2-1 图注与图例 / TERMS 术语表）
包上 <!--data:s-NAME:start-->…<!--data:s-NAME:end--> 标记，原中文抽进 i18n/static.json（英文另填），
之后这些块都由 build_tables.py 从 static.json 输出。
用法：python3 qa/oneoff/i18n_migrate.py 报告.html  （原地改写；static.json 已存在时只补缺的键）"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = sys.argv[1]
src = open(F, encoding='utf-8').read()
SJ = os.path.join(ROOT, 'i18n', 'static.json')
S = json.load(open(SJ, encoding='utf-8')) if os.path.exists(SJ) else {}
S.setdefault('strings', {}); S.setdefault('templates', {}); S.setdefault('blocks', {})

def Z(zh): return {'zh': zh, 'en': ''}
def once(a, start=0):
    assert src.count(a, start) >= 1, ('anchor', a[:60]); return src.index(a, start)
def wrap(name, a, b, js=False):
    """把 src[a:b] 包上标记，返回原内容。"""
    global src
    st, en = ('/*<!--data:s-%s:start-->*/' % name, '/*<!--data:s-%s:end-->*/' % name) if js else ('<!--data:s-%s:start-->' % name, '<!--data:s-%s:end-->' % name)
    old = src[a:b]; src = src[:a] + st + old + en + src[b:]; return old
def tpl(name, old, template, strings):
    for k, v in strings.items(): S['strings'].setdefault(k, Z(v))
    S['templates'][name] = template
    # 自检：模板按中文渲染必须等于原文
    out = re.sub(r'\{\{t:([a-z0-9_]+)\}\}', lambda m: S['strings'][m.group(1)]['zh'], template)
    out = re.sub(r'\{\{a:([a-z-]+):([a-z0-9_]+)\}\}', lambda m: ' %s="%s"' % (m.group(1), S['strings'][m.group(2)]['zh']), out)
    out = out.replace('{{lang}}', '')
    assert out == old, (name, out[:200], old[:200])

# 1 顶栏控件 + 目录头（不含顶栏标题：那是 data:topbar）
a = once('<button id="back" hidden>'); e = '<div id="tocGrip" data-tip="拖动改目录宽度；双击按文字宽度自动适配"></div>'; b = once(e) + len(e)
old = wrap('chrome', a, b)
tpl('chrome', old,
    '<button id="back" hidden>{{t:back}} ×0</button>\n  {{lang}}<div id="more"><button id="moreBtn">{{t:more}} ▾</button>\n    <div id="menu" hidden>\n'
    '      <div class="mg"><span class="ml">{{t:m_theme}}</span><button data-set="theme:light">{{t:m_light}}</button><button data-set="theme:dark">{{t:m_dark}}</button></div>\n'
    '      <div class="mg"><span class="ml">{{t:m_width}}</span><button data-set="width:n">{{t:m_wn}}</button><button data-set="width:w">{{t:m_ww}}</button><button data-set="width:f">{{t:m_wf}}</button></div>\n'
    '      <div class="mg"><span class="ml">{{t:m_fs}}</span><button data-set="fs:s">{{t:m_fss}}</button><button data-set="fs:m">{{t:m_fsm}}</button><button data-set="fs:l">{{t:m_fsl}}</button></div>\n'
    '      <div class="mg"><span class="ml">{{t:m_terms}}</span><button data-set="terms:on">{{t:m_on}}</button><button data-set="terms:off">{{t:m_off}}</button></div>\n'
    '    </div>\n  </div>\n</div>\n<nav id="toc" aria-label="{{t:toc_aria}}">\n'
    '  <div class="toc-head"><button data-tab="ch" class="on">{{t:toc_ch}}</button><button data-tab="as">{{t:toc_as}}</button><button id="tocAll"{{a:data-tip:toc_all}}>±</button></div>\n'
    '  <ul id="tocCh"></ul><ul id="tocAs" hidden></ul>\n</nav>\n<div id="tocGrip"{{a:data-tip:toc_grip}}></div>',
    {'back': '返回', 'more': '更多', 'm_theme': '主题', 'm_light': '浅色', 'm_dark': '深色', 'm_width': '宽度', 'm_wn': '常规', 'm_ww': '加宽', 'm_wf': '填满',
     'm_fs': '字号', 'm_fss': '小', 'm_fsm': '中', 'm_fsl': '大', 'm_terms': '术语', 'm_on': '开', 'm_off': '关', 'toc_aria': '目录',
     'toc_ch': '章节', 'toc_as': '资产', 'toc_all': '全部展开 / 全部收起', 'toc_grip': '拖动改目录宽度；双击按文字宽度自动适配'})

# 2 h1 → data:h1（标题来自 models.json 的 meta.title，与顶栏同源）
m = re.search(r'<h1>[^<]*</h1>', src); src = src[:m.start()] + '<!--data:h1:start-->' + m.group(0) + '<!--data:h1:end-->' + src[m.end():]

# 3 h2 / h3 标题（h23 在 compute 块里，不动）
for hid in ('h1', 'h2', 'h3', 'h4', 'h5', 'h21', 'h22', 'h31', 'h32', 'h33'):
    m = re.search(r'<(h[23]) id="%s">(.*?)</\1>' % hid, src)
    tag, inner = m.group(1), m.group(2)
    nm = re.match(r'<span class="no">([^<]*)</span>(.*)$', inner)
    if nm:
        no, txt = nm.group(1), nm.group(2)
        if re.search(r'[一-鿿]', no):
            t = '<%s id="%s"><span class="no">{{t:no_%s}}</span>{{t:hd_%s}}</%s>' % (tag, hid, hid, hid, tag); st = {'no_' + hid: no, 'hd_' + hid: txt}
        else:
            t = '<%s id="%s"><span class="no">%s</span>{{t:hd_%s}}</%s>' % (tag, hid, no, hid, tag); st = {'hd_' + hid: txt}
    else:
        t = '<%s id="%s">{{t:hd_%s}}</%s>' % (tag, hid, hid, tag); st = {'hd_' + hid: inner}
    old = wrap('hd-' + hid, m.start(), m.end()); tpl('hd-' + hid, old, t, st)

# 4 第 1 章结论
a = once('<ol class="key">', once('<section class="sec" id="s1">')); b = src.index('</ol>', a) + 5
S['blocks'].setdefault('ch1', Z(wrap('ch1', a, b)))

# 5 图 2-1 图注、图例（compute 块之间的手写部分）与 <div class="hl">（→ data:f21hl，按快照日推导）
a = once('<figure id="f21"'); b = once('<!--compute:f21hints:start-->')
old = wrap('f21cap', a, b)
tpl('f21cap', old, '<figure id="f21" class="bleedw"{{a:data-toc:f21_toc}}><figcaption>{{t:f21_cap}}',
    {'f21_toc': '图 2-1 发布时间轴与算力', 'f21_cap': '图 2-1　发布时间轴与算力（横轴按天等距）'})
a = once('<!--compute:f21hints:end-->') + len('<!--compute:f21hints:end-->'); b = once('<!--compute:f21legend:start-->')
old = wrap('f21leg1', a, b)
tpl('f21leg1', old, '</figcaption><div class="legend"><span class="li2"><i class="pd lg"></i>{{t:f21_l1}}</span><span class="li2"><i class="pd lg ho"></i>{{t:f21_l2}}</span><span class="li2"><i class="rb"></i>{{t:f21_l3}}</span>',
    {'f21_l1': '实心：发布', 'f21_l2': '空心：只是宣布', 'f21_l3': '虚线框：内部代号模型'})
a = once('<!--compute:f21legend:end-->') + len('<!--compute:f21legend:end-->'); e = '</div>'; b = src.index(e, a) + len(e)
old = wrap('f21leg2', a, b)
tpl('f21leg2', old, '<span class="li2"><i class="vd"></i>{{t:f21_l4}}</span></div>', {'f21_l4': '竖虚线：快照日'})
m = re.search(r'<div class="hl" data-t0="[0-9-]+" data-span="[0-9]+">', src)
src = src[:m.start()] + '<!--data:f21hl:start-->' + m.group(0) + '<!--data:f21hl:end-->' + src[m.end():]

# 6 第 4 章
a = once('<div class="hints col">'); b = src.index('</div>', a) + 6
S['blocks'].setdefault('ch4', Z(wrap('ch4', a, b)))

# 7 附录手写来源（「核对方式」之后、算力来源之前）
a = once('<!--data:appendix:end-->') + len('<!--data:appendix:end-->'); b = once('<!--compute:src:start-->')
S['blocks'].setdefault('src', Z(wrap('src', a, b)))

# 8 TERMS / ALIAS（JS）
a = once('var TERMS={'); e = "'METR':'metr'};"; b = once(e) + len(e)
wrap('terms', a, b, js=True)

S['_readme'] = {'zh': '报告里不属于 models.json / vendors.json / compute 的全部固定文字：顶栏、目录、各章标题、第 1 章结论、第 4 章、附录来源、图 2-1 图注图例、术语表、页面 JS 用的界面字。build_tables.py 输出。每条都要 zh、en 同时填。', 'en': 'Every fixed piece of text in the report that is not owned by models.json / vendors.json / compute: top bar, TOC, headings, chapter 1 findings, chapter 4, appendix sources, Fig 2-1 caption and legend, glossary, UI strings used by page JS. Written by build_tables.py. Fill zh and en together.'}
os.makedirs(os.path.dirname(SJ), exist_ok=True)
json.dump(S, open(SJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(F, 'w', encoding='utf-8').write(src)
print('ok', len(src))
