#!/usr/bin/env python3
"""双语输出的公共工具（build_tables.py 与 compute/build.py 共用，只用标准库）。

约定（MAINTAIN.md「双语」一节有完整说明）：
  · 面向读者的文字一律成对出现：数据里写 {"zh": …, "en": …}，代码里写 L('中文', 'English')。
  · 输出到页面时：
      文字   → 两种语言相同就原样输出；不同就输出 <span class="lz">中文</span><span class="le" lang="en">English</span>，
               由 :root[data-lang] 决定显示哪个（CSS 在报告 <style> 里）。
      大段   → BLOCK(...)：<div class="lz">…</div><div class="le" lang="en">…</div>。
      属性   → att('data-tip', x)：输出 data-tip="中文"，不同时再加 data-tip-en="English"；页面 JS 按当前语言取。
               aria-label 例外：英文写进 data-aria-en，切换语言时由页面 JS 换掉 aria-label 本身。
  · 英文缺失时退回中文并记一条提示（qa/i18n_check.py 会判失败）。
另含图 2-1 横轴的推导（两个构建脚本共用，见 axis()）。
"""
import datetime as dt, html, re

MISSING = []          # 英文缺失的中文原文（构建结束时打印）
CJK = re.compile(r'[⺀-鿿　-〿＀-￯]')


class Bi:
    """一对文字（中文 / 英文）。支持 + 拼接、% 格式化（参数可以是 Bi、{zh,en} 字段或普通值）。"""
    __slots__ = ('zh', 'en')

    def __init__(self, zh, en=None):
        self.zh = zh
        self.en = zh if en is None else en

    def get(self, lang): return self.zh if lang == 'zh' else self.en
    def same(self): return self.zh == self.en
    def map(self, f): return Bi(f(self.zh), f(self.en))
    def __add__(self, o): return Bi(self.zh + get(o, 'zh'), self.en + get(o, 'en'))
    def __radd__(self, o): return Bi(get(o, 'zh') + self.zh, get(o, 'en') + self.en)

    def __mod__(self, args):
        if not isinstance(args, tuple): args = (args,)
        return Bi(self.zh % tuple(get(a, 'zh') for a in args), self.en % tuple(get(a, 'en') for a in args))

    def replace(self, a, b): return Bi(self.zh.replace(get(a, 'zh'), get(b, 'zh')), self.en.replace(get(a, 'en'), get(b, 'en')))
    def __bool__(self): return bool(self.zh or self.en)
    def __repr__(self): return 'Bi(%r, %r)' % (self.zh, self.en)


def L(zh, en): return Bi(zh, en)


def bi(x):
    """数据字段 → Bi。{zh,en}：en 为空时退回中文并登记；Bi 原样；其他（品牌名、数字、日期）两种语言相同。"""
    if isinstance(x, Bi): return x
    if isinstance(x, dict) and 'zh' in x:
        zh, en = x['zh'], x.get('en') or ''
        if zh and not en:
            if zh not in MISSING: MISSING.append(zh)
            en = zh
        return Bi(zh, en)
    return Bi(x, x)


def get(x, lang):
    if isinstance(x, Bi): return x.get(lang)
    if isinstance(x, dict) and 'zh' in x: return bi(x).get(lang)
    return x


def by(fn):
    """按语言分别计算：by(lambda l: …) → Bi。"""
    return Bi(fn('zh'), fn('en'))


def join(sep, items):
    items = [bi(i) for i in items]
    s = bi(sep)
    return Bi(s.zh.join(i.zh for i in items), s.en.join(i.en for i in items))


def pair(zh_html, en_html):
    if zh_html == en_html: return zh_html
    return '<span class="lz">%s</span><span class="le" lang="en">%s</span>' % (zh_html, en_html)


def TX(x, f=None):
    """文字输出（HTML 片段）。f：对每种语言再加工一次（例如转义）。"""
    b = bi(x)
    if f: b = b.map(f)
    return pair(b.zh, b.en)


def BLOCK(zh_html, en_html, tag='div'):
    if zh_html == en_html: return zh_html
    return '<%s class="lz">%s</%s><%s class="le" lang="en">%s</%s>' % (tag, zh_html, tag, tag, en_html, tag)


def esc(s): return html.escape(s, quote=True)


def att(name, x, f=esc):
    """属性输出：' name="中文"'，英文不同再加 ' name-en="English"'。f＝转义函数。"""
    b = bi(x)
    s = ' %s="%s"' % (name, f(b.zh))
    if b.en != b.zh: s += ' %s="%s"' % ('data-aria-en' if name == 'aria-label' else name + '-en', f(b.en))   # aria-label 由页面 JS 换
    return s


# ---------------------------------------------------------------- 图 2-1 横轴（两个构建脚本共用）
MONTH_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def axis(snapshot):
    """横轴＝快照日所在月往前 5 个月的月初 → 快照日所在月的最后一天（落在 100% 处）。
    返回 (t0: date, span_days: int, months: [date, …6 个月初])。2026-11-19 → 2026-06-01、182 天。"""
    s = dt.date.fromisoformat(snapshot)
    ym = s.year * 12 + s.month - 1 - 5
    t0 = dt.date(ym // 12, ym % 12 + 1, 1)
    nxt = s.year * 12 + s.month          # 快照月的下一个月
    last = dt.date(nxt // 12, nxt % 12 + 1, 1) - dt.timedelta(days=1)
    months = []
    for k in range(6):
        y = t0.year * 12 + t0.month - 1 + k
        months.append(dt.date(y // 12, y % 12 + 1, 1))
    return t0, (last - t0).days, months


def month_label(m):
    """6 → Bi('6 月', 'Jun')"""
    return Bi('%d 月' % m, MONTH_EN[m - 1])


def month_range(m0, m1):
    """(6, 11) → Bi('6–11 月', 'Jun–Nov')"""
    return Bi('%d–%d 月' % (m0, m1), '%s–%s' % (MONTH_EN[m0 - 1], MONTH_EN[m1 - 1]))


def report_missing(prefix='提示：'):
    for z in MISSING[:20]:
        print(prefix + '英文缺失（已退回中文，qa/i18n_check.py 会判失败）：' + z[:60])
    if len(MISSING) > 20: print(prefix + '…另有 %d 条英文缺失' % (len(MISSING) - 20))
