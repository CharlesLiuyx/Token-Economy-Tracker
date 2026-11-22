#!/usr/bin/env python3
"""把 compute/model.json 写进报告 HTML（图 2-1 到卡三行、2.3 节、术语、来源）。
幂等：每块内容包在 <!--compute:NAME:start--> … <!--compute:NAME:end--> 里（JS / CSS 里写成 /*<!--…-->*/）。
第一次运行按原文锚点插入；之后只替换标记之间的内容。重复跑结果逐字节一致。
用法：python3 build.py [报告路径]   默认 = 构建目录上一级的报告文件。
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
REPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(HERE, '..', REPORT_NAME))
M = json.load(open(os.path.join(HERE, 'model.json'), encoding='utf-8'))
RAMPS = json.load(open(os.path.join(HERE, 'ramps.json'), encoding='utf-8'))

def A(s):  # attribute escape
    return html.escape(s, quote=True)

SK = {s['key']: s for s in M['skus']}
ORDER = [s['key'] for s in M['skus']]           # 堆叠顺序：自下而上＝老到新
LANES = [l['key'] for l in M['lanes']]
LANE_NAME = {l['key']: l['name'] for l in M['lanes']}
LANE_KEY = {'nvidia': 'nvidia', 'tpu': 'google', 'other': 'other'}   # 与报告已有的聚光键对齐
SHORT = {'hopper': 'H100/H200', 'b200': 'B200', 'b300': 'B300', 'r200': 'Rubin', 'rubin_ultra': 'Rubin Ultra',
         'tpu_v6e': 'v6e', 'tpu_v7': 'v7', 'tpu_v8i': 'v8i', 'tpu_v8t': 'v8t',
         'trn2': 'Trn2', 'trn3': 'Trn3', 'mi300': 'MI300', 'mi355': 'MI355', 'mi450': 'MI450'}
NX = dict(SHORT, tpu_v6e='TPU v6e', tpu_v7='TPU v7', tpu_v8i='TPU v8i', tpu_v8t='TPU v8t', trn2='Trainium2', trn3='Trainium3')
# 颜色：Nvidia 石墨灰、TPU 与 Google 同一蓝色系、Trainium＋AMD 品红；型号按代际由浅到深（深色主题由暗到亮）。
# 已过 dataviz 校验：各色阶 ordinal 两种主题全过；泳道色与 Google / Anthropic / OpenAI 两两比较最差 CVD 9.2（浅）/ 9.4（深）。
RAMP_IDX = {'hopper': ('nv', 0), 'b200': ('nv', 1), 'b300': ('nv', 2), 'r200': ('nv', 3), 'rubin_ultra': ('nv', 4),
            'tpu_v6e': ('tpu', 0), 'tpu_v7': ('tpu', 1), 'tpu_v8i': ('tpu', 2), 'tpu_v8t': ('tpu', 3),
            'trn2': ('trn', 0), 'trn3': ('trn', 1), 'mi300': ('amd', 0), 'mi355': ('amd', 1), 'mi450': ('amd', 2)}
def col(k, mode):
    r, i = RAMP_IDX[k]; return RAMPS['%s_%s' % (r, mode)][i]

MODES = ('h8', 'h4', 'units')
def wan(v, unit=True):
    w = v / 1e4
    s = ('%d' % round(w)) if w >= 100 else ('%.1f' % w)
    return s + (' 万' if unit else '')
def cnum(n):
    return format(int(round(n)), ',')
def coef(x):
    return ('%.2f' % x).rstrip('0').rstrip('.') if x < 10 else ('%.1f' % x if x * 10 % 1 == 0 else '%.2f' % x)
def coefs(x):
    return '%.2f' % x
def nobr(s):
    return s[:-4] if s.endswith('<br>') else s
def monthcn(m):
    return '%d 月' % int(m[5:])
def ym(m):
    return '%s 年 %d 月' % (m[:4], int(m[5:]))

T0, SPAN = '2026-06-01', 182
def daypct(d):
    import datetime
    a = datetime.date.fromisoformat(T0); b = datetime.date.fromisoformat(d)
    return (b - a).days / SPAN * 100
WIN = ['2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11']
MON = {r['month']: r for r in M['arrive_monthly']}
def lane_total(m, ln, mode): return MON[m]['lanes'][ln]['total'][mode]
FIG1_MAX = {md: max(lane_total(m, ln, md) for m in WIN for ln in LANES) for md in MODES}
LANE_SUM = {ln: {md: sum(lane_total(m, ln, md) for m in WIN) for md in MODES} for ln in LANES}
KIND_TXT = {'epoch': 'Epoch AI 估算', 'sa': 'SemiAnalysis 估算', 'forecast': 'SemiAnalysis 预测', 'est': '本报告推算'}

def seg_tip(sg, am):
    s = SK[sg['sku']]
    lag = s['lag']
    t = ('<b>%s · %s到卡</b>' % (html.escape(s['name']), ym(am)) +
         '对应出货月：%s（出货后约 %d 个月投入使用）<br>' % (ym(sg['ship_month']), lag) +
         '颗数：%s 颗<br>' % cnum(sg['units']) +
         '每颗折合：%s 颗 H100（8 位）／%s 颗（4 位）<br>' % (coefs(s['f8']), coefs(s['f4'])) +
         '合计：%s（8 位）／%s（4 位）H100 等效<br>' % (wan(sg['h8']), wan(sg['h4'])) +
         '出货数来源：%s〔%s〕<br>换算系数：%s〔%s〕' % (html.escape(sg['src']), sg['conf'], html.escape(s['basis']), s['conf']))
    if sg['hatch']:
        t += '<br>斜线＝这一段是预测或推算。'
    return t

def stack_html(segs, am, cls='stk', tot_tip=''):
    """一根堆叠柱：段按 ORDER 自下而上；高度由 JS 按当前换算方式写入（这里先写 8 位的值，无 JS 也能看）。"""
    out = []
    for sg in sorted(segs, key=lambda x: ORDER.index(x['sku'])):
        k = sg['sku']
        out.append('<i class="sg c-%s%s" data-key="%s %s" data-cv="%d,%d,%d" data-tiph="%s"></i>' % (
            k, ' ht' if sg['hatch'] else '', k, LANE_KEY[SK[k]['lane']], sg['h8'], sg['h4'], sg['units'], A(seg_tip(sg, am))))
    return out

# ------------------------------------------------------------------ fig 2-1 lanes
def f21_lanes():
    ml = ''.join('<i class="ml" style="left:%s"></i>' % p for p in ('16.484%', '33.516%', '50.549%', '67.033%', '84.066%')) + '<i class="vl" style="left:93.956%"></i>'
    PINS = {
        'nvidia': ['<span class="pin" data-key="nvidia" style="left:47.253%" data-tip="2026-08-26 Nvidia 财报：Rubin 进入全面量产，机柜已在 CoreWeave、Google Cloud、Microsoft Azure、Oracle、Nebius 运行。〔高〕"><i class="pd"></i><span class="pl noterm"><small>8/26</small> 机柜已在 5 家云上运行</span></span>',
                   '<span class="pin" data-key="nvidia" style="left:92.857%" data-tip="2026-11-17 Nvidia 财报：Oracle 和 Google Cloud 已对外提供 Rubin 实例；SpaceXSI 的机柜即将上线；Anthropic 通过云厂商拿到更多 Blackwell 和 Rubin 算力。大客户约 1 个月就能把 Rubin 投入生产，是 Grace Blackwell 的一半。〔高〕"><i class="pd"></i><span class="pl noterm"><small>11/17</small> 财报：NVL72 已出货</span></span>'],
        'tpu': ['<span class="pin" data-key="google" style="left:51.099%" data-tip="2026-09-02 博通财报：给 Anthropic 和 Google 的 Ironwood 已大批量出货；给 Google 的 TPU 8i 开始量产出货；下一财季加快给 Anthropic 的 Ironwood 出货。Anthropic 的部署计划：2026 年 1 GW（Ironwood），2027 年再加 5 GW（TPU 8i），2028 年再加 10 GW。这是管理层预期。〔中〕"><i class="pd"></i><span class="pl noterm"><small>9/2</small> 博通财报：v8i 开始出货 · Anthropic 今年 1 GW</span></span>'],
        'other': [],
    }
    LAB_TIP = {
        'nvidia': 'Nvidia 每月到卡的算力，按型号分段：H100/H200、B200、B300、Rubin。上面一行是事件。悬停一段看颗数和来源；悬停这里只看 Nvidia。',
        'tpu': 'Google TPU 每月到卡的算力，按型号分段：v6e、v7（Ironwood）、v8i、v8t。上面一行是事件。悬停这里只看 Google。',
        'other': 'AWS Trainium 与 AMD Instinct 每月到卡的算力，按型号分段：Trainium2、Trainium3、MI300、MI355、MI450。悬停这里只看这一行。',
    }
    SW = {'nvidia': 'k-nvidia', 'tpu': 'k-google', 'other': 'k-other'}
    h = []
    for i, ln in enumerate(LANES):
        sep = ' sep' if i == 0 else ''
        s = LANE_SUM[ln]
        h.append('<div class="hl-lab li cmpl%s" data-key="%s" data-tip="%s"><div class="lab-in"><span class="sw %s"></span>到卡<span class="ln">%s</span>'
                 '<small data-cmsum="%d,%d,%d">6–11 月 ≈ %s</small><small class="cm-unit">8 位 H100 等效</small></div></div>' % (
                     sep, LANE_KEY[ln], A(LAB_TIP[ln]), SW[ln], html.escape(LANE_NAME[ln]), s['h8'], s['h4'], s['units'], wan(s['h8'])))
        bars = []
        for j, m in enumerate(WIN):
            l0 = daypct(m + '-01')
            l1 = daypct(WIN[j + 1] + '-01') if j + 1 < len(WIN) else 100.0
            rec = MON[m]['lanes'][ln]
            tot = rec['total']
            rows = ''.join('%s %s（8 位）<br>' % (SHORT[sg['sku']], wan(sg['h8'])) for sg in sorted(rec['segs'], key=lambda x: -ORDER.index(x['sku'])) if sg['h8'] > 0)
            tip = nobr(('<b>%s · %s到卡合计</b>%s 颗；%s（8 位）／%s（4 位）H100 等效<br>%s' % (
                html.escape(LANE_NAME[ln]), ym(m), cnum(tot['units']), wan(tot['h8']), wan(tot['h4']), rows)))
            bars.append('<div class="mb" style="left:calc(%.3f%% + 2px);width:calc(%.3f%% - 4px)"><div class="stk">%s<span class="tot" data-tiph="%s">%s</span></div></div>' % (
                l0, l1 - l0, ''.join(stack_html(rec['segs'], m)), A(tip), wan(tot['h8'])))
        h.append('<div class="hl-track cmp%s" data-lane="cmp-%s">%s%s<div class="cbars" data-cmax="%d,%d,%d">%s</div></div>' % (sep, ln, ml, ''.join(PINS[ln]), FIG1_MAX['h8'], FIG1_MAX['h4'], FIG1_MAX['units'], ''.join(bars)))
    return ''.join(h)

def f21_top():
    ticks = ''.join('<i class="mt" style="left:%s">%s</i>' % (p, t) for p, t in (('0.000%', '6 月'), ('16.484%', '7 月'), ('33.516%', '8 月'), ('50.549%', '9 月'), ('67.033%', '10 月'), ('84.066%', '11 月')))
    return '<div class="hl-lab ax top"></div><div class="hl-axis top">%s<b class="hl-date" aria-hidden="true"></b></div>' % ticks

SWITCH = ('<span class="msw" role="group" aria-label="换算方式">'
          '<button data-cmode="h8" class="on" data-tip="每颗卡按稠密 8 位算力（FP8 或 INT8）折合几颗 H100。与 Epoch AI 的算法一致。">按 8 位算力</button>'
          '<button data-cmode="h4" data-tip="每颗卡按稠密 4 位算力（FP4）折合几颗 H100；没有 FP4 的卡按 8 位算。分母仍是 H100 的 8 位算力，因为 H100 没有 FP4。看的是推理峰值。">按 4 位算力</button>'
          '<button data-cmode="units" data-tip="不换算，直接数封装颗数。用来对照：颗数的排序和算力的排序不一样。">按颗数</button></span>')

def f21_legend():
    return ('<span class="li2"><i class="cbl"></i><span>柱：每月到卡，按型号分段</span></span>'
            '<span class="li2"><i class="htl"></i><span>斜线：预测或推算</span></span>' + SWITCH)

F21_HINTS = (
    '<span class="hint" data-tiph="%s">怎么读<i>?</i></span><span class="hint" data-tiph="%s">算力行<i>?</i></span>' % (
        A('<b>怎么读</b>方块的左右位置就是日期；上下错开只是为了不重叠。<br>鼠标在图上移动，顶部刻度行读出日期；离节点 5 像素以内时，竖线和日期吸到节点上，同一天的节点一起放大。<br>内部代号模型画的是训练完成的时间段，时间来自 METR 的报告。<br>下面三行是每月到卡的算力：每月一根柱，按型号分段，柱顶是当月合计。三行用同一个纵轴，高度可以直接比。斜线段是预测或推算。'),
        A('<b>算力行：每月到卡多少 H100 等效</b>到卡＝出货后往后挪 1–2 个月：Rubin、TPU、Trainium 挪 1 个月，Blackwell、Hopper、AMD 挪 2 个月。Nvidia 11 月 17 日说，大客户约 1 个月就能把 Rubin 投入生产，是 Grace Blackwell 的一半。<br>H100 等效＝颗数 × 每颗折合几颗 H100。按 8 位算力：每颗卡的稠密 FP8（或 INT8）÷ H100 的 1,979 TFLOPS；按 4 位算力：稠密 FP4 ÷ 同一个分母。<br>Rubin 和 GB300 不能按颗数比：一颗 Rubin 按 8 位约等于 %s 颗 GB300，按 4 位约 %s 颗。<br>出货数：到 2026 年 10 月以 Epoch AI（2026-11-19 版）为主；Rubin 下半年以 Nvidia 财季（7/27–10/25）的 Epoch 合计为锚、按爬坡拆到月；11 月起的出货用 SemiAnalysis（2026-11-13）的预测，两家都没有的由本报告推算。做法与假设见 2.3 节。〔中〕' % (
            '%.1f' % (SK['r200']['f8'] / SK['b300']['f8']), '%.1f' % (SK['r200']['f4'] / SK['b300']['f4'])))))

# ------------------------------------------------------------------ fig 2-2 quarterly
Q = M['arrive_quarterly']
def f22():
    QMAX = {md: max(q['lanes'][ln]['total'][md] for q in Q for ln in LANES) for md in MODES}
    leg = []
    for ln in LANES:
        items = ''.join('<span class="li" data-key="%s %s" data-tip="%s"><i class="sw c-%s"></i>%s</span>' % (
            k, LANE_KEY[ln], A('%s：每颗折合 %s 颗 H100（8 位）／%s 颗（4 位）。悬停只看这个型号。' % (SK[k]['name'], coefs(SK[k]['f8']), coefs(SK[k]['f4']))), k, html.escape(SHORT[k]))
            for k in ORDER if SK[k]['lane'] == ln)
        leg.append('<span class="lg-grp"><span class="li lg-h" data-key="%s" data-tip="%s">%s</span>%s</span>' % (
            LANE_KEY[ln], A('悬停只看 %s 这一组。' % LANE_NAME[ln]), html.escape({'other': '其他（Trainium＋AMD）'}.get(ln, LANE_NAME[ln])), items))
    groups, xl = [], []
    for q in Q:
        bars = []
        for ln in LANES:
            rec = q['lanes'][ln]; tot = rec['total']
            segs = []
            for b in rec['segs']:
                s = SK[b['sku']]
                hatch_share = b['hatch_h8'] / b['h8'] if b['h8'] else 0
                kinds = '、'.join(KIND_TXT[x] for x in b['kinds'])
                tip = ('<b>%s · %s到卡</b>对应出货月：%s<br>颗数：%s 颗<br>每颗折合：%s 颗 H100（8 位）／%s 颗（4 位）<br>合计：%s（8 位）／%s（4 位）H100 等效<br>出货数来源：%s%s<br>换算系数：%s〔%s〕' % (
                    html.escape(s['name']), q['quarter'], '、'.join(b['ship_months']), cnum(b['units']), coefs(s['f8']), coefs(s['f4']),
                    wan(b['h8']), wan(b['h4']), kinds, '；其中 %d%% 是预测或推算' % round(hatch_share * 100) if 0 < hatch_share < 1 else '', html.escape(s['basis']), s['conf']))
                segs.append('<i class="sg c-%s%s" data-key="%s %s" data-cv="%d,%d,%d" data-tiph="%s"></i>' % (
                    b['sku'], ' ht' if hatch_share >= 0.5 else '', b['sku'], LANE_KEY[ln], b['h8'], b['h4'], b['units'], A(tip)))
            rows = ''.join('%s %s（8 位）<br>' % (SHORT[b['sku']], wan(b['h8'])) for b in sorted(rec['segs'], key=lambda x: -ORDER.index(x['sku'])) if b['h8'] > 0)
            ttip = nobr(('<b>%s · %s到卡合计</b>%s 颗；%s（8 位）／%s（4 位）H100 等效<br>%s' % (
                html.escape(LANE_NAME[ln]), q['quarter'], cnum(tot['units']), wan(tot['h8']), wan(tot['h4']), rows)))
            bars.append('<div class="qb"><div class="stk">%s<span class="tot" data-tiph="%s">%s</span></div></div>' % (''.join(segs), A(ttip), wan(tot['h8'], False)))
        groups.append('<div class="qg">%s</div>' % ''.join(bars))
        t = q['total']
        xl.append('<div class="qx"><span class="qln"><i data-tip="Nvidia">Nvidia</i><i data-tip="Google TPU">TPU</i><i data-tip="其他＝AWS Trainium＋AMD">其他</i></span>'
                  '<span class="qq">%s</span><span class="qt" data-cv="%d,%d,%d" data-tip="%s">合计 %s</span></div>' % (
                      q['quarter'], t['h8'], t['h4'], t['units'],
                      A('%s 三条泳道合计到卡：%s 颗；%s（8 位）／%s（4 位）H100 等效。' % (q['quarter'], cnum(t['units']), wan(t['h8']), wan(t['h4']))), wan(t['h8'], False)))
    return ('<figure id="f22" class="cmpfig" data-toc="图 2-2 按季到卡">'
            '<figcaption>图 2-2　按季到卡：三家各多少 H100 等效（2025Q4–2027Q2）<span class="hint" data-tiph="%s">怎么读<i>?</i></span></figcaption>'
            '<div class="legend">%s<span class="li2"><i class="htl"></i><span>斜线：预测或推算</span></span>%s</div>'
            '<div class="qc" data-cmax="%d,%d,%d"><div class="qc-unit cm-unit">单位：万 H100 等效（8 位）</div><div class="qc-y"></div><div class="qc-plot"><div class="qc-grid"></div>%s</div><div class="qc-x">%s</div></div>'
            '</figure>') % (
        A('<b>怎么读</b>每季三根柱，从左到右：Nvidia、Google TPU、其他（＝AWS Trainium＋AMD）。每根按型号分段，柱顶是这一季到卡的合计，季度下面是三家合计。<br>到卡季度＝出货月往后挪 1–2 个月之后所在的季度。<br>2027 年两季全部是预测或推算。<br>图例悬停只看一个型号；用上面的按钮切换换算方式，图 2-1 同步切换。'),
        ''.join(leg), SWITCH, QMAX['h8'], QMAX['h4'], QMAX['units'], ''.join(groups), ''.join(xl))

# ------------------------------------------------------------------ fig 2-3 coefficients
def f23():
    rows = sorted(M['skus'], key=lambda s: (-s['f8'], ORDER.index(s['key'])))
    mx = 36.0
    out = []
    ratio8 = SK['r200']['f8'] / SK['b300']['f8']; ratio4 = SK['r200']['f4'] / SK['b300']['f4']
    for s in rows:
        k = s['key']; em = k in ('b300', 'r200')
        est8 = k in ('tpu_v8i', 'tpu_v8t', 'rubin_ultra'); est4 = k == 'rubin_ultra'
        nofp4 = abs(s['f8'] - s['f4']) < 1e-9
        tip8 = '%s：按 8 位算力，每颗折合 %s 颗 H100。%s〔%s〕' % (s['name'], coefs(s['f8']), s['basis'], s['conf'])
        tip4 = '%s：按 4 位算力，每颗折合 %s 颗 H100。%s' % (s['name'], coefs(s['f4']), '没有 FP4，按 8 位算。' if nofp4 else s['basis'] + '〔%s〕' % s['conf'])
        out.append('<div class="cr%s" data-key="%s %s"><span class="cn noterm" data-tip="%s"><i class="sw c-%s"></i>%s</span>'
                   '<span class="ct"><span class="cbar b8 c-%s%s" style="width:%.2f%%" data-tip="%s"></span><span class="cbar f4 c-%s%s" style="width:%.2f%%" data-tip="%s"></span></span>'
                   '<span class="cv"><b>%s</b> ／ %s%s</span></div>' % (
                       ' em' if em else '', k, LANE_KEY[s['lane']], A('%s · %s。时滞：出货后约 %d 个月到卡。' % (s['name'], LANE_NAME[s['lane']], s['lag'])), k, html.escape(s['name'].replace('（含 Meta 定制）', '')),
                       k, ' ht' if est8 else '', s['f8'] / mx * 100, A(tip8), k, ' ht' if est4 else '', s['f4'] / mx * 100, A(tip4),
                       coefs(s['f8']), coefs(s['f4']), '<small>无 FP4</small>' if nofp4 else ''))
    ticks = ''.join('<i style="left:%.3f%%"%s>%d</i>' % (v / mx * 100, ' class="f"' if v == 0 else '', v) for v in range(0, 36, 5))
    return ('<figure id="f23" class="cmpfig" data-toc="图 2-3 一颗卡折合几颗 H100">'
            '<figcaption>图 2-3　一颗卡折合几颗 H100（按 8 位算力排序）<span class="hint" data-tiph="%s">怎么读<i>?</i></span></figcaption>'
            '<div class="legend"><span class="li2"><i class="c8l"></i><span>上条：按 8 位算力</span></span><span class="li2"><i class="c4l"></i><span>下条：按 4 位算力</span></span><span class="li2"><i class="htl"></i><span>斜线：推算或假设的系数</span></span>'
            '<span class="li2 rnote" data-tip="%s"><span>Rubin ≈ %.1f 个 GB300（8 位）／≈ %.1f 个（4 位）</span></span></div>'
            '<div class="cg"><div class="cr hd"><span class="cn">型号</span><span class="ct"><span class="ticks">%s</span></span><span class="cv">8 位 ／ 4 位</span></div>%s</div></figure>') % (
        A('<b>怎么读</b>每个型号一行两根条：上条按 8 位算力，下条按 4 位算力，单位是「折合几颗 H100」。<br>8 位＝稠密 FP8 或 INT8 取大，÷ H100 的 1,979 TFLOPS。4 位＝稠密 FP4，÷ 同一个分母；没有 FP4 的卡两根一样长。<br>GB300 和 Rubin 两行加了底色：同样是「一颗」，算力差 2–3.5 倍。<br>斜线：TPU v8i / v8t 的 8 位是按 FP4 ÷ 2 推算的；Rubin Ultra 两个系数都是按 Rubin × 2 假设的。'),
        A('一颗 Rubin 按 8 位算力是 %s ÷ %s ≈ %.1f 颗 GB300，按 4 位是 %s ÷ %s ≈ %.1f 颗。只数颗数，会把一颗 Rubin 当成一颗 GB300。' % (coefs(SK['r200']['f8']), coefs(SK['b300']['f8']), ratio8, coefs(SK['r200']['f4']), coefs(SK['b300']['f4']), ratio4)),
        ratio8, ratio4, ticks, ''.join(out))

# ------------------------------------------------------------------ table 2-3
def t23():
    QS = M['quarters_ship']; ST = M['ship_quarterly']
    cols = '<col style="width:13.5em">' + ''.join('<col style="width:6.2em">' for _ in QS)
    th = '<th class="c0" data-tip="型号，按泳道分组。组标题那一行是这一组的合计。">型号</th>' + ''.join(
        '<th class="num%s" data-tip="%s">%s</th>' % (' gs' if i == 0 else '', A('%s（日历季）出货的封装颗数。%s' % (q, '这一季全部来自 Epoch AI。' if q < '2026Q3' else '悬停每格看来源。')), q) for i, q in enumerate(QS))
    body = []
    for ln in LANES:
        tots = [sum(ST[k][q]['units'] for k in ORDER if SK[k]['lane'] == ln) for q in QS]
        body.append('<tr class="grp"><td class="c0"><span class="gl"><span class="sw %s"></span>%s</span></td>%s</tr>' % (
            {'nvidia': 'k-nvidia', 'tpu': 'k-google', 'other': 'k-other'}[ln], html.escape(LANE_NAME[ln]),
            ''.join('<td class="num%s">%s</td>' % (' gs' if i == 0 else '', cnum(t)) for i, t in enumerate(tots))))
        for k in ORDER:
            if SK[k]['lane'] != ln: continue
            tds = []
            for i, q in enumerate(QS):
                c = ST[k][q]; u = c['units']
                kind = c['src']
                lab = c['label']
                if kind == 'sa' and q >= '2026Q4': lab = 'SemiAnalysis Accelerator Outlook 预测（2026-11-13）'
                tip = '%s · %s：%s 颗。来源：%s〔%s〕。%s' % (SK[k]['name'], q, cnum(u), lab, c['conf'], c['note'])
                cls = 'num' + (' gs' if i == 0 else '') + (' est' if kind == 'est' else '') + (' na' if u == 0 else '')
                tds.append('<td class="%s" data-tip="%s">%s</td>' % (cls, A(tip.strip()), cnum(u) if u else '—'))
            body.append('<tr><td class="c0 noterm" data-tip="%s"><span class="sw c-%s"></span>%s</td>%s</tr>' % (
                A('%s：每颗折合 %s 颗 H100（8 位）／%s 颗（4 位）。' % (SK[k]['name'], coefs(SK[k]['f8']), coefs(SK[k]['f4']))), k, html.escape(SK[k]['name']), ''.join(tds)))
    width = 13.5 + 6.2 * len(QS)
    return ('<div class="tblwrap wide" id="t23" data-toc="表 2-3 按季出货颗数"><table style="width:%.1fem"><colgroup>%s</colgroup><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>') % (width, cols, th, ''.join(body))

# ------------------------------------------------------------------ section 2.3
def s23():
    nv, tp, ot = (LANE_SUM[l]['h8'] for l in LANES)
    tot = nv + tp + ot
    rub = {}
    for r in M['arrive_monthly']:
        segs = r['lanes']['nvidia']['segs']; t = r['lanes']['nvidia']['total']['h8']
        rub[r['month']] = sum(s['h8'] for s in segs if s['sku'] in ('r200', 'rubin_ultra')) / t if t else 0
    first = next(m for m in sorted(rub) if rub[m] > 0.5)
    h1 = [rub[m] for m in ('2027-01', '2027-02', '2027-03', '2027-04', '2027-05', '2027-06')]
    nov = MON['2026-11']['lanes']
    q4 = next(q for q in Q if q['quarter'] == '2026Q4')['lanes']
    q27 = next(q for q in Q if q['quarter'] == '2027Q2')['lanes']
    sh = M['ship_monthly']
    def pct(x): return '%d%%' % round(x * 100)
    def ranks(qn):
        qq = next(q for q in Q if q['quarter'] == qn)
        segs = [(b['sku'], b['units'], b['h8']) for l in LANES for b in qq['lanes'][l]['segs']]
        return sorted(segs, key=lambda x: -x[1]), sorted(segs, key=lambda x: -x[2])
    r4u, r4h = ranks('2026Q4'); r1u, r1h = ranks('2027Q1')
    # 结论文字的前提：数据变了就让构建失败，而不是写出错话
    assert r4u[0][0] == 'b300' and r4h[0][0] == 'r200' and r4h[1][0] == 'b300' and [x[0] for x in r4u].index('r200') == 2, (r4u[:3], r4h[:2])
    assert r1u[1][0] == 'trn3' and r1h[1][0] == 'mi450' and 'trn3' not in [x[0] for x in r1h[:5]], (r1u[:2], r1h[:5])
    assert rub['2026-08'] < rub['2026-09'] < rub['2026-10'] < rub['2026-11'] < 0.5 < rub['2026-12'] and first == '2026-12', rub
    assert q4['nvidia']['total']['h4'] / q4['tpu']['total']['h4'] > q4['nvidia']['total']['h8'] / q4['tpu']['total']['h8']
    concl = [
        '<li><b>6–11 月到卡（按 8 位算力）：Nvidia ≈ %s、TPU ≈ %s、Trainium＋AMD ≈ %s H100 等效。</b>三家合计 ≈ %s，Nvidia 占 %s。<span class="cf">〔中〕</span></li>' % (
            wan(nv), wan(tp), wan(ot), wan(tot), pct(nv / tot)),
        '<li><b>Rubin 在 Nvidia 到卡里从 %s起过半。</b>按 8 位算，9 月 %s、10 月 %s、11 月 %s，12 月 SemiAnalysis 预测的 11 月出货（%s 颗）到卡，占比到 %s；2027 年上半年在 %s–%s。<span class="cf">〔中〕</span></li>' % (
            ym(first), pct(rub['2026-09']), pct(rub['2026-10']), pct(rub['2026-11']), cnum(sh['r200']['2026-11']['units']), pct(rub[first]), pct(min(h1)), pct(max(h1))),
        '<li><b>按颗数和按算力，排序不一样。</b>2026 年四季度到卡，按颗数前三是 %s；按 8 位算力 %s 排第一（%s），%s 第二（%s）。2027 年一季度按颗数第二是 %s（%s颗），按 8 位算力第二是 %s（%s），%s 不进前五。2027 年二季度按颗数 Nvidia 只比 TPU 多 %s，按 8 位算力是它的 %.1f 倍。<span class="cf">〔中〕</span></li>' % (
            '、'.join('%s（%s颗）' % (NX[k], wan(u)) for k, u, _ in r4u[:3]), NX[r4h[0][0]], wan(r4h[0][2]), NX[r4h[1][0]], wan(r4h[1][2]),
            NX[r1u[1][0]], wan(r1u[1][1]), NX[r1h[1][0]], wan(r1h[1][2]), NX[r1u[1][0]],
            pct(q27['nvidia']['total']['units'] / q27['tpu']['total']['units'] - 1), q27['nvidia']['total']['h8'] / q27['tpu']['total']['h8']),
        '<li><b>按 4 位算，Nvidia 领先更多。</b>2026 年四季度到卡，按 8 位 Nvidia 是 TPU 的 %.1f 倍，按 4 位是 %.1f 倍：TPU v7 没有 FP4，B300 和 Rubin 的 4 位算力是 8 位的 2–3 倍。<span class="cf">〔中〕</span></li>' % (
            q4['nvidia']['total']['h8'] / q4['tpu']['total']['h8'], q4['nvidia']['total']['h4'] / q4['tpu']['total']['h4']),
    ]
    kv = [
        ('到卡时滞', 'Rubin、Rubin Ultra：出货后 1 个月；Blackwell、Hopper：2 个月。出处：Nvidia 11 月 17 日财报会，大客户约 1 个月把 Rubin 投入生产，是 Grace Blackwell 的一半〔中〕。TPU 1 个月（Google 自家机房）、Trainium 1 个月、AMD 2 个月，都是假设〔低〕。对照：Epoch AI 自己假设从卖出到运行中位约 1 个季度。'),
        ('拆到月', '没有特别说明的季度，三个月平分。Rubin 2026 年下半年：以 Nvidia 2027 财年三季度（7/27–10/25）的 Epoch 合计 201,961 颗为锚，按爬坡分 7 月 2,000、8 月 46,500、9 月 68,700、10/1–10/25 84,761 颗；10 月再加 10/26–31 的 4 万颗〔低〕；11、12 月按 42%／58% 分四季度其余。Blackwell 和 Hopper 2026 年四季度：Epoch 的 10 月只算到 10/25，按 × 31/25 补满整月，11、12 月按 45%／55% 分其余。TPU v7、v8i 2026 年三季度：7 月取 Epoch 已有的数（到 8 月 2 日为止），8、9 月平分其余；v8t 8 月 30%、9 月 70%。TPU v7、v8i 2026 年四季度：按博通约 10 月 33 万、11–12 月 80 万颗分。Trainium 和 AMD 每季平分。'),
        ('出货数从哪来', '2025 年三季度到 2026 年三季度用 Epoch AI Chip Sales（2026-11-19 版，取中位数）；2026 年四季度起用 SemiAnalysis Accelerator Outlook（2026-11-13）；两家都没有的由本报告推算〔低〕，表 2-3 里浅色底的格。Epoch 把财季收入按天平均摊到日历季，所以 Rubin 爬坡被摊平；本报告把日历三季度改成 117,200 颗，差额 29,277 颗移到四季度，下半年合计不变（SemiAnalysis 三季度是 220,752 颗，不用）。SemiAnalysis 只给 Blackwell 合计，按 B200 10%／B300 90% 拆。'),
        ('不计入', '华为昇腾、寒武纪（中国国内供给，和这三家实验室的算力无关）；Nvidia H20 和 AMD MI308X（中国特供）；Meta MTIA、微软 Maia、OpenAI 自研芯片（量小或还没量产）；SemiAnalysis 表里每季 45 万颗的「Other Blackwell」（推测是 RTX Pro 这类非训练卡）。'),
        ('换算系数', '8 位＝稠密 FP8 或 INT8 取大 ÷ H100 的 1,979 TFLOPS，与 Epoch AI 一致。4 位＝稠密 FP4 ÷ 同一个分母，没有 FP4 的卡按 8 位算。Rubin 的 4 位取 NVFP4 训练算力 35 PF；Nvidia 另报的推理 50 PF 没有说明是不是稠密，不用。MI350X 和 MI355X 合并，按 MI355X 的 2.54 算（Epoch 给 MI350X 的是 2.33）。Rubin Ultra 按 Rubin × 2 假设〔低〕。'),
        ('TPU v8i 为什么不用 5.10', 'Google 只公布了 v8i 的 FP4 算力 10.1 PF，没有公布 8 位。Epoch AI 把这个 FP4 数当成 8 位，得到 5.10，等于把 v8i 的算力算成两倍。本报告按「8 位通常是 FP4 的一半」推算 8 位 ≈ 5.05 PF，系数 2.55〔低〕；4 位才用 5.10。v8t 同理：FP4 12.6 PF → 8 位系数 3.18、4 位 6.37。哪家做哪颗沿用 SemiAnalysis 和博通 9 月 2 日财报的说法：博通做 8i（Anthropic 2027 年的 5 GW 是 8i），联发科做 8t。代号（Sunfish／Zebrafish）各来源对不上，不影响按 8i／8t 的名字配系数。'),
    ]
    kvh = ''.join('<div class="kv-k">%s</div><div class="kv-v">%s</div>' % (k, v) for k, v in kv)
    intro = ('<p>这一节把各家芯片的出货量换算成「每月有多少算力真正到了机房」。做法分四步：先取按季的出货颗数（按封装算）；再拆到每个月；再按型号往后挪 1–2 个月，当作到卡并投入使用的时间；最后乘以「每颗折合几颗 H100」，得到 H100 等效。'
             '出货数到 2026 年 10 月以 Epoch AI（2026-11-19 版）为主，11 月起来自 SemiAnalysis（2026-11-13）的预测，两家都没有的由本报告推算。'
             '只算 Nvidia、Google TPU、AWS Trainium 和 AMD 卖进数据中心的训练和推理卡；华为、寒武纪和各家还没量产的自研芯片不计入。'
             '同样是「一颗卡」，算力能差几倍，所以图 2-1 和图 2-2 默认按 8 位算力画，也可以切到按 4 位算力或按颗数。</p>')
    return ('<h3 id="h23">2.3 算力到卡：建模与 H100 等效</h3>' + intro +
            '<ol class="key">' + ''.join(concl) + '</ol>' + f22() + f23() +
            '<div class="hints"><span>出货颗数 · 14 个型号 × 8 个日历季</span><span class="hint" data-tiph="%s">怎么读<i>?</i></span></div>' % A(
                '<b>怎么读</b>单位是封装颗数（一颗能单独插上的芯片）。<br>组标题那一行是这一组的合计。<br>浅色底＝本报告推算〔低〕；2026Q4 起 SemiAnalysis 的数是预测。<br>悬停每格看来源和可信度。') +
            t23() +
            '<p class="sg">假设清单</p><div class="kv">' + kvh + '</div>')

# ------------------------------------------------------------------ sources
SRC = [
    ('算力到卡（2.3 节）', [
        ('https://epoch.ai/data/ai-chip-sales', 'Epoch AI：AI Chip Sales 数据集', '2026-11-19 快照；2025Q3–2026Q3 出货颗数与 H100 等效，及 2026 年 10 月的 Nvidia 部分'),
        ('https://epoch.ai/data/ai-chip-sales-documentation/methodology', 'Epoch AI：AI Chip Sales 方法说明', 'H100 等效＝稠密 8 位算力 ÷ 1,979 TFLOPS；颗数按收入 ÷ 单价反推'),
        ('https://epoch.ai/data/ai_chip_sales_chip_types.csv', 'Epoch AI：chip types 表（CSV）', 'H100、TPU v6e、Trainium2、MI300X 的系数'),
        ('https://epoch.ai/data/ai-chip-users-documentation/methodology', 'Epoch AI：AI Chip Users 方法说明', '从卖出到运行中位约 1 个季度'),
        (None, 'SemiAnalysis：Accelerator Outlook（2026-11-13，付费研报，本地文件）', '2026Q4–2027Q2 Nvidia、博通、联发科、AMD 需求表（第 10–14 页）'),
        (None, 'UBS：亚洲半导体 2026 · Nvidia 出货量与亚洲产业链（2026-05-25，本地研报）', '交叉核对 Nvidia 出货'),
        (None, 'J.P. Morgan：TSMC CoWoS and advanced back-end updates（2026-04-08，本地研报）', 'Trainium3 2026 年约 130 万颗、2027 年约 310 万颗'),
        ('https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript', 'Nvidia FY27 第三季财报会文字稿', 'Rubin 约 1 个月投入生产，是 Grace Blackwell 的一半'),
        ('https://www.nvidia.com/en-us/data-center/gb200-nvl72/', 'Nvidia：GB200 NVL72 规格页', '每颗 5 PF FP8 / 10 PF FP4（稠密）'),
        ('https://www.nvidia.com/en-us/data-center/gb300-nvl72/', 'Nvidia：GB300 NVL72 规格页', '每颗 5 PF FP8 / 15 PF FP4（稠密）'),
        ('https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72.md', 'Nvidia：Vera Rubin NVL72 规格页', '每颗 17.5 PF FP8 / 35 PF NVFP4（训练）'),
        ('https://www.nvidia.com/en-us/data-center/hgx/', 'Nvidia：HGX 规格页', 'B200 / B300 的稀疏与稠密算力'),
        ('https://docs.cloud.google.com/tpu/docs/tpu7x', 'Google Cloud：TPU7x（Ironwood）文档', '4,614 TFLOPS FP8'),
        ('https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive', 'Google Cloud Blog：TPU 8t and TPU 8i technical deep dive（2026-04-22）', 'v8i 10.1 PF FP4、v8t 12.6 PF FP4'),
        ('https://aws.amazon.com/ai/machine-learning/trainium/', 'AWS：Trainium 页面', 'Trainium3 2.52 PF MXFP8'),
        ('https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html', 'AMD：Instinct MI355X 产品页', '5 PF FP8 / 10 PF FP4'),
        ('https://www.amd.com/en/products/accelerators/instinct/mi400/mi455x.html', 'AMD：Instinct MI455X 产品页', '20.1 PF FP8 / 40.3 PF FP4'),
    ])]
def sources():
    out = []
    for title, items in SRC:
        lis = []
        for url, name, note in items:
            a = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (A(url), html.escape(name))) if url else '<span>%s</span>' % html.escape(name)
            lis.append('<li>%s<span class="sw2">%s</span></li>' % (a, html.escape(note)))
        out.append('<p class="sg">%s</p><ol class="src">%s</ol>' % (title, ''.join(lis)))
    return ''.join(out)

# ------------------------------------------------------------------ CSS
def css():
    keys = ORDER + ['other']
    v_l = ''.join('--c-%s:%s;' % (k, col(k, 'l')) for k in ORDER)
    v_d = ''.join('--c-%s:%s;' % (k, col(k, 'd')) for k in ORDER)
    lane_l = RAMPS['lane_l']; lane_d = RAMPS['lane_d']
    spot = ',\n'.join('figure[data-hl=%s] [data-key]:not([data-key~=%s])' % (k, k) for k in keys) + '{opacity:.3}\n'
    spot += ',\n'.join('figure[data-hl=%s] .li[data-key~=%s]' % (k, k) for k in keys) + '{background:var(--hover);color:var(--ink)}\n'
    spot += ',\n'.join('figure[data-hl=%s] .sg[data-key~=%s]' % (k, k) for k in ORDER) + '{outline:1px solid var(--ink);outline-offset:-1px}\n'
    return '''<style id="compute-css">
/* 算力到卡：图 2-1 到卡三行、图 2-2、图 2-3、表 2-3（由 compute/build.py 生成） */
:root{--n:%s;--ot:%s;%s--hatch:rgba(255,255,255,.62)}
:root[data-theme=dark]{--n:%s;--ot:%s;%s--hatch:rgba(26,26,25,.62)}
%s
.k-other{background:var(--ot)}
.sg,.sw[class*=" c-"],.cbar{background-color:var(--sc)}
.sg.ht,.cbar.ht,.htl{background-image:repeating-linear-gradient(135deg,var(--hatch) 0 1.5px,transparent 1.5px 5px)}
/* timeline: sticky top scale row + date label + magnet */
.hl-lab.ax.top,.hl-axis.top{position:sticky;top:var(--thTop);z-index:6;background:var(--bg);border-bottom:1px solid var(--line);height:20px}
.hl-axis.top .mt{top:2px}
.hl-date{position:absolute;top:1px;left:0;width:84px;height:17px;line-height:17px;text-align:center;font-weight:650;font-size:12px;font-style:normal;background:var(--ink);color:var(--bg);display:none;font-variant-numeric:tabular-nums;z-index:1}
.hl-date.snap{background:var(--accent)}
.hl-cur{top:20px}
.hl-cur.snap{border-left-color:var(--accent)}
.hl-cur b{display:none}
.pin:not(.rng):hover{outline:1px solid var(--ink3);outline-offset:0;background:var(--soft)}
.pin.snap:not(:hover) .pd{transform:scale(1.3);box-shadow:0 0 0 3px color-mix(in srgb,var(--vc) 38%%,transparent)}
.pin.mu.snap:not(:hover) .pd{box-shadow:inset 0 0 0 1.5px var(--vc),0 0 0 3px color-mix(in srgb,var(--vc) 38%%,transparent)}
.pin.snap:not(:hover) .pl{background:color-mix(in srgb,var(--vc) 14%%,transparent)}
/* arrival lanes */
.hl-lab.cmpl{overflow:clip;display:block;padding:0}
.hl-lab.cmpl .lab-in{position:sticky;top:calc(var(--thTop) + 21px);display:flex;flex-wrap:wrap;align-items:center;padding:4px 4px 2px 2px}
.hl-lab.cmpl .ln{flex-basis:100%%;font-size:12px;margin-top:1px}
.hl-lab.cmpl small{margin-top:1px;white-space:nowrap}
.hl-track.cmp .vl{z-index:1;pointer-events:none}
.cbars{position:absolute;left:0;right:0;bottom:0;height:56px;pointer-events:none}
.mb{position:absolute;bottom:0;height:41px;pointer-events:none}
.stk{position:absolute;left:0;right:0;top:0;bottom:0}
.stk .sg{position:absolute;left:0;right:0;display:block;box-shadow:inset 0 1px 0 var(--bg);pointer-events:auto;cursor:help}
.stk .sg:hover{outline:1px solid var(--ink);outline-offset:-1px}
.stk .tot{position:absolute;left:-2px;right:-2px;text-align:center;font-size:12px;line-height:13px;margin-bottom:1px;color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap;pointer-events:auto;cursor:help;font-weight:650}
.legend .cbl{display:inline-block;width:12px;height:14px;margin-right:6px;background:linear-gradient(var(--c-r200) 0 45%%,var(--bg) 45%% 52%%,var(--c-b300) 52%%)}
.legend .htl{display:inline-block;width:14px;height:12px;margin-right:6px;background-color:var(--ink3)}
.msw{display:inline-flex;border:1px solid var(--line);margin-left:auto;order:9;font-size:12px}
.msw button{padding:0 8px;height:20px;line-height:20px;color:var(--ink2);border-left:1px solid var(--line)}
.msw button:first-child{border-left:0}
.msw button.on{background:var(--ink);color:var(--bg)}
.msw button:not(.on):hover{background:var(--hover);color:var(--ink)}
/* fig 2-2 */
.cmpfig .legend{align-items:center}
.lg-grp{display:inline-flex;flex-wrap:wrap;align-items:center;gap:0 2px}
.lg-grp .lg-h{font-weight:650;color:var(--ink)}
.qc{display:grid;grid-template-columns:44px minmax(0,1fr);grid-template-rows:auto 240px auto;margin-top:2px}
.qc-y{position:relative;grid-row:2;font-size:12px;color:var(--ink3);font-variant-numeric:tabular-nums}
.qc-y i{position:absolute;right:6px;transform:translateY(50%%);font-style:normal;line-height:12px}
.qc-plot{position:relative;grid-row:2;display:flex;border-bottom:1px solid var(--ink3);border-left:1px solid var(--line)}
.qc-grid{position:absolute;inset:0;pointer-events:none}
.qc-grid i{position:absolute;left:0;right:0;border-top:1px solid var(--grid)}
.qg{position:relative;flex:1;display:flex;gap:3px;padding:0 5px;min-width:0}
.qb{position:relative;flex:1;min-width:0}
.qc-unit{grid-row:1;grid-column:1 / span 2;font-size:12px;color:var(--ink3);line-height:1.3;padding:0 0 8px}
.qc-x{grid-row:3;grid-column:2;display:flex}
.qx{flex:1;min-width:0;display:flex;flex-direction:column;align-items:stretch;font-size:12px;line-height:1.45;text-align:center;padding:0 5px}
.qln{display:flex;gap:3px;color:var(--ink3)}
.qln i{flex:1;min-width:0;font-style:normal;cursor:help;white-space:nowrap;text-align:center;display:flex;justify-content:center}
.qc.stag .qln{padding-bottom:1.45em}
.qc.stag .qln i:nth-child(2){transform:translateY(1.45em)}
.qq{font-weight:650;color:var(--ink);font-variant-numeric:tabular-nums}
.qt{color:var(--ink2);font-variant-numeric:tabular-nums;white-space:nowrap;cursor:help}
/* fig 2-3 */
.cg{display:grid;grid-template-columns:max-content minmax(0,1fr) max-content;column-gap:10px}
.cr{grid-column:1 / -1;display:grid;grid-template-columns:subgrid;align-items:center;height:24px;padding:0 4px;font-size:13px;line-height:20px}
.cr .cn{white-space:nowrap;cursor:help}
.cr .ct{position:relative;height:20px;background-repeat:repeat-x;background-size:calc(100%% / 36 * 5) 100%%;background-image:linear-gradient(to right,var(--grid) 1px,transparent 1px)}
.cr .cbar{position:absolute;left:0;height:9px;display:block;cursor:help}
.cr .cbar.b8{top:0}
.cr .cbar.f4{top:11px;opacity:.5;box-shadow:inset 0 0 0 1px var(--sc)}
.cr .cv{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink2)}
.cr .cv b{color:var(--ink);font-weight:650}
.cr .cv small{margin-left:4px;color:var(--ink3);font-size:12px}
.cr.em{background:var(--hl)}
.cr.em .cn{font-weight:700}
.cr[data-key]:hover{background:var(--hover)}
.cr.em[data-key]:hover{background:color-mix(in srgb,var(--hl) 100%%,var(--hover))}
.cr.hd{height:20px;position:sticky;top:var(--thTop);z-index:3;background:var(--bg);border-bottom:1px solid var(--line);color:var(--ink3);font-size:12px}
.cr.hd .ct{background:none;height:18px}
.cr.hd .ticks{position:absolute;inset:0}
.legend .rnote{padding:0 8px;border-left:3px solid var(--c-r200);background:var(--soft);color:var(--ink);cursor:help}
.legend .c8l,.legend .c4l{display:inline-block;width:18px;height:9px;margin-right:6px;background:var(--c-b300)}
.legend .c4l{opacity:.5;box-shadow:inset 0 0 0 1px var(--c-b300)}
/* table 2-3 */
#t23 td.est{background:color-mix(in srgb,var(--ink) 6%%,transparent);color:var(--ink2)}
#t23 tr.grp td{font-weight:650}
#t23 tr.grp td.num{color:var(--ink2)}
#t23 .sw{vertical-align:-1px}
/* key-value list */
.kv{display:grid;grid-template-columns:9.5em minmax(0,1fr);border-top:1px solid var(--line);margin:4px 0 8px;font-size:.93em;line-height:1.75}
.kv-k,.kv-v{padding:5px 8px;border-bottom:1px solid var(--line)}
.kv-k{font-weight:650;color:var(--ink2);background:var(--soft)}
%s
@media print{.hl-lab.ax.top,.hl-axis.top,.cr.hd,.hl-lab.cmpl .lab-in{position:static}}
</style>''' % (lane_l[0], lane_l[2], v_l, lane_d[0], lane_d[2], v_d,
               ''.join('.c-%s{--sc:var(--c-%s)}' % (k, k) for k in ORDER), spot)

# ------------------------------------------------------------------ JS
JS_TERMS = r'''
Object.assign(TERMS,{
 h100e:{n:'H100 等效（H100e）',d:'把不同芯片的算力折算成「相当于多少颗 Nvidia H100」。算法是一颗卡的稠密算力 ÷ H100 的稠密 FP8 算力（1,979 TFLOPS）。好处是 Nvidia、TPU、Trainium、AMD 能加在一起比；它只看峰值算力，不看显存、带宽和实际用上了多少。'},
 dense:{n:'稠密算力（dense）',d:'芯片不跳过任何计算时的峰值算力。厂商常报的「稀疏」算力假设一半的数是零、可以跳过，数值是稠密的 2 倍。本报告一律用稠密，不然各家没法比。'},
 fp8:{n:'FP8（8 位浮点数）',d:'用 8 个二进制位存一个数。位数少，算得更快、更省电，精度够大模型训练和推理用。本报告「按 8 位算力」就是按每颗卡的稠密 FP8（或 INT8）算力换算，和 Epoch AI 的做法一样。'},
 int8:{n:'INT8（8 位整数）',d:'用 8 个二进制位存一个整数，主要用于推理。有的芯片 INT8 比 FP8 快，换算时两者取大。'},
 fp4:{n:'FP4（4 位浮点数）',d:'只用 4 个二进制位存一个数。精度更低，但同一颗芯片的算力能再翻一倍左右，主要用于推理。Blackwell 以后的 Nvidia 卡、AMD MI355X 以后的卡和 TPU v8 支持；H100、TPU v7 和 Trainium 不支持。'},
 nvfp4:{n:'NVFP4',d:'Nvidia 自己定义的 4 位格式，Blackwell 和 Rubin 支持。Rubin 训练用 NVFP4 是 35 PF，推理另报 50 PF。'},
 mxfp8:{n:'MXFP8',d:'一种业界通用的 8 位格式（OCP 标准），AWS Trainium3 用它报算力。'},
 arrive:{n:'到卡',d:'芯片出货以后，装进机柜、运到机房、通电调试，直到能跑训练或推理任务。本报告按出货后 1–2 个月算：Rubin、TPU、Trainium 1 个月，Blackwell、Hopper、AMD 2 个月。'},
 nvl72:{n:'NVL72',d:'Nvidia 的整柜产品：一个机柜里 72 颗 GPU 用高速线连成一体，像一台大机器。GB200、GB300 和 Vera Rubin 都有 NVL72 版本。'},
 pkg:{n:'封装（package）',d:'一颗能单独装上主板的芯片成品。Blackwell 和 Rubin 一个封装里有 2 块裸片，所以 Nvidia 说的「GPU 数」有时按裸片算，是封装数的 2 倍。本报告的颗数一律按封装算。'},
 tflops:{n:'TFLOPS / PF',d:'算力单位。TFLOPS＝每秒一万亿次运算；PF（PFLOPS）＝每秒一千万亿次，1 PF＝1,000 TFLOPS。'},
 epoch:{n:'Epoch AI',d:'研究 AI 发展趋势的非营利机构。它的 AI Chip Sales 数据集按季估算各家 AI 芯片卖了多少颗：用财报里的收入除以单价反推。本报告用的是 2026-11-19 版。'},
 semi:{n:'SemiAnalysis',d:'半导体与 AI 基础设施研究机构，报告收费。它的 Accelerator Outlook（2026-11-13）给出各家加速卡按季的出货预测，本报告 2026 年四季度以后的出货数主要来自这里。'},
 h100:{n:'H100',d:'Nvidia 2022 年发布的数据中心 GPU，是这一轮 AI 算力的基准卡。「H100 等效」就是拿它当一个单位。H200 算力和它一样，只是显存更大。'},
 bw:{n:'Blackwell',d:'Nvidia 2024–2026 年的主力 GPU 系列，包括 B200、B300，以及它们的整柜版 GB200、GB300。按 8 位算力，一颗约等于 2.5 颗 H100。'},
 gb:{n:'GB200 / GB300',d:'Blackwell 的整柜版本：一块板上 1 颗 Grace CPU 配 2 颗 B200（或 B300）GPU，装成 NVL72 机柜。GB300 的 4 位算力比 GB200 高一半，8 位一样。'},
 rubin:{n:'Vera Rubin（R200）',d:'Nvidia 接替 Blackwell 的新一代数据中心 GPU，2026 年 8 月全面量产。按 8 位算力一颗约等于 8.8 颗 H100、3.5 颗 GB300。Rubin Ultra 是 2027 年的加强版。'},
 tpu:{n:'TPU（Tensor Processing Unit）',d:'Google 自己设计的 AI 芯片，由博通和联发科协助设计、台积电生产，主要给 Google 自己和 Anthropic 用。v7 叫 Ironwood，v8 分训练用的 8t 和推理用的 8i。'},
 trn:{n:'Trainium',d:'AWS 自己设计的 AI 芯片，Anthropic 是最大用户。Trainium2 按 8 位算力约等于 0.66 颗 H100，Trainium3 约 1.27 颗。'}
});
Object.assign(ALIAS,{'H100 等效':'h100e','稠密算力':'dense','稠密':'dense','FP8':'fp8','8 位':'fp8','INT8':'int8','FP4':'fp4','4 位':'fp4','NVFP4':'nvfp4','MXFP8':'mxfp8',
 '到卡':'arrive','NVL72':'nvl72','封装':'pkg','TFLOPS':'tflops','PF':'tflops','Epoch AI':'epoch','SemiAnalysis':'semi','H100':'h100','Blackwell':'bw',
 'GB200':'gb','GB300':'gb','Vera Rubin':'rubin','Rubin Ultra':'rubin','Rubin':'rubin','TPU':'tpu','Trainium2':'trn','Trainium3':'trn','Trainium':'trn'});
'''

JS_FITPINS = "L.style.height=(Math.max(1,rowEnd.length)*ROWH+PADY*2+(L.classList.contains('cmp')?56:0))+'px';"

JS_HOVER = r'''
/* ---- timeline: hover line; date in the sticky top row; magnet snap to nodes (all lanes) ---- */
$$('.hl',main).forEach(function(hl){
  var cur=$('.hl-cur',hl),lab=$('.hl-date',hl)||$('b',cur),t0=Date.parse(hl.getAttribute('data-t0')+'T00:00:00Z'),span=+hl.getAttribute('data-span'),
      raf=0,cx=0,ptrPin=null,shown=false,snapG=null,snapOn=false,lastTxt='',LW=84,SNAP=5;
  function p2(n){return (n<10?'0':'')+n}
  function ymd(ms){var d=new Date(ms);return d.getUTCFullYear()+'-'+p2(d.getUTCMonth()+1)+'-'+p2(d.getUTCDate())}
  /* nodes: the dot centre sits on style.left (flipped pins too) -> sorted table, binary search, no geometry in the move frame */
  var groups=[],byPos={};
  $$('.pin:not(.rng)',hl).forEach(function(p){
    var x=parseFloat(p.style.left);if(isNaN(x))return;
    var k=x.toFixed(3),g=byPos[k];
    if(!g){
      var s=p.getAttribute('data-d')||p.getAttribute('data-tip')||'',m=s.match(/^\d{4}-\d{2}-\d{2}/),mm=s.match(/^约\s*\d{4}-\d{2}/);
      g=byPos[k]={x:x,els:[],d:m?m[0]:(mm?mm[0].replace(/\s+/,' '):ymd(t0+Math.round(x/100*span)*864e5))};groups.push(g);
    }
    g.els.push(p);p._g=g;
  });
  groups.sort(function(a,b){return a.x-b.x});
  function nearest(px){
    var lo=0,hi=groups.length-1,w=hlRect.w;if(hi<0)return null;
    while(lo<hi){var mid=(lo+hi)>>1;if(groups[mid].x/100*w<px)lo=mid+1;else hi=mid}
    var best=groups[lo],d=Math.abs(best.x/100*w-px);
    if(lo>0){var d2=Math.abs(groups[lo-1].x/100*w-px);if(d2<d){best=groups[lo-1];d=d2}}
    return d<=SNAP?best:null;
  }
  function setSnap(g,on){
    if(g===snapG&&on===snapOn)return;
    if(snapG&&snapOn)snapG.els.forEach(function(p){p.classList.remove('snap')});
    if(g&&on)g.els.forEach(function(p){p.classList.add('snap')});
    cur.classList.toggle('snap',!!on);lab.classList.toggle('snap',!!on);
    snapG=g;snapOn=on;
  }
  function hide(){if(shown){cur.style.display='none';lab.style.display='none';shown=false}setSnap(null,false)}
  function draw(){
    raf=0;
    if(!hlRect){var tr=$('.hl-track',hl).getBoundingClientRect(),hr=hl.getBoundingClientRect();hlRect={l:tr.left,w:tr.width,off:tr.left-hr.left}}
    var x=cx-hlRect.l;
    if(x<0||x>hlRect.w){hide();return}
    var g=ptrPin&&ptrPin._g?ptrPin._g:nearest(x),lx=g?g.x/100*hlRect.w:x;
    setSnap(g,!!g&&!ptrPin);
    var txt=g?g.d:ymd(t0+Math.round(x/hlRect.w*span)*864e5);
    if(txt!==lastTxt){lab.textContent=txt;lastTxt=txt}
    cur.style.transform='translateX('+Math.round(hlRect.off+lx)+'px)';
    lab.style.transform='translateX('+Math.round(Math.max(0,Math.min(hlRect.w-LW,lx-LW/2)))+'px)';
    if(!shown){cur.style.display='block';lab.style.display='block';shown=true}
  }
  hl.addEventListener('pointermove',function(e){cx=e.clientX;ptrPin=e.target.closest?e.target.closest('.pin:not(.rng)'):null;if(!raf)raf=requestAnimationFrame(draw)});
  hl.addEventListener('pointerleave',function(){if(raf){cancelAnimationFrame(raf);raf=0}ptrPin=null;hide()});
  W.addEventListener('scroll',function(){hlRect=null},{passive:true});
});
'''

JS_CMP = r'''
/* ---- compute: arrival bars (fig 2-1, 2-2) with a shared 8-bit / 4-bit / units switch ---- */
var cmp=(function(){
  var IDX={h8:0,h4:1,units:2},mode='h8',roots=$$('[data-cmax]',main);
  var UNIT={h8:'8 位 H100 等效',h4:'4 位 H100 等效',units:'封装颗数'},UNITQ={h8:'单位：万 H100 等效（8 位）',h4:'单位：万 H100 等效（4 位）',units:'单位：万颗'};
  try{var sv=localStorage.getItem('mdl-cmode');if(sv&&sv in IDX)mode=sv}catch(e){}
  function wan(v){var w=v/1e4;return w>=100?String(Math.round(w)):w.toFixed(1)}
  function tk(v,st){return st>=1e4?String(Math.round(v/1e4)):(v/1e4).toFixed(1)}
  function nice(mx){var raw=mx/4,p=Math.pow(10,Math.floor(Math.log10(raw))),f=raw/p,s=(f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p;return {step:s,top:Math.ceil(mx*1.06/s)*s}}
  function vals(el){return el._cv||(el._cv=el.getAttribute('data-cv').split(',').map(Number))}
  function apply(m){
    if(!(m in IDX))return;mode=m;var i=IDX[m],suf=m==='units'?' 万颗':' 万';
    roots.forEach(function(root){
      var mx=+root.getAttribute('data-cmax').split(',')[i],q=root.classList.contains('qc'),top=mx,ticks=null;
      if(q){var n=nice(mx);top=n.top;ticks=n}
      $$('.stk',root).forEach(function(stk){
        var cum=0,segs=stk.children;
        for(var j=0;j<segs.length;j++){var s=segs[j];if(!s.classList.contains('sg'))continue;var v=vals(s)[i];
          s.style.bottom=(cum/top*100)+'%';s.style.height=(v/top*100)+'%';cum+=v}
        var t=$('.tot',stk);if(t){t.style.bottom=(cum/top*100)+'%';t.textContent=wan(cum)+(q?'':suf)}
      });
      if(q){
        var g=$('.qc-grid',root),y=$('.qc-y',root),gh='',yh='';
        for(var v=0;v<=ticks.top+1e-9;v+=ticks.step){var p=(v/ticks.top*100).toFixed(3);gh+='<i style="bottom:'+p+'%"></i>';yh+='<i style="bottom:'+p+'%">'+tk(v,ticks.step)+'</i>'}
        g.innerHTML=gh;y.innerHTML=yh;
        $$('.qt',root).forEach(function(e){e.textContent='合计 '+wan(vals(e)[i])});
      }
    });
    $$('[data-cmsum]',main).forEach(function(e){e.textContent='6–11 月 ≈ '+wan(+e.getAttribute('data-cmsum').split(',')[i])+suf});
    $$('.cm-unit',main).forEach(function(e){e.textContent=e.classList.contains('qc-unit')?UNITQ[m]:UNIT[m]});
    $$('[data-cmode]',main).forEach(function(b){b.classList.toggle('on',b.getAttribute('data-cmode')===m)});
  }
  main.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('[data-cmode]');if(!b)return;
    var m=b.getAttribute('data-cmode');if(m===mode)return;
    hideTip();apply(m);try{localStorage.setItem('mdl-cmode',m)}catch(x){}
  });
  /* fig 2-2: lane names under bars; stagger the middle one when a name is wider than its bar */
  function fitQ(){
    $$('.qc',main).forEach(function(q){
      var ls=$$('.qln i',q),rg=D.createRange(),rs;q.classList.remove('stag');
      rs=ls.map(function(i){rg.selectNodeContents(i);return rg.getBoundingClientRect()});
      for(var j=0;j+1<rs.length;j++){if(rs[j].right+3>rs[j+1].left){q.classList.add('stag');break}}
    });
  }
  /* fig 2-1 bottom axis: "11/19 快照" must not collide with "11 月" */
  function fitSnap(){
    var el=$('#f21 .hl-axis:not(.top) .mt.vm');if(!el)return;
    if(el._t==null){el._t=el.textContent;el._tip=el.getAttribute('data-tip')||''}
    var prev=el.previousElementSibling,ax=el.parentNode;
    function bad(){var a=prev.getBoundingClientRect(),b=el.getBoundingClientRect(),c=ax.getBoundingClientRect();return b.left<a.right+4||b.right>c.right+1||b.left<c.left-1}
    el.textContent=el._t;el.classList.add('fl');el.setAttribute('data-tip',el._tip);
    if(!bad())return;
    el.classList.remove('fl');if(!bad())return;
    el.textContent='快照';el.setAttribute('data-tip','2026-11-19：本报告的快照日期。');el.classList.add('fl');
    if(bad())el.classList.remove('fl');
  }
  apply(mode);
  return {apply:apply,mode:function(){return mode},fit:function(){fitQ();fitSnap()}};
})();
var relayout0=relayout;
relayout=function(){relayout0();cmp.fit()};
W.__cmp=cmp;
'''

# ------------------------------------------------------------------ splice
def region(name, js=False):
    if js: return '/*<!--compute:%s:start-->*/' % name, '/*<!--compute:%s:end-->*/' % name
    return '<!--compute:%s:start-->' % name, '<!--compute:%s:end-->' % name

def put(src, name, content, first, js=False):
    st, en = region(name, js)
    block = st + content + en
    if st in src:
        a = src.index(st); b = src.index(en, a) + len(en)
        assert src.count(st) == 1, name
        return src[:a] + block + src[b:]
    return first(src, block)

def at_once(src, anchor):
    n = src.count(anchor); assert n == 1, ('anchor count', n, anchor[:80]); return src.index(anchor)
def insert_before(anchor):
    def f(src, block): i = at_once(src, anchor); return src[:i] + block + src[i:]
    return f
def insert_after(anchor):
    def f(src, block): i = at_once(src, anchor) + len(anchor); return src[:i] + block + src[i:]
    return f
def replace_span(start_anchor, end_anchor, keep_end=True):
    def f(src, block):
        a = at_once(src, start_anchor); b = src.index(end_anchor, a)
        if not keep_end: b += len(end_anchor)
        return src[:a] + block + src[b:]
    return f
def replace_exact(old):
    def f(src, block): i = at_once(src, old); return src[:i] + block + src[i + len(old):]
    return f

src = open(REPORT, encoding='utf-8').read()
before = src
src = put(src, 'css', css(), insert_before('</head>'))
src = put(src, 'f21hints', F21_HINTS, replace_span('<span class="hint" data-tiph="&lt;b&gt;怎么读&lt;/b&gt;方块的左右位置', '算力行<i>?</i></span>', keep_end=False))
src = put(src, 'f21legend', f21_legend(), replace_exact('<span class="li2"><i class="qb"></i>实线框：一个财季的出货</span>'))
src = put(src, 'hltop', f21_top(), insert_after('<div class="hl" data-t0="2026-06-01" data-span="182">'))
src = put(src, 'lanes', f21_lanes(), replace_span('<div class="hl-lab li sep" data-key="nvidia"', '<div class="hl-lab ax"></div>'))
src = put(src, 's23', s23(), insert_before('</section>\n\n<section class="sec" id="s3">'))
def src_first(s, block):
    a = at_once(s, '<section class="sec collapsed" id="s5">'); b = s.index('</section>', a); return s[:b] + block + s[b:]
src = put(src, 'src', sources(), src_first)
src = put(src, 'terms', JS_TERMS, insert_after("'METR':'metr'};"), js=True)
src = put(src, 'fitpins', JS_FITPINS, replace_exact("L.style.height=(Math.max(1,rowEnd.length)*ROWH+PADY*2)+'px';"), js=True)
src = put(src, 'hover', JS_HOVER, replace_span('/* ---- timeline hover line: date under the cursor ---- */', '/* ---- legend / mark spotlight ---- */'), js=True)
src = put(src, 'cjs', JS_CMP, insert_before('/* ---- init (keep at the very end) ---- */'), js=True)
open(REPORT, 'w', encoding='utf-8').write(src)
print('wrote', REPORT, len(before), '->', len(src), 'bytes', '(unchanged)' if src == before else '')
