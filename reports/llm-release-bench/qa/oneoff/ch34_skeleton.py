#!/usr/bin/env python3
"""一次性脚本（2026-11-22）：把报告骨架从「1 结论｜2 总表｜3 得分对比图｜4 怎么读｜附录」改成
「1 结论｜2 前沿模型｜3 大厂与开源模型｜4 全部模型对比｜5 怎么读这些数｜附录」——只动骨架和标记，标记之间的内容由
build_tables.py / compute/build.py 重新生成。第 2 章的骨架一个字不动。已经跑过，不要再跑。"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
R = os.path.join(ROOT, '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html')
src = open(R, encoding='utf-8').read()
assert '<!--data:t31:start-->' not in src, '已经改过'
def M(n): return '<!--data:%s:start--><!--data:%s:end-->' % (n, n)
def keep(name, kind='data'):
    st, en = '<!--%s:%s:start-->' % (kind, name), '<!--%s:%s:end-->' % (kind, name)
    a = src.index(st); b = src.index(en) + len(en); return src[a:b]
a = src.index('<section class="sec" id="s3">')
b = src.index('</section>\n</main>') + len('</section>')
new = '\n'.join([
    '<section class="sec" id="s3">',
    M('s-hd-h3'), M('ch3meta'), M('s-hd-h31'), M('t31hints'), M('t31'), M('s-hd-h32'), M('f32'),
    '</section>', '',
    '<section class="sec" id="s4">',
    M('s-hd-h4'), M('s-hd-h41'), M('f41'), M('s-hd-h42'), M('f42'), M('s-hd-h43'), M('f43'), M('s-hd-h44'), M('f44'), M('s-hd-h45'), M('f45'),
    '</section>', '',
    '<section class="sec" id="s5">',
    M('s-hd-h5'), M('s-ch5'),
    '</section>', '',
    '<section class="sec collapsed" id="s6">',
    M('s-hd-h6'),
    M('appendix') + M('s-src') + M('src3') + keep('src', 'compute') + '</section>'])
src = src[:a] + new + src[b:]
# head：第 3、4 章的样式块（在 i18n-css 之后）
x = '<!--data:s-css:end-->'; assert src.count(x) == 1
src = src.replace(x, x + '\n' + M('c34css'))
# 页面脚本：散点标签避让（在 init 之前）
y = '/* ---- init (keep at the very end) ---- */'; assert src.count(y) == 1
src = src.replace(y, '/*<!--data:c34js:start-->*//*<!--data:c34js:end-->*/' + y)
open(R, 'w', encoding='utf-8').write(src)
print('ok')
