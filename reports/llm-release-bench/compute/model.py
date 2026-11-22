#!/usr/bin/env python3
"""算力到卡模型（按 compute/decisions.md 2026-11-22 裁定）。幂等：同样输入 → 同样的 model.json。
步骤：按季出货（日历季，封装颗数）→ 拆到月 → 按 SKU 时滞平移 → 每月到卡 × 三种换算（8 位 / 4 位 / 颗数）。
用法：python3 model.py   （在 compute/ 目录或任意目录均可）
"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
H100 = 1979  # H100 稠密 FP8 TFLOPS，三种换算的分母

# ---------- 1. SKU 与系数（decisions.md 第 1 节） ----------
# key, 泳道, 显示名, 8 位系数, 4 位系数, 可信度, 依据
SKUS = [
 ('hopper','nvidia','H100 / H200',1.00,1.00,'高','定义：H100 稠密 FP8 1,979 TFLOPS = 1'),
 ('b200','nvidia','B200 / GB200',2.53,5.05,'高','Nvidia 官方：GB200 每颗 5 PF FP8 / 10 PF FP4（稠密）'),
 ('b300','nvidia','B300 / GB300',2.53,7.58,'高','Nvidia 官方：GB300 每颗 5 PF FP8 / 15 PF FP4（稠密）'),
 ('r200','nvidia','Rubin（VR200）',8.84,17.69,'中','Nvidia 官方 + Epoch：17.5 PF FP8；4 位取 NVFP4 训练 35 PF。推理 50 PF 没有注明是否稠密，不用'),
 ('rubin_ultra','nvidia','Rubin Ultra',17.7,35.4,'低','假设：按 Rubin × 2'),
 ('tpu_v6e','tpu','TPU v6e（Trillium）',0.93,0.93,'中','Epoch AI chip types（0.93）'),
 ('tpu_v7','tpu','TPU v7（Ironwood）',2.33,2.33,'高','Google Cloud 文档：4,614 TFLOPS FP8；没有 FP4'),
 ('tpu_v8i','tpu','TPU v8i',2.55,5.10,'低','Google 只给 10.1 PF FP4；8 位按 FP4 ÷ 2 推算。Epoch 填的 5.10 是把 FP4 当成 8 位，不采用'),
 ('tpu_v8t','tpu','TPU v8t',3.18,6.37,'低','Google 只给 12.6 PF FP4；8 位按 FP4 ÷ 2 推算'),
 ('trn2','other','Trainium2',0.66,0.66,'中','Epoch AI chip types（0.66）'),
 ('trn3','other','Trainium3',1.27,1.27,'中','AWS：2.52 PF MXFP8；没有找到 FP4'),
 ('mi300','other','MI300X / MI325X',1.32,1.32,'中','Epoch AI chip types（1.32）'),
 ('mi355','other','MI350X / MI355X',2.54,5.05,'中','AMD 官方：MI355X 5 PF FP8 / 10 PF FP4'),
 ('mi450','other','MI450 / MI455X（含 Meta 定制）',10.16,20.4,'中','AMD 官方：MI455X 20.1 PF FP8 / 40.3 PF FP4'),
]
LANES = [('nvidia','Nvidia'),('tpu','TPU'),('other','Trainium＋AMD')]
LAG = {'hopper':2,'b200':2,'b300':2,'r200':1,'rubin_ultra':1,
       'tpu_v6e':1,'tpu_v7':1,'tpu_v8i':1,'tpu_v8t':1,'trn2':1,'trn3':1,'mi300':2,'mi355':2,'mi450':2}
LAG_NOTE = {2:'Blackwell / Hopper / AMD：出货后约 2 个月投入使用',1:'Rubin / TPU / Trainium：出货后约 1 个月投入使用'}

QS = ['2025Q3','2025Q4','2026Q1','2026Q2','2026Q3','2026Q4','2027Q1','2027Q2']
# ---------- 2. 按季出货（decisions.md 第 2 节；src: epoch / sa / est） ----------
E,S,X='epoch','sa','est'
def row(vals, srcs): return {q:{'units':v,'src':s} for q,v,s in zip(QS,vals,srcs)}
SHIP = {
 'hopper':row([127343,23391,0,19361,74310,100000,100000,50000],[E,E,E,E,E,S,S,S]),
 'b200':  row([346338,417922,347540,223383,134927,73450,33252,26248],[E,E,E,E,E,S,S,S]),
 'b300':  row([541916,743918,993133,1334389,1424701,661054,299268,236232],[E,E,E,E,E,S,S,S]),
 'r200':  row([0,0,0,0,117200,949277,1258280,1057880],[E,E,E,E,X,S,S,S]),   # 第二轮裁定 5.1：以 Nvidia FY27Q3 为锚按爬坡重排
 'rubin_ultra':row([0,0,0,0,0,0,0,250000],[E,E,E,E,E,S,S,S]),
 'tpu_v6e':row([734300,408357,155055,41792,0,0,0,0],[E,E,E,E,X,X,X,X]),
 'tpu_v7': row([51286,212828,334346,616658,820000,750000,300000,150000],[E,E,E,E,X,X,X,X]),
 'tpu_v8i':row([0,0,0,25654,120000,380000,495000,590000],[E,E,E,E,X,X,S,S]),
 'tpu_v8t':row([0,0,0,0,90000,560000,711000,812000],[E,E,E,E,S,S,S,S]),
 'trn2':  row([285000,335000,345000,255000,150000,50000,0,0],[E,E,E,E,X,X,X,X]),
 'trn3':  row([0,0,0,95000,350000,600000,700000,750000],[E,E,E,E,X,X,X,X]),
 'mi300': row([65568,23974,28478,31102,25000,10000,0,0],[E,E,E,E,S,X,X,X]),   # 5.2：SA 25,000
 'mi355': row([48610,72246,78179,88419,139000,100000,50000,25000],[E,E,E,E,S,X,X,X]),
 'mi450': row([0,0,0,0,5000,207000,225000,265000],[E,E,E,E,S,S,S,S]),
}
NOTES = {  # 按季格的补充说明（表 2-3 悬停）
 ('b200','2026Q4'):'SemiAnalysis 只给 Blackwell 合计 734,504 颗，按 B200 10% / B300 90% 拆。10 月取 Epoch 的 30,946 颗 × 31/25（Epoch 的 10 月只算到 10/25）＝38,373 颗；11、12 月按 45% / 55% 分其余，属预测。',
 ('b300','2026Q4'):'SemiAnalysis 只给 Blackwell 合计 734,504 颗，按 B200 10% / B300 90% 拆。10 月取 Epoch 的 384,733 颗 × 31/25＝477,069 颗；11、12 月按 45% / 55% 分其余，属预测。',
 ('b200','2027Q1'):'SemiAnalysis Blackwell 合计 332,520 颗，按 10% / 90% 拆。',('b300','2027Q1'):'SemiAnalysis Blackwell 合计 332,520 颗，按 10% / 90% 拆。',
 ('b200','2027Q2'):'SemiAnalysis Blackwell 合计 262,480 颗，按 10% / 90% 拆。',('b300','2027Q2'):'SemiAnalysis Blackwell 合计 262,480 颗，按 10% / 90% 拆。',
 ('r200','2026Q3'):'本报告推算：以 Nvidia 2027 财年三季度（7/27–10/25）Epoch 合计 201,961 颗为锚，按爬坡分 7 月 2,000、8 月 46,500、9 月 68,700、10/1–10/25 84,761。日历三季度＝117,200 颗。Epoch 的日历三季度是 146,477 颗（按天平摊），差额 29,277 颗移到四季度。SemiAnalysis 这一季是 220,752 颗。',
 ('r200','2026Q4'):'SemiAnalysis 920,000 颗 + 三季度让出的 29,277 颗＝949,277 颗（下半年总数不变）。10 月＝84,761 + 10/26–31 的 40,000＝124,761 颗（推算）；11、12 月按 42% / 58% 分其余 824,516 颗（预测）。',
 ('hopper','2026Q3'):'用 Epoch。SemiAnalysis 这一季是 200,000 颗。',
 ('hopper','2026Q4'):'10 月取 Epoch 的 25,214 颗 × 31/25＝31,265 颗；SemiAnalysis 全季 100,000 颗，11、12 月按 45% / 55% 分其余。',
 ('tpu_v7','2026Q3'):'本报告推算：Epoch 到 8/2 为止 274,866 颗（约等于 7 月）；博通 5–7 月那一季约 80 万颗、8–10 月推算约 100 万颗 → 日历三季度博通约 94 万颗（v7 + v8i）。',
 ('tpu_v8i','2026Q3'):'本报告推算：Epoch 到 8/2 为止 14,596 颗（约等于 7 月），8、9 月平分其余。',
 ('tpu_v8t','2026Q3'):'SemiAnalysis（联发科那一份）。月度：8 月 30%、9 月 70%。',
 ('tpu_v7','2026Q4'):'本报告推算：博通约 10 月 33 万 + 11–12 月 80 万颗（v7 + v8i 合计，按两者季度量的比例分）。',
 ('tpu_v8i','2026Q4'):'本报告推算：同 v7 那一格。',
 ('tpu_v8t','2026Q4'):'SemiAnalysis（联发科那一份）。2026 全年 TPU 合计约 389 万颗，落在各家预测 330–460 万颗之内，低于 Google 说的 430 万颗。',
 ('tpu_v7','2027Q1'):'v7 尾量 30 万颗是本报告的假设。',('tpu_v7','2027Q2'):'v7 尾量 15 万颗是本报告的假设。',
 ('tpu_v8i','2027Q1'):'SemiAnalysis（博通那一份，Google 自用 345,000 + Anthropic 150,000）。',
 ('tpu_v8i','2027Q2'):'SemiAnalysis（博通那一份，Google 自用 275,000 + Anthropic 315,000）。',
 ('trn3','2026Q3'):'本报告推算：JPMorgan 预计 2026 年 Trainium3 约 130 万颗。',
 ('trn3','2027Q1'):'本报告推算：JPMorgan 预计 2027 年 Trainium3 约 310 万颗。',('trn3','2027Q2'):'本报告推算：JPMorgan 预计 2027 年 Trainium3 约 310 万颗。',
 ('mi355','2026Q4'):'10 万颗是本报告的假设。',
 ('mi300','2026Q3'):'SemiAnalysis（MI300/325）。',
 ('mi450','2026Q4'):'SemiAnalysis：MI400/450 155,000 + Meta 定制 52,000。',
 ('mi450','2027Q1'):'SemiAnalysis：MI400/450 135,000 + Meta 定制 90,000。',('mi450','2027Q2'):'SemiAnalysis：MI400/450 140,000 + Meta 定制 125,000。',
 ('mi355','2025Q4'):'不含中国特供的 MI308X 31,783 颗。',
}

def qmonths(q):
    y,n=int(q[:4]),int(q[-1]); return ['%d-%02d'%(y,3*(n-1)+i) for i in (1,2,3)]
def madd(m,k):
    y,mo=int(m[:4]),int(m[5:]); t=y*12+mo-1+k; return '%d-%02d'%(t//12,t%12+1)

# ---------- 2b. 拆到月 ----------
def split(sku,q,units,src):
    """返回 [(month, units, src)]，src 可在月内不同（例如 10 月是 Epoch 已有的数）。"""
    ms=qmonths(q)
    if q=='2026Q3' and sku=='r200':   # 5.1：财季锚 + 爬坡
        return [(ms[0],2000,X),(ms[1],46500,X),(ms[2],68700,X)]
    if q=='2026Q4' and sku=='r200':   # 5.1：10 月推算 124,761；11/12 月 42%/58%（预测）
        octv=84761+40000; r=units-octv
        return [(ms[0],octv,X),(ms[1],r*0.42,src),(ms[2],r*0.58,src)]
    if q=='2026Q3' and sku=='tpu_v8t':return [(ms[0],0,src),(ms[1],units*0.3,src),(ms[2],units*0.7,src)]
    if q=='2026Q3' and sku in ('tpu_v7','tpu_v8i'):
        jul={'tpu_v7':274866,'tpu_v8i':14596}[sku]; r=(units-jul)/2
        return [(ms[0],jul,E),(ms[1],r,src),(ms[2],r,src)]
    if q=='2026Q4' and sku in ('hopper','b200','b300'):   # 5.1：Epoch 10 月只到 10/25 → × 31/25；11/12 月 45%/55%
        octv={'hopper':25214,'b200':30946,'b300':384733}[sku]*31/25; r=units-octv
        return [(ms[0],octv,'epoch31'),(ms[1],r*0.45,src),(ms[2],r*0.55,src)]
    if q=='2026Q4' and sku in ('tpu_v7','tpu_v8i'):
        tot=750000+380000; share=units/tot
        return [(ms[0],330000*share,src),(ms[1],400000*share,src),(ms[2],400000*share,src)]
    return [(m,units/3,src) for m in ms]

SKU = {s[0]:dict(key=s[0],lane=s[1],name=s[2],f8=s[3],f4=s[4],conf=s[5],basis=s[6],lag=LAG[s[0]]) for s in SKUS}
ship_m = {}   # sku -> month -> {units,src}
for k,rows in SHIP.items():
    ship_m[k]={}
    for q in QS:
        for m,u,src in split(k,q,rows[q]['units'],rows[q]['src']):
            ship_m[k][m]={'units':u,'src':src}

def label(src,ship_month):
    if src=='epoch': return ('epoch','Epoch AI Chip Sales（2026-11-19）','中',False)
    if src=='epoch31': return ('epoch','Epoch AI Chip Sales（2026-11-19；10 月只算到 10/25，按 31/25 补满整月）','中',False)
    if src=='sa':
        if ship_month>='2026-11': return ('forecast','SemiAnalysis Accelerator Outlook 预测（2026-11-13）','中',True)
        return ('sa','SemiAnalysis Accelerator Outlook（2026-11-13）','中',False)
    return ('est','本报告推算','低',True)

# ---------- 3. 平移到到卡 ----------
ARR_MONTHS=[]; m='2025-10'
while m<='2027-06': ARR_MONTHS.append(m); m=madd(m,1)
monthly=[]
for am in ARR_MONTHS:
    rec={'month':am,'lanes':{}}
    for ln,_ in LANES:
        segs=[]
        for s in SKUS:
            if s[1]!=ln: continue
            k=s[0]; sm=madd(am,-LAG[k]); c=ship_m[k].get(sm)
            if not c or c['units']<=0: continue
            kind,srcname,conf,hatch=label(c['src'],sm)
            u=c['units']
            segs.append({'sku':k,'ship_month':sm,'units':round(u),'h8':round(u*SKU[k]['f8']),'h4':round(u*SKU[k]['f4']),
                         'kind':kind,'src':srcname,'conf':conf,'hatch':hatch})
        tot={v:sum(x[v] for x in segs) for v in ('units','h8','h4')}
        rec['lanes'][ln]={'segs':segs,'total':tot}
    rec['total']={v:sum(rec['lanes'][l]['total'][v] for l,_ in LANES) for v in ('units','h8','h4')}
    monthly.append(rec)

def m2q(m): return '%sQ%d'%(m[:4],(int(m[5:])-1)//3+1)
AQ=['2025Q4','2026Q1','2026Q2','2026Q3','2026Q4','2027Q1','2027Q2']
quarterly=[]
for q in AQ:
    recs=[r for r in monthly if m2q(r['month'])==q]
    lanes={}
    for ln,_ in LANES:
        bysku={}
        for r in recs:
            for sg in r['lanes'][ln]['segs']:
                b=bysku.setdefault(sg['sku'],{'sku':sg['sku'],'units':0,'h8':0,'h4':0,'hatch_h8':0,'hatch_h4':0,'hatch_units':0,'kinds':set(),'ship_months':[]})
                for v in ('units','h8','h4'):
                    b[v]+=sg[v]
                    if sg['hatch']: b['hatch_'+v]+=sg[v]
                b['kinds'].add(sg['kind']); b['ship_months'].append(sg['ship_month'])
        segs=[]
        for s in SKUS:
            if s[0] in bysku:
                b=bysku[s[0]]; b['kinds']=sorted(b['kinds']); b['ship_months']=sorted(set(b['ship_months'])); segs.append(b)
        lanes[ln]={'segs':segs,'total':{v:sum(x[v] for x in segs) for v in ('units','h8','h4')}}
    quarterly.append({'quarter':q,'lanes':lanes,'total':{v:sum(lanes[l]['total'][v] for l,_ in LANES) for v in ('units','h8','h4')}})

ship_table={k:{q:dict(SHIP[k][q],note=NOTES.get((k,q),''),**{'label':label(SHIP[k][q]['src'],qmonths(q)[2])[1],'conf':label(SHIP[k][q]['src'],qmonths(q)[2])[2]}) for q in QS} for k in SHIP}

out={'meta':{'generated':'2026-11-22','decisions':'compute/decisions.md（2026-11-22）','h100_fp8_dense_tflops':H100,
             'sources':{'epoch':'Epoch AI Chip Sales（2026-11-19 版）','sa':'SemiAnalysis Accelerator Outlook（2026-11-13）','est':'本报告推算'},
             'not_counted':['华为昇腾、寒武纪（中国国内供给）','Nvidia H20、AMD MI308X（中国特供）','Meta MTIA、微软 Maia、OpenAI 自研芯片（量小或未量产）','SemiAnalysis 的「Other Blackwell」每季 45 万颗（推测为 RTX Pro 等非训练卡）'],
             'lag_note':LAG_NOTE},
     'lanes':[{'key':k,'name':n} for k,n in LANES],
     'skus':[SKU[s[0]] for s in SKUS],
     'quarters_ship':QS,'ship_quarterly':ship_table,
     'ship_monthly':{k:{m:{'units':round(v['units']),'src':v['src']} for m,v in ship_m[k].items()} for k in ship_m},
     'arrive_monthly':monthly,'arrive_quarterly':quarterly}
json.dump(out,open(os.path.join(HERE,'model.json'),'w'),ensure_ascii=False,indent=1,sort_keys=True)

# ---------- 4. 自检 ----------
ok=True
print('自检①  每季出货合计 = decisions.md 表（逐 SKU 逐季，月度相加回到季度）')
bad=0
for k in SHIP:
    for q in QS:
        s=sum(ship_m[k][m]['units'] for m in qmonths(q))
        if abs(s-SHIP[k][q]['units'])>0.5: bad+=1; print('   不等',k,q,s,SHIP[k][q]['units'])
print('   %s（%d 个 SKU × %d 季）'%('全部相等' if not bad else '有 %d 处不等'%bad,len(SHIP),len(QS))); ok&=not bad
for ln,nm in LANES:
    print('   %-14s'%nm,'  '.join('%s %s'%(q[2:],format(sum(SHIP[k][q]['units'] for k in SHIP if SKU[k]['lane']==ln),',')) for q in QS))

# 与 Epoch CSV 交叉核对（2025Q3–2026Q2 + 已给的月度数）
EMAP={'H100/H200':'hopper','B200':'b200','B300':'b300','R200':'r200','TPU v6e':'tpu_v6e','TPU v7':'tpu_v7','TPU v8i':'tpu_v8i',
      'Trainium2':'trn2','Trainium3':'trn3','MI300X':'mi300','MI325X':'mi300','MI350X':'mi355','MI355X':'mi355'}
CHINA=('Ascend','Siyuan','MI308X','H20')
ep={};ep_all={};ep_cn={}
p=os.path.join(HERE,'web','epoch_ai_chip_sales_timelines_by_chip.csv')
for r in csv.DictReader(open(p,encoding='utf-8')):
    sd=r['Start date'];q='%sQ%d'%(sd[:4],(int(sd[5:7])-1)//3+1)
    h=float(r['Compute estimate in H100e (median)'] or 0)
    ep_all[q]=ep_all.get(q,0)+h
    ct=r['Chip type'].strip()
    if any(c in r['Name'] or c in ct for c in CHINA): ep_cn[q]=ep_cn.get(q,0)+h; continue
    k=EMAP.get(ct)
    if k: ep.setdefault((k,q),0); ep[(k,q)]+=int(float(r['Number of Units']))
diff=[(k,q,SHIP[k][q]['units'],v) for (k,q),v in ep.items() if q in QS[:5] and k in SHIP and SHIP[k][q]['src']=='epoch' and v!=SHIP[k][q]['units']]
print('   与 Epoch CSV 逐格核对（Epoch 来源的格）：','全部一致' if not diff else diff)

print('自检②  2026Q2 出货的 8 位 H100 等效（三条泳道合计）')
mine=sum(SHIP[k]['2026Q2']['units']*SKU[k]['f8'] for k in SHIP)
print('   本模型 %.2f M；Epoch 全行业 %.2f M，减去华为 / 寒武纪 / MI308X / H20 %.2f M → %.2f M；差 %.2f M（%.1f%%）'%(
    mine/1e6,ep_all['2026Q2']/1e6,ep_cn.get('2026Q2',0)/1e6,(ep_all['2026Q2']-ep_cn.get('2026Q2',0))/1e6,
    (mine-(ep_all['2026Q2']-ep_cn.get('2026Q2',0)))/1e6,100*(mine/(ep_all['2026Q2']-ep_cn.get('2026Q2',0))-1)))
print('   差额来源：TPU v8i 系数 2.55（Epoch 5.10）、MI350X 系数 2.54（Epoch 2.33）、各家系数取两位小数。')

print('自检③  图 2-1：2026 年 6–11 月每月到卡（8 位 H100 等效，万）')
print('   月份      Nvidia    TPU   Trn+AMD   合计   Rubin 占 Nvidia')
for r in monthly:
    if '2026-06'<=r['month']<='2026-11':
        L=r['lanes'];rb=sum(s['h8'] for s in L['nvidia']['segs'] if s['sku'] in('r200','rubin_ultra'))
        print('   %s  %7.1f %7.1f %7.1f %7.1f   %4.0f%%'%(r['month'],L['nvidia']['total']['h8']/1e4,L['tpu']['total']['h8']/1e4,L['other']['total']['h8']/1e4,r['total']['h8']/1e4,100*rb/max(1,L['nvidia']['total']['h8'])))
print('   按到卡季汇总（8 位，万 H100 等效）：')
for q in quarterly:
    print('   %s  Nvidia %6.1f  TPU %6.1f  Trn+AMD %6.1f  合计 %6.1f'%(q['quarter'],*(q['lanes'][l]['total']['h8']/1e4 for l,_ in LANES),q['total']['h8']/1e4))
first=[r['month'] for r in monthly if sum(s['h8'] for s in r['lanes']['nvidia']['segs'] if s['sku'] in('r200','rubin_ultra'))*2>r['lanes']['nvidia']['total']['h8']]
print('   Rubin 在 Nvidia 到卡里过半的第一个月：',first[0] if first else '无')
sys.exit(0 if ok else 1)
