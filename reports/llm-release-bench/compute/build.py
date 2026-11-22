#!/usr/bin/env python3
"""把 compute/model.json 写进报告 HTML（图 2-1 到卡三行、2.3 节、术语、来源）。
幂等：每块内容包在 <!--compute:NAME:start--> … <!--compute:NAME:end--> 里（JS / CSS 里写成 /*<!--…-->*/）。
标记必须已在报告里（第一次插入的锚点逻辑保留在下面，只在标记缺失时用）；之后只替换标记之间的内容。重复跑结果逐字节一致。
双语：所有文字都写成 L('中文', 'English')，输出规则见 ../bilingual.py；页面按 :root[data-lang] 显示其一。
横轴：由 ../data/models.json 的 meta.snapshot 推导（bilingual.axis，与 build_tables.py 同一个函数），不写死日期。
用法：python3 build.py [报告路径] [--data 数据目录]   默认报告＝上一级目录里的正式报告，数据＝../data/。
"""
import html, json, os, re, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from bilingual import Bi, L, bi, get, by, join, TX, BLOCK, att, esc, axis, month_label, month_range, MONTH_EN, report_missing

REPORT_NAME = '大模型发布和 Bench 跟进：前沿 Gemini Claude ChatGPT 大厂 Grok Muse 开源 DeepSeek Kimi GLM.html'
args = sys.argv[1:]
DATA = os.path.join(ROOT, 'data')
if '--data' in args:
    i = args.index('--data'); DATA = args[i + 1]; del args[i:i + 2]
REPORT = args[0] if args else os.path.join(ROOT, REPORT_NAME)
M = json.load(open(os.path.join(HERE, 'model.json'), encoding='utf-8'))
RAMPS = json.load(open(os.path.join(HERE, 'ramps.json'), encoding='utf-8'))
SNAP = json.load(open(os.path.join(DATA, 'models.json'), encoding='utf-8'))['meta']['snapshot']

def A(s):  # attribute escape
    return html.escape(s, quote=True)
def E(x): return bi(x).map(html.escape)      # 文字转义（Bi）

SK = {s['key']: s for s in M['skus']}
ORDER = [s['key'] for s in M['skus']]           # 堆叠顺序：自下而上＝老到新
LANES = [l['key'] for l in M['lanes']]
LANE_NAME = {l['key']: bi(l['name']) for l in M['lanes']}
LANE_KEY = {'nvidia': 'nvidia', 'tpu': 'google', 'other': 'other'}   # 与报告已有的聚光键对齐
SHORT = {'hopper': 'H100/H200', 'b200': 'B200', 'b300': 'B300', 'r200': 'Rubin', 'rubin_ultra': 'Rubin Ultra',
         'tpu_v6e': 'v6e', 'tpu_v7': 'v7', 'tpu_v8i': 'v8i', 'tpu_v8t': 'v8t',
         'trn2': 'Trn2', 'trn3': 'Trn3', 'mi300': 'MI300', 'mi355': 'MI355', 'mi450': 'MI450'}
NX = dict(SHORT, tpu_v6e='TPU v6e', tpu_v7='TPU v7', tpu_v8i='TPU v8i', tpu_v8t='TPU v8t', trn2='Trainium2', trn3='Trainium3')
def NAME(k): return bi(SK[k]['name'])
def BASIS(k): return bi(SK[k]['basis'])
# 颜色：Nvidia 石墨灰、TPU 与 Google 同一蓝色系（2026-11-22 起跟随 Google 官方蓝 #4285F4，色阶同色相）、Trainium＋AMD 品红；型号按代际由浅到深（深色主题由暗到亮）。
# 已过 dataviz 校验：各色阶 ordinal 两种主题全过（TPU 新色阶同样全过）。
RAMP_IDX = {'hopper': ('nv', 0), 'b200': ('nv', 1), 'b300': ('nv', 2), 'r200': ('nv', 3), 'rubin_ultra': ('nv', 4),
            'tpu_v6e': ('tpu', 0), 'tpu_v7': ('tpu', 1), 'tpu_v8i': ('tpu', 2), 'tpu_v8t': ('tpu', 3),
            'trn2': ('trn', 0), 'trn3': ('trn', 1), 'mi300': ('amd', 0), 'mi355': ('amd', 1), 'mi450': ('amd', 2)}
def col(k, mode):
    r, i = RAMP_IDX[k]; return RAMPS['%s_%s' % (r, mode)][i]

MODES = ('h8', 'h4', 'units')
# ---- 数字写法：中文用「万」，英文用 K / M（$20B、4.3M units 这类英文习惯）
def wan(v, unit=True):
    w = v / 1e4
    s = ('%d' % round(w)) if w >= 100 else ('%.1f' % w)
    return s + (' 万' if unit else '')
def en_num(v):
    """英文金额式写法：≥1M → 4.36M / 12.6M；否则 523K。"""
    if v >= 999500 or round(v / 1e3) >= 1000:
        m = v / 1e6; return ('%.1fM' % m) if m >= 10 else ('%.2fM' % m)
    if v >= 1e3: return '%dK' % round(v / 1e3)
    return '%d' % round(v)
def en_m(v):
    """英文、单位已在轴上写明为 M 时：12.6 / 4.37 / 0.30"""
    m = v / 1e6; return ('%.1f' % m) if m >= 10 else ('%.2f' % m)
def amt(v): return Bi(wan(v), en_num(v))                 # 带单位：436 万 / 4.36M
def amt_n(v): return Bi(wan(v, False), en_m(v))          # 不带单位（图 2-2 柱顶）：436 / 4.36
def cnum(n):
    return format(int(round(n)), ',')
def coef(x):
    return ('%.2f' % x).rstrip('0').rstrip('.') if x < 10 else ('%.1f' % x if x * 10 % 1 == 0 else '%.2f' % x)
def coefs(x):
    return '%.2f' % x
def nobr(s):
    return s[:-4] if s.endswith('<br>') else s
def ym(m):
    return Bi('%s 年 %d 月' % (m[:4], int(m[5:])), '%s %s' % (MONTH_EN[int(m[5:]) - 1], m[:4]))
def cf(c):   # 可信度标记
    return Bi('〔%s〕' % c, ' [%s]' % {'高': 'high', '中': 'medium', '低': 'low'}[c])
CONF = {'高': Bi('高', 'high'), '中': Bi('中', 'medium'), '低': Bi('低', 'low')}

# ---- 横轴（与 build_tables.py 共用 bilingual.axis）
T0D, SPAN, MONTHS = axis(SNAP)
T0 = T0D.isoformat()
def daypct(d):
    b = dt.date.fromisoformat(d)
    return (b - T0D).days / SPAN * 100
WIN = ['%d-%02d' % (d.year, d.month) for d in MONTHS]
WINLAB = month_range(MONTHS[0].month, MONTHS[-1].month)       # 6–11 月 / Jun–Nov
MON = {r['month']: r for r in M['arrive_monthly']}
for m in WIN: assert m in MON, ('model.json 的到卡月份不覆盖横轴', m)
def lane_total(m, ln, mode): return MON[m]['lanes'][ln]['total'][mode]
FIG1_MAX = {md: max(lane_total(m, ln, md) for m in WIN for ln in LANES) for md in MODES}
LANE_SUM = {ln: {md: sum(lane_total(m, ln, md) for m in WIN) for md in MODES} for ln in LANES}
KIND_TXT = {'epoch': L('Epoch AI 估算', 'Epoch AI estimate'), 'sa': L('SemiAnalysis 估算', 'SemiAnalysis estimate'),
            'forecast': L('SemiAnalysis 预测', 'SemiAnalysis forecast'), 'est': L('本报告推算', 'our estimate')}
WARN = []

def seg_tip(sg, am):
    k = sg['sku']; s = SK[k]
    lag = s['lag']
    t = (L('<b>%s · %s到卡</b>', '<b>%s · arrivals, %s</b>') % (E(NAME(k)), ym(am)) +
         L('对应出货月：%s（出货后约 %d 个月投入使用）%.0s<br>', 'Shipped: %s (in service about %d month%s after shipment)<br>') % (ym(sg['ship_month']), lag, Bi('', 's' if lag > 1 else '')) +
         L('颗数：%s 颗<br>', 'Units: %s<br>') % cnum(sg['units']) +
         L('每颗折合：%s 颗 H100（8 位）／%s 颗（4 位）<br>', 'Per unit: %s H100 (8-bit) / %s (4-bit)<br>') % (coefs(s['f8']), coefs(s['f4'])) +
         L('合计：%s（8 位）／%s（4 位）H100 等效<br>', 'Total: %s (8-bit) / %s (4-bit) H100e<br>') % (amt(sg['h8']), amt(sg['h4'])) +
         L('出货数来源：%s〔%s〕<br>换算系数：%s〔%s〕', 'Shipment source: %s [%s]<br>Conversion factor: %s [%s]') % (E(sg['src']), CONF[sg['conf']], E(BASIS(k)), CONF[s['conf']]))
    if sg['hatch']:
        t += L('<br>斜线＝这一段是预测或推算。', '<br>Hatched = forecast or estimate.')
    return t

def stack_html(segs, am, cls='stk', tot_tip=''):
    """一根堆叠柱：段按 ORDER 自下而上；高度由 JS 按当前换算方式写入（这里先写 8 位的值，无 JS 也能看）。"""
    out = []
    for sg in sorted(segs, key=lambda x: ORDER.index(x['sku'])):
        k = sg['sku']
        out.append('<i class="sg c-%s%s" data-key="%s %s" data-cv="%d,%d,%d"%s></i>' % (
            k, ' ht' if sg['hatch'] else '', k, LANE_KEY[SK[k]['lane']], sg['h8'], sg['h4'], sg['units'], att('data-tiph', seg_tip(sg, am))))
    return out

# ------------------------------------------------------------------ fig 2-1 lanes
# 算力泳道上的事件节点（日期决定位置；落在横轴外的不画）
PIN_EVENTS = {
    'nvidia': [('2026-08-26', 'nvidia',
                L('2026-08-26 Nvidia 财报：Rubin 进入全面量产，机柜已在 CoreWeave、Google Cloud、Microsoft Azure、Oracle、Nebius 运行。〔高〕',
                  '2026-08-26 Nvidia earnings: Rubin is in full production, with racks running at CoreWeave, Google Cloud, Microsoft Azure, Oracle and Nebius. [high]'),
                L('机柜已在 5 家云上运行', 'Racks live on 5 clouds')),
               ('2026-11-17', 'nvidia',
                L('2026-11-17 Nvidia 财报：Oracle 和 Google Cloud 已对外提供 Rubin 实例；SpaceXSI 的机柜即将上线；Anthropic 通过云厂商拿到更多 Blackwell 和 Rubin 算力。大客户约 1 个月就能把 Rubin 投入生产，是 Grace Blackwell 的一半。〔高〕',
                  '2026-11-17 Nvidia earnings: Oracle and Google Cloud now offer Rubin instances; SpaceXSI racks are about to come online; Anthropic is getting more Blackwell and Rubin capacity through cloud providers. Large customers put Rubin into production in about 1 month, half the time Grace Blackwell took. [high]'),
                L('财报：NVL72 已出货', 'Earnings: NVL72 shipping'))],
    'tpu': [('2026-09-02', 'google',
             L('2026-09-02 博通财报：给 Anthropic 和 Google 的 Ironwood 已大批量出货；给 Google 的 TPU 8i 开始量产出货；下一财季加快给 Anthropic 的 Ironwood 出货。Anthropic 的部署计划：2026 年 1 GW（Ironwood），2027 年再加 5 GW（TPU 8i），2028 年再加 10 GW。这是管理层预期。〔中〕',
               '2026-09-02 Broadcom earnings: Ironwood is shipping in volume to Anthropic and Google; TPU 8i volume shipments to Google have begun; Ironwood shipments to Anthropic accelerate next quarter. Anthropic\'s deployment plan: 1 GW in 2026 (Ironwood), another 5 GW in 2027 (TPU 8i), another 10 GW in 2028. Management expectations. [medium]'),
             L('博通财报：v8i 开始出货 · Anthropic 今年 1 GW', 'Broadcom: v8i ships · Anthropic 1 GW'))],
    'other': [],
}
def f21_lanes():
    ml = ''.join('<i class="ml" style="left:%.3f%%"></i>' % daypct(d.isoformat()) for d in MONTHS[1:]) + '<i class="vl" style="left:%.3f%%"></i>' % daypct(SNAP)
    PINS = {}
    for ln, evs in PIN_EVENTS.items():
        PINS[ln] = []
        for d, key, tip, lab in evs:
            p = daypct(d)
            if not 0 <= p <= 100: WARN.append('算力泳道节点 %s 在横轴之外，不画' % d); continue
            md = dt.date.fromisoformat(d)
            PINS[ln].append('<span class="pin" data-key="%s" style="left:%.3f%%"%s><i class="pd"></i><span class="pl noterm"><small>%d/%d</small> %s</span></span>' % (
                key, p, att('data-tip', tip), md.month, md.day, TX(lab)))
    LAB_TIP = {
        'nvidia': L('Nvidia 每月到卡的算力，按型号分段：H100/H200、B200、B300、Rubin。上面一行是事件。悬停一段看颗数和来源；悬停这里只看 Nvidia。',
                    'Nvidia compute arriving each month, segmented by model: H100/H200, B200, B300, Rubin. The row above holds events. Hover a segment for units and source; hover here to show Nvidia only.'),
        'tpu': L('Google TPU 每月到卡的算力，按型号分段：v6e、v7（Ironwood）、v8i、v8t。上面一行是事件。悬停这里只看 Google。',
                 'Google TPU compute arriving each month, segmented by model: v6e, v7 (Ironwood), v8i, v8t. The row above holds events. Hover here to show Google only.'),
        'other': L('AWS Trainium 与 AMD Instinct 每月到卡的算力，按型号分段：Trainium2、Trainium3、MI300、MI355、MI450。悬停这里只看这一行。',
                   'AWS Trainium and AMD Instinct compute arriving each month, segmented by model: Trainium2, Trainium3, MI300, MI355, MI450. Hover here to show this row only.'),
    }
    SW = {'nvidia': 'k-nvidia', 'tpu': 'k-google', 'other': 'k-other'}
    h = []
    for i, ln in enumerate(LANES):
        sep = ' sep' if i == 0 else ''
        s = LANE_SUM[ln]
        h.append('<div class="hl-lab li cmpl%s" data-key="%s"%s><div class="lab-in"><span class="sw %s"></span>%s<span class="ln">%s</span>'
                 '<small data-cmsum="%d,%d,%d">%s</small><small class="cm-unit">%s</small></div></div>' % (
                     sep, LANE_KEY[ln], att('data-tip', LAB_TIP[ln]), SW[ln], TX(L('到卡', 'Arrivals')), TX(E(LANE_NAME[ln])), s['h8'], s['h4'], s['units'],
                     TX(L('%s ≈ %s', '%s ≈ %s') % (WINLAB, amt(s['h8']))), TX(L('8 位 H100 等效', '8-bit H100e'))))
        bars = []
        for j, m in enumerate(WIN):
            l0 = daypct(m + '-01')
            l1 = daypct(WIN[j + 1] + '-01') if j + 1 < len(WIN) else 100.0
            rec = MON[m]['lanes'][ln]
            tot = rec['total']
            rows = join('', [L('%s %s（8 位）<br>', '%s %s (8-bit)<br>') % (SHORT[sg['sku']], amt(sg['h8'])) for sg in sorted(rec['segs'], key=lambda x: -ORDER.index(x['sku'])) if sg['h8'] > 0])
            tip = (L('<b>%s · %s到卡合计</b>%s 颗；%s（8 位）／%s（4 位）H100 等效<br>%s', '<b>%s · total arrivals, %s</b>%s units; %s (8-bit) / %s (4-bit) H100e<br>%s') % (
                E(LANE_NAME[ln]), ym(m), cnum(tot['units']), amt(tot['h8']), amt(tot['h4']), rows)).map(nobr)
            bars.append('<div class="mb" style="left:calc(%.3f%% + 2px);width:calc(%.3f%% - 4px)"><div class="stk">%s<span class="tot"%s>%s</span></div></div>' % (
                l0, l1 - l0, ''.join(stack_html(rec['segs'], m)), att('data-tiph', tip), TX(amt(tot['h8']))))
        h.append('<div class="hl-track cmp%s" data-lane="cmp-%s">%s%s<div class="cbars" data-cmax="%d,%d,%d">%s</div></div>' % (sep, ln, ml, ''.join(PINS[ln]), FIG1_MAX['h8'], FIG1_MAX['h4'], FIG1_MAX['units'], ''.join(bars)))
    return ''.join(h)

def f21_top():
    ticks = ''.join('<i class="mt" style="left:%.3f%%">%s</i>' % (daypct(d.isoformat()), TX(month_label(d.month))) for d in MONTHS)
    return '<div class="hl-lab ax top"></div><div class="hl-axis top">%s<b class="hl-date" aria-hidden="true"></b></div>' % ticks

SWITCH = ('<span class="msw" role="group"%s>' % att('aria-label', L('换算方式', 'Conversion'), A) +
          '<button data-cmode="h8" class="on"%s>%s</button>' % (att('data-tip', L('每颗卡按稠密 8 位算力（FP8 或 INT8）折合几颗 H100。与 Epoch AI 的算法一致。',
                                                                                  'Each chip converted to H100s by dense 8-bit compute (FP8 or INT8). Same method as Epoch AI.')), TX(L('按 8 位算力', '8-bit compute'))) +
          '<button data-cmode="h4"%s>%s</button>' % (att('data-tip', L('每颗卡按稠密 4 位算力（FP4）折合几颗 H100；没有 FP4 的卡按 8 位算。分母仍是 H100 的 8 位算力，因为 H100 没有 FP4。看的是推理峰值。',
                                                                       'Each chip converted to H100s by dense 4-bit compute (FP4); chips without FP4 use 8-bit. The denominator is still H100 8-bit compute, since H100 has no FP4. This shows peak inference throughput.')), TX(L('按 4 位算力', '4-bit compute'))) +
          '<button data-cmode="units"%s>%s</button></span>' % (att('data-tip', L('不换算，直接数封装颗数。用来对照：颗数的排序和算力的排序不一样。',
                                                                                  'No conversion: count packages. Useful as a contrast, since ranking by units differs from ranking by compute.')), TX(L('按颗数', 'Units'))))

def f21_legend():
    return ('<span class="li2"><i class="cbl"></i><span>%s</span></span>' % TX(L('柱：每月到卡，按型号分段', 'Bars: monthly arrivals by model')) +
            '<span class="li2"><i class="htl"></i><span>%s</span></span>' % TX(L('斜线：预测或推算', 'Hatched: forecast or estimate')) + SWITCH)

def f21_hints():
    r8 = '%.1f' % (SK['r200']['f8'] / SK['b300']['f8']); r4 = '%.1f' % (SK['r200']['f4'] / SK['b300']['f4'])
    how = L('<b>怎么读</b>方块的左右位置就是日期；上下错开只是为了不重叠。<br>鼠标在图上移动，顶部刻度行读出日期；离节点 5 像素以内时，竖线和日期吸到节点上，同一天的节点一起放大。<br>内部代号模型画的是训练完成的时间段，时间来自 METR 的报告。<br>下面三行是每月到卡的算力：每月一根柱，按型号分段，柱顶是当月合计。三行用同一个纵轴，高度可以直接比。斜线段是预测或推算。',
            '<b>How to read</b>A marker\'s horizontal position is its date; vertical offsets only keep labels from overlapping.<br>Move the pointer across the chart and the sticky scale at the top reads out the date; within 5 px of a node, the line and date snap to it and every node on that day is enlarged.<br>Internal codenamed models are drawn as the period when training finished, taken from METR\'s report.<br>The three rows below show compute arriving each month: one bar per month, segmented by model, with the monthly total on top. All three rows share one vertical scale, so heights compare directly. Hatched segments are forecasts or estimates.')
    lane = L('<b>算力行：每月到卡多少 H100 等效</b>到卡＝出货后往后挪 1–2 个月：Rubin、TPU、Trainium 挪 1 个月，Blackwell、Hopper、AMD 挪 2 个月。Nvidia 11 月 17 日说，大客户约 1 个月就能把 Rubin 投入生产，是 Grace Blackwell 的一半。<br>H100 等效＝颗数 × 每颗折合几颗 H100。按 8 位算力：每颗卡的稠密 FP8（或 INT8）÷ H100 的 1,979 TFLOPS；按 4 位算力：稠密 FP4 ÷ 同一个分母。<br>Rubin 和 GB300 不能按颗数比：一颗 Rubin 按 8 位约等于 %s 颗 GB300，按 4 位约 %s 颗。<br>出货数：到 2026 年 10 月以 Epoch AI（2026-11-19 版）为主；Rubin 下半年以 Nvidia 财季（7/27–10/25）的 Epoch 合计为锚、按爬坡拆到月；11 月起的出货用 SemiAnalysis（2026-11-13）的预测，两家都没有的由本报告推算。做法与假设见 2.3 节。〔中〕',
             '<b>Compute rows: H100-equivalents arriving each month</b>Arrival = shipment shifted forward 1–2 months: 1 month for Rubin, TPU and Trainium; 2 months for Blackwell, Hopper and AMD. On Nov 17 Nvidia said large customers put Rubin into production in about 1 month, half the time Grace Blackwell took.<br>H100-equivalents = units × H100s per unit. 8-bit: each chip\'s dense FP8 (or INT8) ÷ the H100\'s 1,979 TFLOPS; 4-bit: dense FP4 ÷ the same denominator.<br>Rubin and GB300 cannot be compared unit for unit: one Rubin is about %s GB300s at 8-bit and about %s at 4-bit.<br>Shipments: through October 2026 mainly Epoch AI (2026-11-19 release); Rubin in the second half is anchored on Epoch\'s total for Nvidia\'s fiscal quarter (Jul 27–Oct 25) and spread by month along the ramp; shipments from November use SemiAnalysis forecasts (2026-11-13), and anything neither covers is our estimate. Method and assumptions in Section 2.3. [medium]') % (r8, r4)
    return ('<span class="hint"%s>%s<i>?</i></span><span class="hint"%s>%s<i>?</i></span>' % (
        att('data-tiph', how), TX(L('怎么读', 'How to read')), att('data-tiph', lane), TX(L('算力行', 'Compute rows'))))

# ------------------------------------------------------------------ fig 2-2 quarterly
Q = M['arrive_quarterly']
OTHER_TIP = L('其他＝AWS Trainium＋AMD', 'Other = AWS Trainium + AMD')
def f22():
    QMAX = {md: max(q['lanes'][ln]['total'][md] for q in Q for ln in LANES) for md in MODES}
    leg = []
    for ln in LANES:
        items = ''.join('<span class="li" data-key="%s %s"%s><i class="sw c-%s"></i>%s</span>' % (
            k, LANE_KEY[ln], att('data-tip', L('%s：每颗折合 %s 颗 H100（8 位）／%s 颗（4 位）。悬停只看这个型号。', '%s: %s H100 per unit (8-bit) / %s (4-bit). Hover to show this model only.') % (NAME(k), coefs(SK[k]['f8']), coefs(SK[k]['f4']))), k, html.escape(SHORT[k]))
            for k in ORDER if SK[k]['lane'] == ln)
        hname = L('其他（Trainium＋AMD）', 'Other (Trainium + AMD)') if ln == 'other' else LANE_NAME[ln]
        leg.append('<span class="lg-grp"><span class="li lg-h" data-key="%s"%s>%s</span>%s</span>' % (
            LANE_KEY[ln], att('data-tip', L('悬停只看 %s 这一组。', 'Hover to show the %s group only.') % LANE_NAME[ln]), TX(E(hname)), items))
    groups, xl = [], []
    for q in Q:
        bars = []
        for ln in LANES:
            rec = q['lanes'][ln]; tot = rec['total']
            segs = []
            for b in rec['segs']:
                s = SK[b['sku']]
                hatch_share = b['hatch_h8'] / b['h8'] if b['h8'] else 0
                kinds = join(L('、', ', '), [KIND_TXT[x] for x in b['kinds']])
                part = (L('；其中 %d%% 是预测或推算', '; %d%% of it is forecast or estimate') % round(hatch_share * 100)) if 0 < hatch_share < 1 else ''
                tip = L('<b>%s · %s到卡</b>对应出货月：%s<br>颗数：%s 颗<br>每颗折合：%s 颗 H100（8 位）／%s 颗（4 位）<br>合计：%s（8 位）／%s（4 位）H100 等效<br>出货数来源：%s%s<br>换算系数：%s〔%s〕',
                        '<b>%s · arrivals, %s</b>Shipped: %s<br>Units: %s<br>Per unit: %s H100 (8-bit) / %s (4-bit)<br>Total: %s (8-bit) / %s (4-bit) H100e<br>Shipment source: %s%s<br>Conversion factor: %s [%s]') % (
                    E(NAME(b['sku'])), q['quarter'], join(L('、', ', '), b['ship_months']), cnum(b['units']), coefs(s['f8']), coefs(s['f4']),
                    amt(b['h8']), amt(b['h4']), kinds, part, E(BASIS(b['sku'])), CONF[s['conf']])
                segs.append('<i class="sg c-%s%s" data-key="%s %s" data-cv="%d,%d,%d"%s></i>' % (
                    b['sku'], ' ht' if hatch_share >= 0.5 else '', b['sku'], LANE_KEY[ln], b['h8'], b['h4'], b['units'], att('data-tiph', tip)))
            rows = join('', [L('%s %s（8 位）<br>', '%s %s (8-bit)<br>') % (SHORT[b['sku']], amt(b['h8'])) for b in sorted(rec['segs'], key=lambda x: -ORDER.index(x['sku'])) if b['h8'] > 0])
            ttip = (L('<b>%s · %s到卡合计</b>%s 颗；%s（8 位）／%s（4 位）H100 等效<br>%s', '<b>%s · total arrivals, %s</b>%s units; %s (8-bit) / %s (4-bit) H100e<br>%s') % (
                E(LANE_NAME[ln]), q['quarter'], cnum(tot['units']), amt(tot['h8']), amt(tot['h4']), rows)).map(nobr)
            bars.append('<div class="qb"><div class="stk">%s<span class="tot"%s>%s</span></div></div>' % (''.join(segs), att('data-tiph', ttip), TX(amt_n(tot['h8']))))
        groups.append('<div class="qg">%s</div>' % ''.join(bars))
        t = q['total']
        xl.append('<div class="qx"><span class="qln"><i data-tip="Nvidia">Nvidia</i><i data-tip="Google TPU">TPU</i><i%s>%s</i></span>' % (att('data-tip', OTHER_TIP), TX(L('其他', 'Other'))) +
                  '<span class="qq">%s</span><span class="qt" data-cv="%d,%d,%d"%s>%s</span></div>' % (
                      q['quarter'], t['h8'], t['h4'], t['units'],
                      att('data-tip', L('%s 三条泳道合计到卡：%s 颗；%s（8 位）／%s（4 位）H100 等效。', '%s, all three rows: %s units arrived; %s (8-bit) / %s (4-bit) H100e.') % (q['quarter'], cnum(t['units']), amt(t['h8']), amt(t['h4']))),
                      TX(L('合计 %s', 'Total %s') % amt_n(t['h8']))))
    how = L('<b>怎么读</b>每季三根柱，从左到右：Nvidia、Google TPU、其他（＝AWS Trainium＋AMD）。每根按型号分段，柱顶是这一季到卡的合计，季度下面是三家合计。<br>到卡季度＝出货月往后挪 1–2 个月之后所在的季度。<br>2027 年两季全部是预测或推算。<br>图例悬停只看一个型号；用上面的按钮切换换算方式，图 2-1 同步切换。',
            '<b>How to read</b>Three bars per quarter, left to right: Nvidia, Google TPU, Other (= AWS Trainium + AMD). Each bar is segmented by model with the quarter\'s arrivals on top; the figure under each quarter is the three-row total.<br>Arrival quarter = the quarter a shipment lands in after shifting it forward 1–2 months.<br>Both 2027 quarters are entirely forecasts or estimates.<br>Hover the legend to isolate one model; the buttons above switch the conversion, and Fig 2-1 switches with it.')
    return ('<figure id="f22" class="cmpfig"%s>' % att('data-toc', L('图 2-2 按季到卡', 'Fig 2-2 Quarterly arrivals')) +
            '<figcaption>%s<span class="hint"%s>%s<i>?</i></span></figcaption>' % (TX(L('图 2-2　按季到卡：三家各多少 H100 等效（2025Q4–2027Q2）', 'Fig 2-2 Quarterly arrivals: H100-equivalents by supplier (2025Q4–2027Q2)')), att('data-tiph', how), TX(L('怎么读', 'How to read'))) +
            '<div class="legend">%s<span class="li2"><i class="htl"></i><span>%s</span></span>%s</div>' % (''.join(leg), TX(L('斜线：预测或推算', 'Hatched: forecast or estimate')), SWITCH) +
            '<div class="qc" data-cmax="%d,%d,%d"><div class="qc-unit cm-unit">%s</div><div class="qc-y"></div><div class="qc-plot"><div class="qc-grid"></div>%s</div><div class="qc-x">%s</div></div>' % (
                QMAX['h8'], QMAX['h4'], QMAX['units'], TX(L('单位：万 H100 等效（8 位）', 'Unit: million H100e (8-bit)')), ''.join(groups), ''.join(xl)) +
            '</figure>')

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
        tip8 = L('%s：按 8 位算力，每颗折合 %s 颗 H100。%s〔%s〕', '%s: %s H100 per unit at 8-bit. %s [%s]') % (NAME(k), coefs(s['f8']), BASIS(k), CONF[s['conf']])
        tip4 = L('%s：按 4 位算力，每颗折合 %s 颗 H100。%s', '%s: %s H100 per unit at 4-bit. %s') % (NAME(k), coefs(s['f4']), L('没有 FP4，按 8 位算。', 'No FP4, so 8-bit is used.') if nofp4 else BASIS(k) + (L('〔%s〕', ' [%s]') % CONF[s['conf']]))
        nm = NAME(k).replace(L('（含 Meta 定制）', ' (incl. Meta custom)'), L('', ''))
        out.append('<div class="cr%s" data-key="%s %s"><span class="cn noterm"%s><i class="sw c-%s"></i>%s</span>'
                   '<span class="ct"><span class="cbar b8 c-%s%s" style="width:%.2f%%"%s></span><span class="cbar f4 c-%s%s" style="width:%.2f%%"%s></span></span>'
                   '<span class="cv"><b>%s</b>%s%s%s</span></div>' % (
                       ' em' if em else '', k, LANE_KEY[s['lane']],
                       att('data-tip', L('%s · %s。时滞：出货后约 %d 个月到卡。%.0s', '%s · %s. Lag: arrives about %d month%s after shipment.') % (NAME(k), LANE_NAME[s['lane']], s['lag'], Bi('', 's' if s['lag'] > 1 else ''))),
                       k, TX(E(nm)),
                       k, ' ht' if est8 else '', s['f8'] / mx * 100, att('data-tip', tip8), k, ' ht' if est4 else '', s['f4'] / mx * 100, att('data-tip', tip4),
                       coefs(s['f8']), TX(L(' ／ ', ' / ')), coefs(s['f4']), ('<small>%s</small>' % TX(L('无 FP4', 'no FP4'))) if nofp4 else ''))
    ticks = ''.join('<i style="left:%.3f%%"%s>%d</i>' % (v / mx * 100, ' class="f"' if v == 0 else '', v) for v in range(0, 36, 5))
    how = L('<b>怎么读</b>每个型号一行两根条：上条按 8 位算力，下条按 4 位算力，单位是「折合几颗 H100」。<br>8 位＝稠密 FP8 或 INT8 取大，÷ H100 的 1,979 TFLOPS。4 位＝稠密 FP4，÷ 同一个分母；没有 FP4 的卡两根一样长。<br>GB300 和 Rubin 两行加了底色：同样是「一颗」，算力差 2–3.5 倍。<br>斜线：TPU v8i / v8t 的 8 位是按 FP4 ÷ 2 推算的；Rubin Ultra 两个系数都是按 Rubin × 2 假设的。',
            '<b>How to read</b>Two bars per model: the upper bar is 8-bit compute, the lower bar 4-bit, both in "H100s per unit".<br>8-bit = the larger of dense FP8 and INT8, ÷ the H100\'s 1,979 TFLOPS. 4-bit = dense FP4 ÷ the same denominator; chips without FP4 get two equal bars.<br>The GB300 and Rubin rows are shaded: both count as "one chip", yet compute differs by 2–3.5×.<br>Hatched: the TPU v8i / v8t 8-bit figures are estimated as FP4 ÷ 2; both Rubin Ultra factors assume Rubin × 2.')
    rtip = L('一颗 Rubin 按 8 位算力是 %s ÷ %s ≈ %.1f 颗 GB300，按 4 位是 %s ÷ %s ≈ %.1f 颗。只数颗数，会把一颗 Rubin 当成一颗 GB300。',
             'At 8-bit, one Rubin is %s ÷ %s ≈ %.1f GB300s; at 4-bit it is %s ÷ %s ≈ %.1f. Counting units alone treats one Rubin as one GB300.') % (coefs(SK['r200']['f8']), coefs(SK['b300']['f8']), ratio8, coefs(SK['r200']['f4']), coefs(SK['b300']['f4']), ratio4)
    return ('<figure id="f23" class="cmpfig"%s>' % att('data-toc', L('图 2-3 一颗卡折合几颗 H100', 'Fig 2-3 H100s per chip')) +
            '<figcaption>%s<span class="hint"%s>%s<i>?</i></span></figcaption>' % (TX(L('图 2-3　一颗卡折合几颗 H100（按 8 位算力排序）', 'Fig 2-3 How many H100s one chip is worth (sorted by 8-bit compute)')), att('data-tiph', how), TX(L('怎么读', 'How to read'))) +
            '<div class="legend"><span class="li2"><i class="c8l"></i><span>%s</span></span><span class="li2"><i class="c4l"></i><span>%s</span></span><span class="li2"><i class="htl"></i><span>%s</span></span>' % (
                TX(L('上条：按 8 位算力', 'Upper bar: 8-bit')), TX(L('下条：按 4 位算力', 'Lower bar: 4-bit')), TX(L('斜线：推算或假设的系数', 'Hatched: estimated or assumed factor'))) +
            '<span class="li2 rnote"%s><span>%s</span></span></div>' % (att('data-tip', rtip), TX(L('Rubin ≈ %.1f 个 GB300（8 位）／≈ %.1f 个（4 位）', 'Rubin ≈ %.1f GB300s (8-bit) / ≈ %.1f (4-bit)') % (ratio8, ratio4))) +
            '<div class="cg"><div class="cr hd"><span class="cn">%s</span><span class="ct"><span class="ticks">%s</span></span><span class="cv">%s</span></div>%s</div></figure>' % (
                TX(L('型号', 'Model')), ticks, TX(L('8 位 ／ 4 位', '8-bit / 4-bit')), ''.join(out)))

# ------------------------------------------------------------------ table 2-3
def t23():
    QS = M['quarters_ship']; ST = M['ship_quarterly']
    cols = '<col style="width:13.5em">' + ''.join('<col style="width:6.2em">' for _ in QS)
    th = '<th class="c0"%s>%s</th>' % (att('data-tip', L('型号，按泳道分组。组标题那一行是这一组的合计。', 'Model, grouped by row. The group heading row is the group total.')), TX(L('型号', 'Model'))) + ''.join(
        '<th class="num%s"%s>%s</th>' % (' gs' if i == 0 else '', att('data-tip', L('%s（日历季）出货的封装颗数。%s', 'Packages shipped in %s (calendar quarter). %s') % (q, L('这一季全部来自 Epoch AI。', 'All from Epoch AI this quarter.') if q < '2026Q3' else L('悬停每格看来源。', 'Hover each cell for its source.'))), q) for i, q in enumerate(QS))
    body = []
    for ln in LANES:
        tots = [sum(ST[k][q]['units'] for k in ORDER if SK[k]['lane'] == ln) for q in QS]
        body.append('<tr class="grp"><td class="c0"><span class="gl"><span class="sw %s"></span>%s</span></td>%s</tr>' % (
            {'nvidia': 'k-nvidia', 'tpu': 'k-google', 'other': 'k-other'}[ln], TX(E(LANE_NAME[ln])),
            ''.join('<td class="num%s">%s</td>' % (' gs' if i == 0 else '', cnum(t)) for i, t in enumerate(tots))))
        for k in ORDER:
            if SK[k]['lane'] != ln: continue
            tds = []
            for i, q in enumerate(QS):
                c = ST[k][q]; u = c['units']
                kind = c['src']
                lab = bi(c['label'])
                if kind == 'sa' and q >= '2026Q4': lab = L('SemiAnalysis Accelerator Outlook 预测（2026-11-13）', 'SemiAnalysis Accelerator Outlook forecast (2026-11-13)')
                tip = L('%s · %s：%s 颗。来源：%s〔%s〕。%s', '%s · %s: %s units. Source: %s [%s]. %s') % (NAME(k), q, cnum(u), lab, CONF[c['conf']], c['note'])
                cls = 'num' + (' gs' if i == 0 else '') + (' est' if kind == 'est' else '') + (' na' if u == 0 else '')
                tds.append('<td class="%s"%s>%s</td>' % (cls, att('data-tip', tip.map(str.strip)), cnum(u) if u else '—'))
            body.append('<tr><td class="c0 noterm"%s><span class="sw c-%s"></span>%s</td>%s</tr>' % (
                att('data-tip', L('%s：每颗折合 %s 颗 H100（8 位）／%s 颗（4 位）。', '%s: %s H100 per unit (8-bit) / %s (4-bit).') % (NAME(k), coefs(SK[k]['f8']), coefs(SK[k]['f4']))), k, TX(E(NAME(k))), ''.join(tds)))
    width = 13.5 + 6.2 * len(QS)
    return ('<div class="tblwrap wide" id="t23"%s><table style="width:%.1fem"><colgroup>%s</colgroup><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>') % (
        att('data-toc', L('表 2-3 按季出货颗数', 'Table 2-3 Quarterly shipments (units)')), width, cols, th, ''.join(body))

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
    CF = L('<span class="cf">〔中〕</span>', ' <span class="cf">[medium]</span>')
    def units(u): return L('%s颗', '%s units') % amt(u)
    concl = [
        L('<li><b>%s到卡（按 8 位算力）：Nvidia ≈ %s、TPU ≈ %s、Trainium＋AMD ≈ %s H100 等效。</b>三家合计 ≈ %s，Nvidia 占 %s。%s</li>',
          '<li><b>Arrivals %s (8-bit): Nvidia ≈ %s, TPU ≈ %s, Trainium + AMD ≈ %s H100e.</b> Combined ≈ %s, of which Nvidia is %s.%s</li>') % (
            WINLAB, amt(nv), amt(tp), amt(ot), amt(tot), pct(nv / tot), CF),
        L('<li><b>Rubin 在 Nvidia 到卡里从 %s起过半。</b>按 8 位算，9 月 %s、10 月 %s、11 月 %s，12 月 SemiAnalysis 预测的 11 月出货（%s 颗）到卡，占比到 %s；2027 年上半年在 %s–%s。%s</li>',
          '<li><b>Rubin passes half of Nvidia arrivals from %s.</b> At 8-bit its share is %s in September, %s in October and %s in November; in December, as the November shipments SemiAnalysis forecasts (%s units) arrive, it reaches %s; in the first half of 2027 it stays at %s–%s.%s</li>') % (
            ym(first), pct(rub['2026-09']), pct(rub['2026-10']), pct(rub['2026-11']), cnum(sh['r200']['2026-11']['units']), pct(rub[first]), pct(min(h1)), pct(max(h1)), CF),
        L('<li><b>按颗数和按算力，排序不一样。</b>2026 年四季度到卡，按颗数前三是 %s；按 8 位算力 %s 排第一（%s），%s 第二（%s）。2027 年一季度按颗数第二是 %s（%s），按 8 位算力第二是 %s（%s），%s 不进前五。2027 年二季度按颗数 Nvidia 只比 TPU 多 %s，按 8 位算力是它的 %.1f 倍。%s</li>',
          '<li><b>Ranking by units and ranking by compute disagree.</b> For 2026 Q4 arrivals, the top three by units are %s; by 8-bit compute %s ranks first (%s) and %s second (%s). In 2027 Q1, second place by units is %s (%s), while second by 8-bit compute is %s (%s) and %s misses the top five. In 2027 Q2 Nvidia has only %s more units than TPU, but %.1f× its 8-bit compute.%s</li>') % (
            join(L('、', ', '), [L('%s（%s）', '%s (%s)') % (NX[k], units(u)) for k, u, _ in r4u[:3]]), NX[r4h[0][0]], amt(r4h[0][2]), NX[r4h[1][0]], amt(r4h[1][2]),
            NX[r1u[1][0]], units(r1u[1][1]), NX[r1h[1][0]], amt(r1h[1][2]), NX[r1u[1][0]],
            pct(q27['nvidia']['total']['units'] / q27['tpu']['total']['units'] - 1), q27['nvidia']['total']['h8'] / q27['tpu']['total']['h8'], CF),
        L('<li><b>按 4 位算，Nvidia 领先更多。</b>2026 年四季度到卡，按 8 位 Nvidia 是 TPU 的 %.1f 倍，按 4 位是 %.1f 倍：TPU v7 没有 FP4，B300 和 Rubin 的 4 位算力是 8 位的 2–3 倍。%s</li>',
          '<li><b>At 4-bit, Nvidia\'s lead widens.</b> For 2026 Q4 arrivals Nvidia has %.1f× TPU at 8-bit and %.1f× at 4-bit: TPU v7 has no FP4, while B300 and Rubin deliver 2–3× as much at 4-bit as at 8-bit.%s</li>') % (
            q4['nvidia']['total']['h8'] / q4['tpu']['total']['h8'], q4['nvidia']['total']['h4'] / q4['tpu']['total']['h4'], CF),
    ]
    kv = [
        (L('到卡时滞', 'Arrival lag'), L('Rubin、Rubin Ultra：出货后 1 个月；Blackwell、Hopper：2 个月。出处：Nvidia 11 月 17 日财报会，大客户约 1 个月把 Rubin 投入生产，是 Grace Blackwell 的一半〔中〕。TPU 1 个月（Google 自家机房）、Trainium 1 个月、AMD 2 个月，都是假设〔低〕。对照：Epoch AI 自己假设从卖出到运行中位约 1 个季度。',
                                       'Rubin and Rubin Ultra: 1 month after shipment; Blackwell and Hopper: 2 months. Source: Nvidia\'s Nov 17 earnings call, where large customers put Rubin into production in about 1 month, half the time Grace Blackwell took [medium]. TPU 1 month (Google\'s own data centers), Trainium 1 month, AMD 2 months are all assumptions [low]. For comparison, Epoch AI itself assumes a median of about one quarter from sale to operation.')),
        (L('拆到月', 'Monthly split'), L('没有特别说明的季度，三个月平分。Rubin 2026 年下半年：以 Nvidia 2027 财年三季度（7/27–10/25）的 Epoch 合计 201,961 颗为锚，按爬坡分 7 月 2,000、8 月 46,500、9 月 68,700、10/1–10/25 84,761 颗；10 月再加 10/26–31 的 4 万颗〔低〕；11、12 月按 42%／58% 分四季度其余。Blackwell 和 Hopper 2026 年四季度：Epoch 的 10 月只算到 10/25，按 × 31/25 补满整月，11、12 月按 45%／55% 分其余。TPU v7、v8i 2026 年三季度：7 月取 Epoch 已有的数（到 8 月 2 日为止），8、9 月平分其余；v8t 8 月 30%、9 月 70%。TPU v7、v8i 2026 年四季度：按博通约 10 月 33 万、11–12 月 80 万颗分。Trainium 和 AMD 每季平分。',
                                     'Unless noted, a quarter is split evenly across its three months. Rubin, second half of 2026: anchored on Epoch\'s total of 201,961 units for Nvidia fiscal Q3 FY27 (Jul 27–Oct 25) and spread along the ramp as Jul 2,000, Aug 46,500, Sep 68,700 and Oct 1–25 84,761; October adds 40K for Oct 26–31 [low]; the rest of Q4 is split 42% / 58% across November and December. Blackwell and Hopper, 2026 Q4: Epoch\'s October stops at Oct 25, so it is scaled by 31/25 to a full month, and the rest is split 45% / 55% across November and December. TPU v7 and v8i, 2026 Q3: July takes Epoch\'s figure (through Aug 2) and August and September split the rest evenly; v8t is 30% August, 70% September. TPU v7 and v8i, 2026 Q4: split by Broadcom\'s roughly 330K in October and 800K in Nov–Dec. Trainium and AMD are split evenly within each quarter.')),
        (L('出货数从哪来', 'Where shipments come from'), L('2025 年三季度到 2026 年三季度用 Epoch AI Chip Sales（2026-11-19 版，取中位数）；2026 年四季度起用 SemiAnalysis Accelerator Outlook（2026-11-13）；两家都没有的由本报告推算〔低〕，表 2-3 里浅色底的格。Epoch 把财季收入按天平均摊到日历季，所以 Rubin 爬坡被摊平；本报告把日历三季度改成 117,200 颗，差额 29,277 颗移到四季度，下半年合计不变（SemiAnalysis 三季度是 220,752 颗，不用）。SemiAnalysis 只给 Blackwell 合计，按 B200 10%／B300 90% 拆。',
                                                    '2025 Q3 through 2026 Q3 use Epoch AI Chip Sales (2026-11-19 release, medians); from 2026 Q4, SemiAnalysis Accelerator Outlook (2026-11-13); anything neither covers is our estimate [low], shown as shaded cells in Table 2-3. Epoch spreads fiscal-quarter revenue evenly by day into calendar quarters, which flattens the Rubin ramp; we set calendar Q3 to 117,200 units and move the 29,277 difference into Q4, leaving the second-half total unchanged (SemiAnalysis has 220,752 for Q3; not used). SemiAnalysis gives only a Blackwell total, split 10% B200 / 90% B300.')),
        (L('不计入', 'Excluded'), L('华为昇腾、寒武纪（中国国内供给，和这三家实验室的算力无关）；Nvidia H20 和 AMD MI308X（中国特供）；Meta MTIA、微软 Maia、OpenAI 自研芯片（量小或还没量产）；SemiAnalysis 表里每季 45 万颗的「Other Blackwell」（推测是 RTX Pro 这类非训练卡）。',
                                  'Huawei Ascend and Cambricon (domestic China supply, unrelated to these three labs\' compute); Nvidia H20 and AMD MI308X (China-only parts); Meta MTIA, Microsoft Maia and OpenAI in-house chips (low volume or not yet in volume production); the 450K-a-quarter "Other Blackwell" line in SemiAnalysis\'s table (likely RTX Pro-class, non-training cards).')),
        (L('换算系数', 'Conversion factors'), L('8 位＝稠密 FP8 或 INT8 取大 ÷ H100 的 1,979 TFLOPS，与 Epoch AI 一致。4 位＝稠密 FP4 ÷ 同一个分母，没有 FP4 的卡按 8 位算。Rubin 的 4 位取 NVFP4 训练算力 35 PF；Nvidia 另报的推理 50 PF 没有说明是不是稠密，不用。MI350X 和 MI355X 合并，按 MI355X 的 2.54 算（Epoch 给 MI350X 的是 2.33）。Rubin Ultra 按 Rubin × 2 假设〔低〕。',
                                           '8-bit = the larger of dense FP8 and INT8 ÷ the H100\'s 1,979 TFLOPS, matching Epoch AI. 4-bit = dense FP4 ÷ the same denominator; chips without FP4 use 8-bit. Rubin\'s 4-bit uses the 35 PF NVFP4 training figure; the separate 50 PF inference figure is not stated as dense, so it is not used. MI350X and MI355X are combined at the MI355X factor of 2.54 (Epoch gives MI350X 2.33). Rubin Ultra assumes Rubin × 2 [low].')),
        (L('TPU v8i 为什么不用 5.10', 'Why TPU v8i is not 5.10'), L('Google 只公布了 v8i 的 FP4 算力 10.1 PF，没有公布 8 位。Epoch AI 把这个 FP4 数当成 8 位，得到 5.10，等于把 v8i 的算力算成两倍。本报告按「8 位通常是 FP4 的一半」推算 8 位 ≈ 5.05 PF，系数 2.55〔低〕；4 位才用 5.10。v8t 同理：FP4 12.6 PF → 8 位系数 3.18、4 位 6.37。哪家做哪颗沿用 SemiAnalysis 和博通 9 月 2 日财报的说法：博通做 8i（Anthropic 2027 年的 5 GW 是 8i），联发科做 8t。代号（Sunfish／Zebrafish）各来源对不上，不影响按 8i／8t 的名字配系数。',
                                                               'Google has published only v8i\'s FP4 compute, 10.1 PF, not its 8-bit figure. Epoch AI treats that FP4 number as 8-bit and gets 5.10, which doubles v8i\'s compute. We assume 8-bit is typically half of FP4, giving ≈ 5.05 PF at 8-bit and a factor of 2.55 [low]; 5.10 is used only at 4-bit. Same for v8t: 12.6 PF FP4 → 3.18 at 8-bit, 6.37 at 4-bit. Who builds which chip follows SemiAnalysis and Broadcom\'s Sep 2 earnings: Broadcom builds 8i (Anthropic\'s 5 GW in 2027 is 8i) and MediaTek builds 8t. The codenames (Sunfish / Zebrafish) are inconsistent across sources, which does not affect assigning factors by the 8i / 8t names.')),
    ]
    kvh = ''.join('<div class="kv-k">%s</div><div class="kv-v">%s</div>' % (TX(k), TX(v)) for k, v in kv)
    intro = L('这一节把各家芯片的出货量换算成「每月有多少算力真正到了机房」。做法分四步：先取按季的出货颗数（按封装算）；再拆到每个月；再按型号往后挪 1–2 个月，当作到卡并投入使用的时间；最后乘以「每颗折合几颗 H100」，得到 H100 等效。'
              '出货数到 2026 年 10 月以 Epoch AI（2026-11-19 版）为主，11 月起来自 SemiAnalysis（2026-11-13）的预测，两家都没有的由本报告推算。'
              '只算 Nvidia、Google TPU、AWS Trainium 和 AMD 卖进数据中心的训练和推理卡；华为、寒武纪和各家还没量产的自研芯片不计入。'
              '同样是「一颗卡」，算力能差几倍，所以图 2-1 和图 2-2 默认按 8 位算力画，也可以切到按 4 位算力或按颗数。',
              'This section converts each vendor\'s chip shipments into how much compute actually lands in data centers each month. Four steps: take quarterly shipments (counted in packages); split them into months; shift each model forward 1–2 months to when it arrives and enters service; then multiply by H100s per chip to get H100-equivalents. '
              'Shipments through October 2026 come mainly from Epoch AI (2026-11-19 release), from November on from SemiAnalysis forecasts (2026-11-13), and anything neither covers is our estimate. '
              'Only training and inference chips sold into data centers by Nvidia, Google TPU, AWS Trainium and AMD are counted; Huawei, Cambricon and in-house chips not yet in volume production are excluded. '
              'Since "one chip" can differ several-fold in compute, Figs 2-1 and 2-2 default to 8-bit compute and can switch to 4-bit compute or unit counts.')
    t23how = L('<b>怎么读</b>单位是封装颗数（一颗能单独插上的芯片）。<br>组标题那一行是这一组的合计。<br>浅色底＝本报告推算〔低〕；2026Q4 起 SemiAnalysis 的数是预测。<br>悬停每格看来源和可信度。',
               '<b>How to read</b>Units are packages (a chip that mounts on its own).<br>Group heading rows are group totals.<br>Shaded cells = our estimate [low]; SemiAnalysis figures from 2026Q4 on are forecasts.<br>Hover any cell for its source and confidence.')
    return ('<h3 id="h23">%s</h3>' % TX(L('2.3 算力到卡：建模与 H100 等效', '2.3 Compute arrivals: model and H100-equivalents')) +
            '<p>%s</p>' % TX(intro) +
            BLOCK('<ol class="key">%s</ol>' % ''.join(c.zh for c in concl), '<ol class="key">%s</ol>' % ''.join(c.en for c in concl)) + f22() + f23() +
            '<div class="hints"><span>%s</span><span class="hint"%s>%s<i>?</i></span></div>' % (
                TX(L('出货颗数 · 14 个型号 × 8 个日历季', 'Shipments in units · 14 models × 8 calendar quarters')), att('data-tiph', t23how), TX(L('怎么读', 'How to read'))) +
            t23() +
            '<p class="sg">%s</p><div class="kv">' % TX(L('假设清单', 'Assumptions')) + kvh + '</div>')

# ------------------------------------------------------------------ sources
SRC = [
    (L('算力到卡（2.3 节）', 'Compute arrivals (Section 2.3)'), [
        ('https://epoch.ai/data/ai-chip-sales', L('Epoch AI：AI Chip Sales 数据集', 'Epoch AI: AI Chip Sales dataset'), L('2026-11-19 快照；2025Q3–2026Q3 出货颗数与 H100 等效，及 2026 年 10 月的 Nvidia 部分', '2026-11-19 snapshot; 2025Q3–2026Q3 units and H100e, plus Nvidia\'s October 2026 portion')),
        ('https://epoch.ai/data/ai-chip-sales-documentation/methodology', L('Epoch AI：AI Chip Sales 方法说明', 'Epoch AI: AI Chip Sales methodology'), L('H100 等效＝稠密 8 位算力 ÷ 1,979 TFLOPS；颗数按收入 ÷ 单价反推', 'H100e = dense 8-bit compute ÷ 1,979 TFLOPS; units backed out as revenue ÷ unit price')),
        ('https://epoch.ai/data/ai_chip_sales_chip_types.csv', L('Epoch AI：chip types 表（CSV）', 'Epoch AI: chip types table (CSV)'), L('H100、TPU v6e、Trainium2、MI300X 的系数', 'Factors for H100, TPU v6e, Trainium2, MI300X')),
        ('https://epoch.ai/data/ai-chip-users-documentation/methodology', L('Epoch AI：AI Chip Users 方法说明', 'Epoch AI: AI Chip Users methodology'), L('从卖出到运行中位约 1 个季度', 'Median of about one quarter from sale to operation')),
        (None, L('SemiAnalysis：Accelerator Outlook（2026-11-13，付费研报，本地文件）', 'SemiAnalysis: Accelerator Outlook (2026-11-13; paid report, local copy)'), L('2026Q4–2027Q2 Nvidia、博通、联发科、AMD 需求表（第 10–14 页）', '2026Q4–2027Q2 demand tables for Nvidia, Broadcom, MediaTek, AMD (pp. 10–14)')),
        (None, L('UBS：亚洲半导体 2026 · Nvidia 出货量与亚洲产业链（2026-05-25，本地研报）', 'UBS: Asia Semiconductors 2026 · Nvidia shipments and the Asian supply chain (2026-05-25; local copy)'), L('交叉核对 Nvidia 出货', 'Cross-check of Nvidia shipments')),
        (None, L('J.P. Morgan：TSMC CoWoS and advanced back-end updates（2026-04-08，本地研报）', 'J.P. Morgan: TSMC CoWoS and advanced back-end updates (2026-04-08; local copy)'), L('Trainium3 2026 年约 130 万颗、2027 年约 310 万颗', 'Trainium3: about 1.3M units in 2026, about 3.1M in 2027')),
        ('https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript', L('Nvidia FY27 第三季财报会文字稿', 'Nvidia Q3 FY27 earnings call transcript'), L('Rubin 约 1 个月投入生产，是 Grace Blackwell 的一半', 'Rubin enters production in about 1 month, half of Grace Blackwell')),
        ('https://www.nvidia.com/en-us/data-center/gb200-nvl72/', L('Nvidia：GB200 NVL72 规格页', 'Nvidia: GB200 NVL72 specs'), L('每颗 5 PF FP8 / 10 PF FP4（稠密）', '5 PF FP8 / 10 PF FP4 per GPU (dense)')),
        ('https://www.nvidia.com/en-us/data-center/gb300-nvl72/', L('Nvidia：GB300 NVL72 规格页', 'Nvidia: GB300 NVL72 specs'), L('每颗 5 PF FP8 / 15 PF FP4（稠密）', '5 PF FP8 / 15 PF FP4 per GPU (dense)')),
        ('https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72.md', L('Nvidia：Vera Rubin NVL72 规格页', 'Nvidia: Vera Rubin NVL72 specs'), L('每颗 17.5 PF FP8 / 35 PF NVFP4（训练）', '17.5 PF FP8 / 35 PF NVFP4 (training) per GPU')),
        ('https://www.nvidia.com/en-us/data-center/hgx/', L('Nvidia：HGX 规格页', 'Nvidia: HGX specs'), L('B200 / B300 的稀疏与稠密算力', 'Sparse and dense compute for B200 / B300')),
        ('https://docs.cloud.google.com/tpu/docs/tpu7x', L('Google Cloud：TPU7x（Ironwood）文档', 'Google Cloud: TPU7x (Ironwood) docs'), L('4,614 TFLOPS FP8', '4,614 TFLOPS FP8')),
        ('https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive', L('Google Cloud Blog：TPU 8t and TPU 8i technical deep dive（2026-04-22）', 'Google Cloud Blog: TPU 8t and TPU 8i technical deep dive (2026-04-22)'), L('v8i 10.1 PF FP4、v8t 12.6 PF FP4', 'v8i 10.1 PF FP4, v8t 12.6 PF FP4')),
        ('https://aws.amazon.com/ai/machine-learning/trainium/', L('AWS：Trainium 页面', 'AWS: Trainium page'), L('Trainium3 2.52 PF MXFP8', 'Trainium3 2.52 PF MXFP8')),
        ('https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html', L('AMD：Instinct MI355X 产品页', 'AMD: Instinct MI355X product page'), L('5 PF FP8 / 10 PF FP4', '5 PF FP8 / 10 PF FP4')),
        ('https://www.amd.com/en/products/accelerators/instinct/mi400/mi455x.html', L('AMD：Instinct MI455X 产品页', 'AMD: Instinct MI455X product page'), L('20.1 PF FP8 / 40.3 PF FP4', '20.1 PF FP8 / 40.3 PF FP4')),
    ])]
def sources():
    def one(lang):
        out = []
        for title, items in SRC:
            lis = []
            for url, name, note in items:
                a = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (A(url), html.escape(get(name, lang)))) if url else '<span>%s</span>' % html.escape(get(name, lang))
                lis.append('<li>%s<span class="sw2">%s</span></li>' % (a, html.escape(get(note, lang))))
            out.append('<p class="sg">%s</p><ol class="src">%s</ol>' % (get(title, lang), ''.join(lis)))
        return ''.join(out)
    return BLOCK(one('zh'), one('en'))

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
# 术语（与报告 TERMS 合并）：n / d 中文，ne / de 英文；ALIAS 中文别名，ALIAS_EN 英文别名
C_TERMS = [
 ('h100e', L('H100 等效（H100e）', 'H100-equivalent (H100e)'),
  L('把不同芯片的算力折算成「相当于多少颗 Nvidia H100」。算法是一颗卡的稠密算力 ÷ H100 的稠密 FP8 算力（1,979 TFLOPS）。好处是 Nvidia、TPU、Trainium、AMD 能加在一起比；它只看峰值算力，不看显存、带宽和实际用上了多少。',
    'Expresses any chip\'s compute as "how many Nvidia H100s it is worth": the chip\'s dense compute ÷ the H100\'s dense FP8 compute (1,979 TFLOPS). It lets Nvidia, TPU, Trainium and AMD be added up and compared, but it reflects peak compute only, not memory, bandwidth or real utilization.')),
 ('dense', L('稠密算力（dense）', 'Dense compute'),
  L('芯片不跳过任何计算时的峰值算力。厂商常报的「稀疏」算力假设一半的数是零、可以跳过，数值是稠密的 2 倍。本报告一律用稠密，不然各家没法比。',
    'Peak compute when the chip skips no work. The "sparse" figures vendors often quote assume half the values are zero and can be skipped, so they are 2× the dense number. This report always uses dense; otherwise vendors cannot be compared.')),
 ('fp8', L('FP8（8 位浮点数）', 'FP8 (8-bit floating point)'),
  L('用 8 个二进制位存一个数。位数少，算得更快、更省电，精度够大模型训练和推理用。本报告「按 8 位算力」就是按每颗卡的稠密 FP8（或 INT8）算力换算，和 Epoch AI 的做法一样。',
    'Stores each number in 8 bits. Fewer bits mean faster, more power-efficient math, with enough precision for large-model training and inference. "8-bit compute" in this report converts each chip by its dense FP8 (or INT8) compute, the same approach as Epoch AI.')),
 ('int8', L('INT8（8 位整数）', 'INT8 (8-bit integer)'),
  L('用 8 个二进制位存一个整数，主要用于推理。有的芯片 INT8 比 FP8 快，换算时两者取大。',
    'Stores an integer in 8 bits, used mainly for inference. Some chips are faster at INT8 than FP8; the conversion takes whichever is larger.')),
 ('fp4', L('FP4（4 位浮点数）', 'FP4 (4-bit floating point)'),
  L('只用 4 个二进制位存一个数。精度更低，但同一颗芯片的算力能再翻一倍左右，主要用于推理。Blackwell 以后的 Nvidia 卡、AMD MI355X 以后的卡和 TPU v8 支持；H100、TPU v7 和 Trainium 不支持。',
    'Stores a number in just 4 bits. Precision is lower, but the same chip delivers roughly twice the compute, mainly for inference. Supported by Nvidia from Blackwell on, AMD from MI355X on and TPU v8; not by H100, TPU v7 or Trainium.')),
 ('nvfp4', L('NVFP4', 'NVFP4'),
  L('Nvidia 自己定义的 4 位格式，Blackwell 和 Rubin 支持。Rubin 训练用 NVFP4 是 35 PF，推理另报 50 PF。',
    'Nvidia\'s own 4-bit format, supported by Blackwell and Rubin. Rubin is rated 35 PF in NVFP4 for training, with a separate 50 PF figure for inference.')),
 ('mxfp8', L('MXFP8', 'MXFP8'),
  L('一种业界通用的 8 位格式（OCP 标准），AWS Trainium3 用它报算力。',
    'An industry-standard 8-bit format (OCP spec); AWS quotes Trainium3 compute in it.')),
 ('arrive', L('到卡', 'Arrival'),
  L('芯片出货以后，装进机柜、运到机房、通电调试，直到能跑训练或推理任务。本报告按出货后 1–2 个月算：Rubin、TPU、Trainium 1 个月，Blackwell、Hopper、AMD 2 个月。',
    'After a chip ships it is racked, delivered to a data center and brought up until it can run training or inference. This report assumes 1–2 months after shipment: 1 month for Rubin, TPU and Trainium; 2 months for Blackwell, Hopper and AMD.')),
 ('nvl72', L('NVL72', 'NVL72'),
  L('Nvidia 的整柜产品：一个机柜里 72 颗 GPU 用高速线连成一体，像一台大机器。GB200、GB300 和 Vera Rubin 都有 NVL72 版本。',
    'Nvidia\'s rack-scale product: 72 GPUs in one rack linked by high-speed interconnect so they act like a single machine. GB200, GB300 and Vera Rubin all come in NVL72 form.')),
 ('pkg', L('封装（package）', 'Package'),
  L('一颗能单独装上主板的芯片成品。Blackwell 和 Rubin 一个封装里有 2 块裸片，所以 Nvidia 说的「GPU 数」有时按裸片算，是封装数的 2 倍。本报告的颗数一律按封装算。',
    'A finished chip that mounts on a board by itself. Blackwell and Rubin put 2 dies in one package, so Nvidia\'s "GPU" counts are sometimes per die, twice the package count. Unit counts in this report are always packages.')),
 ('tflops', L('TFLOPS / PF', 'TFLOPS / PF'),
  L('算力单位。TFLOPS＝每秒一万亿次运算；PF（PFLOPS）＝每秒一千万亿次，1 PF＝1,000 TFLOPS。',
    'Units of compute. TFLOPS = a trillion operations per second; PF (PFLOPS) = a quadrillion per second; 1 PF = 1,000 TFLOPS.')),
 ('epoch', L('Epoch AI', 'Epoch AI'),
  L('研究 AI 发展趋势的非营利机构。它的 AI Chip Sales 数据集按季估算各家 AI 芯片卖了多少颗：用财报里的收入除以单价反推。本报告用的是 2026-11-19 版。',
    'A nonprofit that tracks AI trends. Its AI Chip Sales dataset estimates quarterly AI chip unit sales by dividing reported revenue by unit price. This report uses the 2026-11-19 release.')),
 ('semi', L('SemiAnalysis', 'SemiAnalysis'),
  L('半导体与 AI 基础设施研究机构，报告收费。它的 Accelerator Outlook（2026-11-13）给出各家加速卡按季的出货预测，本报告 2026 年四季度以后的出货数主要来自这里。',
    'A paid research firm covering semiconductors and AI infrastructure. Its Accelerator Outlook (2026-11-13) forecasts quarterly accelerator shipments by vendor and is the main source for shipments from 2026 Q4 on.')),
 ('h100', L('H100', 'H100'),
  L('Nvidia 2022 年发布的数据中心 GPU，是这一轮 AI 算力的基准卡。「H100 等效」就是拿它当一个单位。H200 算力和它一样，只是显存更大。',
    'Nvidia\'s 2022 data-center GPU and the reference chip of this AI build-out; "H100-equivalent" uses it as the unit. H200 has the same compute with more memory.')),
 ('bw', L('Blackwell', 'Blackwell'),
  L('Nvidia 2024–2026 年的主力 GPU 系列，包括 B200、B300，以及它们的整柜版 GB200、GB300。按 8 位算力，一颗约等于 2.5 颗 H100。',
    'Nvidia\'s main GPU family for 2024–2026: B200, B300 and their rack-scale versions GB200 and GB300. At 8-bit, one is worth about 2.5 H100s.')),
 ('gb', L('GB200 / GB300', 'GB200 / GB300'),
  L('Blackwell 的整柜版本：一块板上 1 颗 Grace CPU 配 2 颗 B200（或 B300）GPU，装成 NVL72 机柜。GB300 的 4 位算力比 GB200 高一半，8 位一样。',
    'The rack-scale Blackwell versions: one Grace CPU paired with two B200 (or B300) GPUs per board, built into NVL72 racks. GB300 has 50% more 4-bit compute than GB200; 8-bit is the same.')),
 ('rubin', L('Vera Rubin（R200）', 'Vera Rubin (R200)'),
  L('Nvidia 接替 Blackwell 的新一代数据中心 GPU，2026 年 8 月全面量产。按 8 位算力一颗约等于 8.8 颗 H100、3.5 颗 GB300。Rubin Ultra 是 2027 年的加强版。',
    'Nvidia\'s successor to Blackwell, in full production since August 2026. At 8-bit, one is worth about 8.8 H100s or 3.5 GB300s. Rubin Ultra is the 2027 step-up.')),
 ('tpu', L('TPU（Tensor Processing Unit）', 'TPU (Tensor Processing Unit)'),
  L('Google 自己设计的 AI 芯片，由博通和联发科协助设计、台积电生产，主要给 Google 自己和 Anthropic 用。v7 叫 Ironwood，v8 分训练用的 8t 和推理用的 8i。',
    'Google\'s in-house AI chip, co-designed with Broadcom and MediaTek and made by TSMC, used mainly by Google itself and Anthropic. v7 is Ironwood; v8 splits into 8t for training and 8i for inference.')),
 ('trn', L('Trainium', 'Trainium'),
  L('AWS 自己设计的 AI 芯片，Anthropic 是最大用户。Trainium2 按 8 位算力约等于 0.66 颗 H100，Trainium3 约 1.27 颗。',
    'AWS\'s in-house AI chip; Anthropic is its largest user. At 8-bit, Trainium2 is worth about 0.66 H100 and Trainium3 about 1.27.')),
]
C_ALIAS = {'H100 等效': 'h100e', '稠密算力': 'dense', '稠密': 'dense', 'FP8': 'fp8', '8 位': 'fp8', 'INT8': 'int8', 'FP4': 'fp4', '4 位': 'fp4', 'NVFP4': 'nvfp4', 'MXFP8': 'mxfp8',
           '到卡': 'arrive', 'NVL72': 'nvl72', '封装': 'pkg', 'TFLOPS': 'tflops', 'PF': 'tflops', 'Epoch AI': 'epoch', 'SemiAnalysis': 'semi', 'H100': 'h100', 'Blackwell': 'bw',
           'GB200': 'gb', 'GB300': 'gb', 'Vera Rubin': 'rubin', 'Rubin Ultra': 'rubin', 'Rubin': 'rubin', 'TPU': 'tpu', 'Trainium2': 'trn', 'Trainium3': 'trn', 'Trainium': 'trn'}
C_ALIAS_EN = {'H100-equivalents': 'h100e', 'H100-equivalent': 'h100e', 'H100e': 'h100e', 'dense': 'dense', 'FP8': 'fp8', '8-bit': 'fp8', 'INT8': 'int8', 'FP4': 'fp4', '4-bit': 'fp4',
              'NVFP4': 'nvfp4', 'MXFP8': 'mxfp8', 'arrivals': 'arrive', 'NVL72': 'nvl72', 'packages': 'pkg', 'package': 'pkg', 'TFLOPS': 'tflops', 'PF': 'tflops', 'Epoch AI': 'epoch',
              'SemiAnalysis': 'semi', 'H100': 'h100', 'Blackwell': 'bw', 'GB200': 'gb', 'GB300': 'gb', 'Vera Rubin': 'rubin', 'Rubin Ultra': 'rubin', 'Rubin': 'rubin', 'TPU': 'tpu',
              'Trainium2': 'trn', 'Trainium3': 'trn', 'Trainium': 'trn'}
def js_str(s): return json.dumps(s, ensure_ascii=False)
JS_TERMS = ('\nObject.assign(TERMS,{\n' + ',\n'.join(' %s:{n:%s,d:%s,ne:%s,de:%s}' % (k, js_str(n.zh), js_str(d.zh), js_str(n.en), js_str(d.en)) for k, n, d in C_TERMS) +
            '\n});\nObject.assign(ALIAS,%s);\nObject.assign(ALIAS_EN,%s);\n' % (js_str(C_ALIAS), js_str(C_ALIAS_EN)))

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
/* ---- compute: arrival bars (fig 2-1, 2-2) with a shared 8-bit / 4-bit / units switch; text follows the page language ---- */
var cmp=(function(){
  var IDX={h8:0,h4:1,units:2},mode='h8',roots=$$('[data-cmax]',main);
  var TXT=%s;
  try{var sv=localStorage.getItem('mdl-cmode');if(sv&&sv in IDX)mode=sv}catch(e){}
  function wan(v){var w=v/1e4;return w>=100?String(Math.round(w)):w.toFixed(1)}
  function enM(v){var m=v/1e6;return m>=10?m.toFixed(1):m.toFixed(2)}
  function enN(v){if(v>=999500||Math.round(v/1e3)>=1000)return enM(v)+'M';if(v>=1e3)return Math.round(v/1e3)+'K';return String(Math.round(v))}
  function tk(v,st){return st>=1e4?String(Math.round(v/1e4)):(v/1e4).toFixed(1)}
  function tkE(v,st){var m=v/1e6;return st>=1e6?String(Math.round(m)):st>=1e5?m.toFixed(1):m.toFixed(2)}
  function nice(mx){var raw=mx/4,p=Math.pow(10,Math.floor(Math.log10(raw))),f=raw/p,s=(f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p;return {step:s,top:Math.ceil(mx*1.06/s)*s}}
  function vals(el){return el._cv||(el._cv=el.getAttribute('data-cv').split(',').map(Number))}
  function apply(m){
    if(!(m in IDX))return;mode=m;var i=IDX[m],en=LANG()==='en',T=TXT[en?'en':'zh'],suf=m==='units'?' 万颗':' 万';
    function full(v){return en?enN(v)+(m==='units'?' '+T.units:''):wan(v)+suf}
    roots.forEach(function(root){
      var mx=+root.getAttribute('data-cmax').split(',')[i],q=root.classList.contains('qc'),top=mx,ticks=null;
      if(q){var n=nice(mx);top=n.top;ticks=n}
      $$('.stk',root).forEach(function(stk){
        var cum=0,segs=stk.children;
        for(var j=0;j<segs.length;j++){var s=segs[j];if(!s.classList.contains('sg'))continue;var v=vals(s)[i];
          s.style.bottom=(cum/top*100)+'%%';s.style.height=(v/top*100)+'%%';cum+=v}
        var t=$('.tot',stk);if(t){t.style.bottom=(cum/top*100)+'%%';t.textContent=q?(en?enM(cum):wan(cum)):(en?enN(cum):wan(cum)+suf)}
      });
      if(q){
        var g=$('.qc-grid',root),y=$('.qc-y',root),gh='',yh='';
        for(var v=0;v<=ticks.top+1e-9;v+=ticks.step){var p=(v/ticks.top*100).toFixed(3);gh+='<i style="bottom:'+p+'%%"></i>';yh+='<i style="bottom:'+p+'%%">'+(en?tkE(v,ticks.step):tk(v,ticks.step))+'</i>'}
        g.innerHTML=gh;y.innerHTML=yh;
        $$('.qt',root).forEach(function(e){e.textContent=T.total+(en?enM(vals(e)[i]):wan(vals(e)[i]))});
      }
    });
    $$('[data-cmsum]',main).forEach(function(e){e.textContent=T.win+' ≈ '+full(+e.getAttribute('data-cmsum').split(',')[i])});
    $$('.cm-unit',main).forEach(function(e){e.textContent=e.classList.contains('qc-unit')?T.unitq[m]:T.unit[m]});
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
  /* timeline bottom axes (fig 2-1, 3-2): the snapshot label must not collide with the last month tick; fall back to the short label (data-short*) */
  function fitSnap(){$$('.hl .hl-axis:not(.top) .mt.vm',main).forEach(fitSnap1)}
  function fitSnap1(el){
    if(el._h==null){el._h=el.innerHTML;el._tip=el.getAttribute('data-tip')||'';el._tipe=el.getAttribute('data-tip-en')}
    var prev=el.previousElementSibling,ax=el.parentNode;
    function bad(){var a=prev.getBoundingClientRect(),b=el.getBoundingClientRect(),c=ax.getBoundingClientRect();return b.left<a.right+6||b.right>c.right+1||b.left<c.left-1}
    function setTip(z,e){el.setAttribute('data-tip',z);if(e!=null)el.setAttribute('data-tip-en',e);else el.removeAttribute('data-tip-en')}
    el.innerHTML=el._h;el.style.marginLeft='';el.classList.add('fl');setTip(el._tip,el._tipe);
    if(!bad())return;
    el.classList.remove('fl');if(!bad())return;
    el.textContent=attrL(el,'data-short');setTip(el.getAttribute('data-short-tip')||'',el.getAttribute('data-short-tip-en'));el.classList.add('fl');
    if(!bad())return;
    el.classList.remove('fl');if(!bad())return;
    /* the month label just before the snapshot runs past the snapshot line (snapshot early in its month): nudge right of that label */
    var a=prev.getBoundingClientRect(),b=el.getBoundingClientRect(),c=ax.getBoundingClientRect(),dx=a.right+6-b.left;
    if(dx>0&&b.right+dx<=c.right+1)el.style.marginLeft=dx+'px';
  }
  apply(mode);
  return {apply:apply,mode:function(){return mode},fit:function(){fitQ();fitSnap()}};
})();
var relayout0=relayout;
relayout=function(){relayout0();cmp.fit()};
W.__cmp=cmp;
''' % json.dumps({
    'zh': {'unit': {'h8': '8 位 H100 等效', 'h4': '4 位 H100 等效', 'units': '封装颗数'},
           'unitq': {'h8': '单位：万 H100 等效（8 位）', 'h4': '单位：万 H100 等效（4 位）', 'units': '单位：万颗'}, 'total': '合计 ', 'win': WINLAB.zh, 'units': '颗'},
    'en': {'unit': {'h8': '8-bit H100e', 'h4': '4-bit H100e', 'units': 'Packages'},
           'unitq': {'h8': 'Unit: million H100e (8-bit)', 'h4': 'Unit: million H100e (4-bit)', 'units': 'Unit: million packages'}, 'total': 'Total ', 'win': WINLAB.en, 'units': 'units'}},
    ensure_ascii=False)

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
src = put(src, 'f21hints', f21_hints(), replace_span('<span class="hint" data-tiph="&lt;b&gt;怎么读&lt;/b&gt;方块的左右位置', '算力行<i>?</i></span>', keep_end=False))
src = put(src, 'f21legend', f21_legend(), replace_exact('<span class="li2"><i class="qb"></i>实线框：一个财季的出货</span>'))
src = put(src, 'hltop', f21_top(), insert_after('<!--data:f21hl:end-->'))
src = put(src, 'lanes', f21_lanes(), replace_span('<div class="hl-lab li sep" data-key="nvidia"', '<div class="hl-lab ax"></div>'))
src = put(src, 's23', s23(), insert_before('</section>\n\n<section class="sec" id="s3">'))
def src_first(s, block):
    a = at_once(s, '<section class="sec collapsed" id="s5">'); b = s.index('</section>', a); return s[:b] + block + s[b:]
src = put(src, 'src', sources(), src_first)
src = put(src, 'terms', JS_TERMS, insert_after('/*<!--data:s-terms:end-->*/'), js=True)
src = put(src, 'fitpins', JS_FITPINS, replace_exact("L.style.height=(Math.max(1,rowEnd.length)*ROWH+PADY*2)+'px';"), js=True)
src = put(src, 'hover', JS_HOVER, replace_span('/* ---- timeline hover line: date under the cursor ---- */', '/* ---- legend / mark spotlight ---- */'), js=True)
src = put(src, 'cjs', JS_CMP, insert_before('/* ---- init (keep at the very end) ---- */'), js=True)
for w in WARN: print('提示：' + w)
report_missing()
if src != before: open(REPORT, 'w', encoding='utf-8').write(src)
print('wrote', REPORT, len(before), '->', len(src), 'bytes', '(unchanged)' if src == before else '')
