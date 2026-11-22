import csv, json, collections
EP_URL="https://epoch.ai/data/ai-chip-sales"
EP_CSV="https://epoch.ai/data/ai_chip_sales_timelines_by_chip.csv"
EP_METH="https://epoch.ai/data/ai-chip-sales-documentation/methodology"
EP_DATE="2026-11-19"
def q(s):
    y=s[:4]; m=int(s[5:7]); return f"{y}Q{(m-1)//3+1}"
rows=list(csv.DictReader(open('epoch_ai_chip_sales_timelines_by_chip.csv',encoding='utf-8')))
def num(x):
    try: return float(x)
    except: return None
shipments=[]; agg=collections.defaultdict(lambda:[0,0,0]); aggu=collections.defaultdict(float)
for r in rows:
    if r['Start date']<'2025-01-01': continue
    per=q(r['Start date']); vendor=r['Chip manufacturer'].strip(); sku=r['Chip type'].strip()
    u=num(r['Number of Units']); inc=r['Incomplete'].strip()=='True'
    shipments.append({"vendor":vendor,"sku":sku,"period":per,"period_kind":"calendar",
      "units":u,"units_low":num(r['Number of Units (5th percentile)']),"units_high":num(r['Number of Units (95th percentile)']),
      "unit_type":"package","source_title":"Epoch AI, AI Chip Sales dataset (timelines_by_chip.csv)","url":EP_CSV,"source_date":EP_DATE,
      "excerpt":"Epoch 中位数＋90% 区间（第5/95百分位）","confidence":"中" if not inc else "低",
      "note":("Epoch 标记 Incomplete：该日历季数据未覆盖完整（Nvidia 只到 FQ3 结束 10/25，博通只到 FQ3 结束 8/2）。" if inc else "")+
             "Epoch 把厂商财季插值分配到日历季；H100e 中位数="+str(r['Compute estimate in H100e (median)'])+
             "（5–95%："+str(r['H100e (5th percentile)'])+"–"+str(r['H100e (95th percentile)'])+"）；chip cost USD="+str(r['Chip Cost (USD)'])+
             "。B200 含 GB200，B300 含 GB300；R200=Rubin（一颗封装两 die）。",
      "h100e_median":num(r['Compute estimate in H100e (median)'])})
    a=agg[(vendor,per)]
    for i,k in enumerate(['Compute estimate in H100e (median)','H100e (5th percentile)','H100e (95th percentile)']):
        a[i]+=num(r[k]) or 0
    aggu[(vendor,per)]+=u or 0
inc_periods={q(r['Start date']) for r in rows if r['Incomplete'].strip()=='True'}
h100e_series=[]
for (v,p),a in sorted(agg.items(), key=lambda x:(x[0][1],x[0][0])):
    h100e_series.append({"vendor":v,"period":p,"h100e":round(a[0]),"h100e_sum_of_p5":round(a[1]),"h100e_sum_of_p95":round(a[2]),
      "units_sum":round(aggu[(v,p)]),"source":"Epoch AI AI Chip Sales（按 chip 行加总；p5/p95 直接相加偏宽，不是真实区间）"+("；该季含 Incomplete 行" if p in inc_periods else ""),"url":EP_CSV})
tot=collections.defaultdict(float)
for (v,p),a in agg.items(): tot[p]+=a[0]
for p in sorted(tot):
    h100e_series.append({"vendor":"ALL(Epoch 六家)","period":p,"h100e":round(tot[p]),"source":"Epoch AI 各行加总"+("；含 Incomplete 行，偏低" if p in inc_periods else ""),"url":EP_CSV})

S=lambda **k:k
# 非 Epoch 出货口径
shipments += [
 S(vendor="Nvidia",sku="Rubin (VR200 NVL72, R200)",period="FY27Q3 (2026-07-27..10-25)",period_kind="nvda_fiscal",units=200000,units_low=None,units_high=None,unit_type="package",
   source_title="Epoch AI methodology – Rubin",url=EP_METH,source_date=EP_DATE,excerpt="just over 200,000 Rubin GPUs shipped",confidence="中",
   note="≈160亿美元 Rubin compute 收入 ÷ 每 GPU 约 7.5 万美元 compute 收入；Rubin 平台收入近 200 亿（含网络等）。CSV 里日历 Q3=146,477 + Q4(部分)=55,484。"),
 S(vendor="Nvidia",sku="Rubin (VR200 NVL72)",period="FY27Q3",period_kind="nvda_fiscal",units=None,units_low=183500,units_high=286100,unit_type="package",
   source_title="Tom's Hardware: Nvidia expects to sell $20B worth of Vera Rubin hardware this quarter",url="https://www.tomshardware.com/tech-industry/artificial-intelligence/nvidia-expects-to-sell-usd20-billion-worth-of-vera-rubin-hardware-this-quarter-would-account-for-20-percent-of-data-center-revenue-its-fastest-ramp-in-company-history",
   source_date="2026-08-27",excerpt="183,500 – 286,100 Rubin GPUs",confidence="低",note="作者按 $5M–7.8M/机柜 反推 2,550–3,975 个 NVL72；事前估算，假设全部为 NVL72。"),
 S(vendor="Nvidia",sku="Rubin (VR200 NVL72)",period="FY27Q3",period_kind="nvda_fiscal",units=None,units_low=2550,units_high=3975,unit_type="rack",
   source_title="Tom's Hardware (同上)",url="https://www.tomshardware.com/tech-industry/artificial-intelligence/nvidia-expects-to-sell-usd20-billion-worth-of-vera-rubin-hardware-this-quarter-would-account-for-20-percent-of-data-center-revenue-its-fastest-ramp-in-company-history",
   source_date="2026-08-27",excerpt="2,550 to approximately 3,975 machines",confidence="低",note="机柜数＝颗数/72。"),
 S(vendor="Google(Broadcom)",sku="TPU (v7 为主 + v8i 起量)",period="AVGO FY26Q3 (≈2026-05-04..08-02)",period_kind="avgo_fiscal",units=800000,units_low=None,units_high=None,unit_type="chip",
   source_title="Epoch AI Data Insight: Broadcom TPU production doubling",url="https://epoch.ai/data-insights/tpu-production-doubling",source_date="2026-11-04",
   excerpt="roughly 800,000 chips",confidence="中",note="环比 +65%；算力近 200 万 H100e（1.97M）；含卖给 Anthropic 的 TPU；v8i 本季投产，单颗≈v7 的 2.2 倍。"),
 S(vendor="Google",sku="TPU 全部",period="2026",period_kind="year",units=3200000,units_low=None,units_high=None,unit_type="chip",
   source_title="KuCoin flash 转述 Morgan Stanley (Joseph Moore)",url="https://www.kucoin.com/news/flash/morgan-stanley-defends-broadcom-s-role-in-google-s-tpu-supply-chain-forecasts-5m-shipments-by-2027",
   source_date="2026-07-15",excerpt="3.2 million units in 2026",confidence="低",note="二手转述；同一来源 2027=500 万。"),
 S(vendor="Google",sku="TPU 全部",period="2027",period_kind="year",units=5000000,units_low=None,units_high=None,unit_type="chip",
   source_title="KuCoin flash 转述 Morgan Stanley",url="https://www.kucoin.com/news/flash/morgan-stanley-defends-broadcom-s-role-in-google-s-tpu-supply-chain-forecasts-5m-shipments-by-2027",
   source_date="2026-07-15",excerpt="5 million in 2027",confidence="低",note="二手转述。"),
 S(vendor="Google",sku="TPU 全部",period="2026",period_kind="year",units=4504000,units_low=None,units_high=None,unit_type="chip",
   source_title="24/7 Wall St. 转述 GF Securities（广发证券）",url="https://247wallst.com/investing/2026/08/25/google-tpu-volume-could-triple-to-8-8-million-by-2027/",
   source_date="2026-08-25",excerpt="4.504 million units",confidence="低",note="2025=285.4 万，2027=884 万；Google 未背书。"),
 S(vendor="Google",sku="TPU 全部",period="2027",period_kind="year",units=8840000,units_low=None,units_high=None,unit_type="chip",
   source_title="24/7 Wall St. 转述 GF Securities",url="https://247wallst.com/investing/2026/08/25/google-tpu-volume-could-triple-to-8-8-million-by-2027/",
   source_date="2026-08-25",excerpt="8.84 million units",confidence="低",note=""),
 S(vendor="Amazon",sku="Trainium2",period="截至 2025 末/2026 初累计",period_kind="year",units=1400000,units_low=None,units_high=None,unit_type="chip",
   source_title="Epoch methodology 引 Amazon Q4 2025 财报（2026-02-05）",url=EP_METH,source_date="2026-02-05",
   excerpt="Trainium2 is fully subscribed with 1.4 million chips landed",confidence="高",note="“landed”可能指已运行或仅已到货；Epoch 估 2026H1 再增约 60 万（40–90 万），Trainium3 不到 10 万（3–30 万）。"),
 S(vendor="Amazon",sku="Trainium2+Trainium3",period="2026Q3",period_kind="calendar",units=None,units_low=None,units_high=None,unit_type="chip",
   source_title="TradingKey: AWS hiking Q3 ASIC server shipment targets",url="https://www.tradingkey.com/analysis/stocks/us-stocks/262013038-amazon-aws-hiking-q3-asic-server-shipment-targets-up-30-tradingkey",
   source_date="2026-07-06",excerpt="Q3 目标上调 20%–30%",confidence="低",note="无绝对颗数；Trainium3 主板级 5 月起出货，机柜组装 7 月量产。Epoch CSV 无 2026Q3 Trainium 行。"),
 S(vendor="Nvidia",sku="Blackwell vs Rubin 份额",period="2026",period_kind="year",units=None,units_low=None,units_high=None,unit_type="package",
   source_title="TrendForce 2026-04-08",url="https://www.trendforce.com/presscenter/news/20260408-13003.html",source_date="2026-04-08",
   excerpt="Rubin share 29% → 22%",confidence="中",note="2026 高端 GPU 出货份额：Blackwell 71%、Rubin 22%、Hopper 7%；无绝对颗数。"),
 S(vendor="Nvidia",sku="Blackwell / Rubin",period="2026",period_kind="year",units=None,units_low=None,units_high=None,unit_type="die?",
   source_title="TweakTown 转述 JP Morgan（2025-06-30，已过时）",url="https://www.tweaktown.com/news/106116/nvidia-expected-to-ship-5-2m-blackwell-gpus-in-2025-1-8m-2026-and-7m-rubin/index.html",
   source_date="2025-06-30",excerpt="Blackwell 1.8M、Rubin 5.7M (2026)",confidence="低",note="2025 年中旧预测，Rubin 实际 8 月才出货，与实际偏差大，仅作反面参照。"),
]

specs=[
 S(sku="H100 SXM",fp8_dense_tflops=1979,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=989.5,hbm_gb=80,power_w=700,
   sparse_or_dense_note="Nvidia 官方 FP8 3,958 为稀疏；稠密=1,979。无 FP4。Epoch H100e 基准分母=1,979 TFLOPS。",source_title="Epoch chip_types.csv",url="https://epoch.ai/data/ai_chip_sales_chip_types.csv"),
 S(sku="H200 SXM",fp8_dense_tflops=1979,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=989.5,hbm_gb=141,power_w=700,
   sparse_or_dense_note="算力同 H100，显存 141GB。Epoch H100e=1.0。",source_title="Epoch chip_types.csv",url="https://epoch.ai/data/ai_chip_sales_chip_types.csv"),
 S(sku="B200 (HGX, 风冷/1000W 级)",fp8_dense_tflops=4500,fp4_dense_tflops=9000,fp4_dense_inference_tflops=None,bf16_dense_tflops=2250,hbm_gb=180,power_w=1000,
   sparse_or_dense_note="HGX B200 8 卡：FP4 144|72 PF（稀疏|稠密），FP8 72 PF 为稀疏（稠密=一半）→ 每卡 FP8 稠密 4.5 PF、FP4 稠密 9 PF、BF16 稠密 2.25 PF。HGX 8卡显存 1.4TB。功耗 1000W 为常见口径（未在本页核实）；Epoch 用 1200W、8-bit 5 PF（按 GB200 口径）。",
   source_title="NVIDIA HGX 规格页",url="https://www.nvidia.com/en-us/data-center/hgx/"),
 S(sku="GB200 (每 GPU, NVL72)",fp8_dense_tflops=5000,fp4_dense_tflops=10000,fp4_dense_inference_tflops=None,bf16_dense_tflops=2500,hbm_gb=186,power_w=1200,
   sparse_or_dense_note="Superchip(2 GPU)：NVFP4 40|20 PF（稀疏|稠密），FP8 20 PF 稀疏，BF16 10 PF 稀疏；“Dense is one-half sparse”。372GB/2=186GB。功耗取 Epoch 1200W。",
   source_title="NVIDIA GB200 NVL72 规格页",url="https://www.nvidia.com/en-us/data-center/gb200-nvl72/"),
 S(sku="B300 (HGX)",fp8_dense_tflops=4500,fp4_dense_tflops=13500,fp4_dense_inference_tflops=None,bf16_dense_tflops=2250,hbm_gb=270,power_w=None,
   sparse_or_dense_note="HGX B300 8 卡：FP4 144|108 PF（稀疏|稠密），FP8 72 PF 稀疏，INT8 仅 3 POPS（B300 砍了 INT8），显存 2.1TB/8≈270GB（标称 288GB）。",
   source_title="NVIDIA HGX 规格页",url="https://www.nvidia.com/en-us/data-center/hgx/"),
 S(sku="GB300 (每 GPU, NVL72)",fp8_dense_tflops=5000,fp4_dense_tflops=15000,fp4_dense_inference_tflops=None,bf16_dense_tflops=2500,hbm_gb=288,power_w=1400,
   sparse_or_dense_note="NVL72 整柜：FP4 1,440|1,080 PF，FP8 720 PF、BF16 360 PF（页面注“默认带稀疏”）→ 每 GPU FP8 稠密 5 PF、FP4 稠密 15 PF。整柜 20TB（≈279GB/GPU，标称 288GB HBM3e）。功耗取 Epoch B300 1400W。",
   source_title="NVIDIA GB300 NVL72 规格页",url="https://www.nvidia.com/en-us/data-center/gb300-nvl72/"),
 S(sku="Rubin (R200 / VR200 NVL72 每 GPU)",fp8_dense_tflops=17500,fp4_dense_tflops=35000,fp4_dense_inference_tflops=50000,bf16_dense_tflops=4000,hbm_gb=288,power_w=2300,
   sparse_or_dense_note="官方：NVFP4 推理 50 PF（未标稠密/稀疏，靠自适应压缩）、NVFP4 训练 35 PF（稠密）、FP8/FP6 17.5 PF（稠密）、BF16 4 PF（稠密）、INT8 250 TOPS（稠密）、HBM4 288GB/22TB/s；“Preliminary”。功耗 2300W 为 Tom's Hardware 报道（由 1800W 上调），Epoch 也用 2300W。Epoch H100e=17.5/1.979=8.84。",
   source_title="NVIDIA Vera Rubin NVL72 规格页（.md）",url="https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72.md"),
 S(sku="Rubin CPX",fp8_dense_tflops=None,fp4_dense_tflops=None,fp4_dense_inference_tflops=30000,bf16_dense_tflops=None,hbm_gb=None,power_w=None,
   sparse_or_dense_note="30 PF NVFP4（口径未标），128GB GDDR7（非 HBM），面向长上下文 prefill；2026 年底推出，本季未见出货收入。",
   source_title="TechPowerUp 2026-07-21 Rubin 技术细节",url="https://www.techpowerup.com/350947/"),
 S(sku="TPU v6e (Trillium)",fp8_dense_tflops=1836,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=918,hbm_gb=32,power_w=380,
   sparse_or_dense_note="8-bit 为 INT8 1,836 TOPS；功耗 380W 为 Epoch 值。Epoch H100e=0.93。",source_title="Epoch chip_types.csv",url="https://epoch.ai/data/ai_chip_sales_chip_types.csv"),
 S(sku="TPU v7 Ironwood (TPU7x)",fp8_dense_tflops=4614,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=2307,hbm_gb=192,power_w=960,
   sparse_or_dense_note="Google 文档：BF16 2,307、FP8 4,614 TFLOPS，未标稠密/稀疏（TPU 无结构化稀疏，按稠密处理）；192GiB/7.37TB/s。功耗 960W 为 Epoch 值（官方未给）。Epoch H100e=2.33。",
   source_title="Google Cloud TPU7x 文档",url="https://docs.cloud.google.com/tpu/docs/tpu7x"),
 S(sku="TPU 8i (v8i, Zebrafish)",fp8_dense_tflops=None,fp4_dense_tflops=10100,fp4_dense_inference_tflops=None,bf16_dense_tflops=None,hbm_gb=288,power_w=None,
   sparse_or_dense_note="官方只给 Peak FP4 10.1 PF，未给 FP8/BF16/功耗；HBM 288GB/8.6TB/s，SRAM 384MB。注意：Epoch 把 10.1 PF 填进“8-bit OP/s”，得 H100e=5.10（≈v7 的 2.2 倍）；若 v8i 的 FP8 只有 FP4 的一半，真实 8-bit H100e≈2.55。",
   source_title="Google Cloud Blog: TPU 8t and TPU 8i technical deep dive (2026-04-22)",url="https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive"),
 S(sku="TPU 8t (v8t, Sunfish)",fp8_dense_tflops=None,fp4_dense_tflops=12600,fp4_dense_inference_tflops=None,bf16_dense_tflops=None,hbm_gb=216,power_w=None,
   sparse_or_dense_note="官方 Peak FP4 12.6 PF（StorageReview 称稠密），HBM 216GB/6.5TB/s；superpod 9,600 颗=121 EF FP4。Epoch 数据集尚无 v8t。",
   source_title="Google Cloud Blog (同上)",url="https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive"),
 S(sku="Trainium2",fp8_dense_tflops=1299,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=667,hbm_gb=96,power_w=500,
   sparse_or_dense_note="Epoch 值（稠密）。Epoch H100e=0.66。",source_title="Epoch chip_types.csv",url="https://epoch.ai/data/ai_chip_sales_chip_types.csv"),
 S(sku="Trainium3",fp8_dense_tflops=2517,fp4_dense_tflops=None,fp4_dense_inference_tflops=None,bf16_dense_tflops=671,hbm_gb=144,power_w=None,
   sparse_or_dense_note="MXFP8 2.52 PF（AWS/Digitimes，未标稠密），144GB HBM3e/4.9TB/s，3nm；BF16 671 为 Epoch 值。功耗官方未给（Epoch 表 TDP 空；Trainium1 行的 300W 是 Epoch 估计）。Epoch H100e=1.27。",
   source_title="AWS Trainium 页 + Epoch chip_types.csv",url="https://aws.amazon.com/ai/machine-learning/trainium/"),
 S(sku="MI355X",fp8_dense_tflops=5000,fp4_dense_tflops=10100,fp4_dense_inference_tflops=None,bf16_dense_tflops=2500,hbm_gb=288,power_w=1400,
   sparse_or_dense_note="AMD 官方：FP8 5 PF 无稀疏 / 10.1 PF 结构化稀疏；BF16 2.5 / 5；MXFP4 10.1 PF（无稀疏版本）；8TB/s；TBP 1400W。Epoch H100e=2.54。",
   source_title="AMD MI355X 产品页",url="https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html"),
 S(sku="MI455X (MI400/Helios)",fp8_dense_tflops=20100,fp4_dense_tflops=40300,fp4_dense_inference_tflops=None,bf16_dense_tflops=5000,hbm_gb=432,power_w=None,
   sparse_or_dense_note="AMD 官方：OCP FP8 20.1 PF、MXFP4 40.3 PF（页面未标稀疏，按 AMD 惯例为稠密）、BF16 5 PF 稠密/10.1 稀疏、HBM4 432GB/23.3TB/s；功耗未给。MI450X 手册写 288GB HBM4，同为 ~20 PF FP8。Epoch 数据集尚无 MI4xx。",
   source_title="AMD MI455X 产品页",url="https://www.amd.com/en/products/accelerators/instinct/mi400/mi455x.html"),
]

h100e_methods=[
 S(source="Epoch AI",method="H100e = 芯片峰值稠密 8-bit 算力（FP8 或 INT8，取两者较大）÷ H100 的 1,979 TFLOPS × 颗数",
   precision="8-bit，稠密（非稀疏）",excerpt="peak number of dense 8-bit operations (FP8 or INT8)",
   url=EP_URL,note="选 8-bit 是因为推理与头部实验室训练普遍用 8-bit；不考虑显存/带宽/利用率。GB200/GB300 每 GPU 比 B200/B300 单卡高 10%。B200 与 B300 都记 5 PF → H100e 2.53（未计 B300 的 FP4 增强）；Rubin 17.5 PF → 8.84；TPU v8i 用了 10.1 PF（官方标为 FP4）→ 5.10。"),
 S(source="Epoch AI",method="颗数估计：Nvidia/AMD 按季度 compute 收入 × 产品份额（财报口径）÷ ASP；Google TPU 按博通 AI 收入 × XPU 占比 × Google 份额 ÷ BOM 成本×(1+毛利)；Amazon 靠官方披露（1.4M Trn2）+ 分析师；华为靠第三方估计",
   precision="",excerpt="revenue-based models ... divide by average selling prices",url=EP_METH,
   note="单位=封装（package）。Nvidia 一个 Blackwell 封装=2 die，Nvidia 幻灯片“6M Blackwell GPUs”按 die 计≈3M 封装。财季按插值摊到日历季。统计的是交付/确认收入，不是已上线。"),
]

revenue=[
 S(vendor="Nvidia",period="FY27Q3 (2026-07-27..10-25)",item="总收入",usd_b=115.8,source="NVIDIA 财报 / Fierce Network",url="https://www.fierce-network.com/newswire/nvidia-revenue-more-doubles-vera-rubin-ramps",note=""),
 S(vendor="Nvidia",period="FY27Q3",item="数据中心收入",usd_b=107.6,source="Fierce Network / Futurum",url="https://futurumgroup.com/?p=98250",note="Hyperscale 601.4 亿，ACIE 474.7 亿（Next Platform）"),
 S(vendor="Nvidia",period="FY27Q3",item="数据中心 compute（CPU+GPU）",usd_b=86.32,source="The Next Platform",url="https://www.nextplatform.com/a/5310669",note="networking >21B（电话会）"),
 S(vendor="Nvidia",period="FY27Q3",item="Rubin 平台收入",usd_b=20.0,source="电话会：nearly $20 billion",url="https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript",note="Epoch 估其中 compute 约 160 亿"),
 S(vendor="Nvidia",period="FY27Q3",item="对华授权 Hopper 销售",usd_b=2.4,source="电话会",url="https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript",note="Q4 指引不含，已停止对华发货"),
 S(vendor="Nvidia",period="FY27Q3",item="Blackwell（推算，非披露）",usd_b=None,source="推算：86.3 − Rubin compute≈16 − Hopper≈2.4 ≈ 68",url="https://www.nextplatform.com/a/5310669",note="Nvidia 未披露 Blackwell 金额，此为粗算，含 Grace CPU 等"),
 S(vendor="Nvidia",period="FY27Q4 (2026-10-26..2027-01-31, 含额外一周)",item="总收入指引",usd_b=130.0,source="NVIDIA 指引 ±3%",url="https://futurumgroup.com/?p=98250",note="不含中国数据中心 compute；毛利率 71–72%；增长由 Vera Rubin 放量驱动；未给 Rubin/Blackwell 拆分"),
 S(vendor="Nvidia",period="FY27Q2 (2026-04-27..07-26)",item="总收入 / 数据中心",usd_b=96.22,source="Zacks/Nasdaq",url="https://www.nasdaq.com/articles/nvidia-q2-earnings-beat-blackwell-ultra-data-center-strength",note="数据中心 89.02B；Blackwell 为“vast majority”；Rubin 8 月开始量产出货，Q2 无 Rubin 收入"),
 S(vendor="Nvidia",period="FY27Q1 (2026-01-26..04-26)",item="总收入 / 数据中心",usd_b=81.62,source="Zacks/Nasdaq",url="https://www.nasdaq.com/articles/nvidia-q1-earnings-beat-blackwell-ramp-data-center-strength",note="数据中心 75.25B"),
 S(vendor="Broadcom",period="AVGO FY26Q3 (≈2026-05-04..08-02)",item="AI 半导体收入",usd_b=16.7,source="Nasdaq 电话会要点",url="https://www.nasdaq.com/articles/broadcom-q3-earnings-call-highlights",note="XPU 占 73%（≈122 亿）；v7 大量出货给 Anthropic 与 Google；v8i 本季开始量产出货"),
 S(vendor="Broadcom",period="AVGO FY26Q4 (≈2026-08-03..11-01)",item="AI 半导体收入指引",usd_b=21.7,source="Nasdaq 电话会要点",url="https://www.nasdaq.com/articles/broadcom-q3-earnings-call-highlights",note="实际财报约 12 月中旬发布，截至 2026-11-22 未出；FY27 AI 收入展望约 1,150 亿"),
 S(vendor="AMD",period="2026Q3",item="数据中心收入",usd_b=8.5,source="Constellation Research",url="https://www.constellationr.com/insights/news/amd-q3-shines-data-center-revenue-nearly-doubles",note="未拆 Instinct；MI455X 本季开始批量出货，首批 Helios 机柜上线；Q4 总收入指引 170 亿"),
]

asp=[
 S(sku="H100/H200",usd=25000,basis="Epoch 用于颗数（2025 几何均值约 2.56 万，区间 2.2–3.0 万）",source="Epoch methodology",url=EP_METH),
 S(sku="B200/GB200",usd=37000,basis="Epoch：GB200 区间 3.3–4.2 万（NVL72 指向 3.5–4 万/GPU）",source="Epoch methodology",url=EP_METH),
 S(sku="B300/GB300",usd=43000,basis="Epoch：GB300 区间 3.8–4.9 万（GB200 加价 10–20%）；Apple 据报 5.1–5.5 万/GPU",source="Epoch methodology",url=EP_METH),
 S(sku="Rubin (R200)",usd=75000,basis="Epoch：每 GPU 的 Nvidia compute 收入约 7.5 万；GPU 本体约 5.5 万（摩根士丹利 BOM）；整柜 700–800 万美元（MS 780 万=10.8 万/GPU；Bernstein 752 万）",source="Epoch methodology",url=EP_METH),
 S(sku="VR NVL72 vs GB300 NVL72",usd=None,basis="TrendForce：Vera Rubin 系统 ASP 约为 GB300 的 2 倍",source="TrendForce 2026-08-28",url="https://www.trendforce.com/presscenter/news/20260828-13204.html"),
 S(sku="TPU v6e / v7 / v8i",usd=None,basis="Epoch 每颗价格（BOM 模型+博通毛利约 60%）：v6e 约 4,059、v7 约 11,737（表内另写 13,000）、v8i 约 17,500",source="Epoch CSV",url=EP_CSV),
 S(sku="Trainium2",usd=4000,basis="Epoch 值",source="Epoch CSV",url=EP_CSV),
 S(sku="MI355X",usd=27500,basis="Epoch：2.5–3.0 万（引 Seeking Alpha）",source="Epoch methodology",url=EP_METH),
]

lags=[
 S(item="Rubin：Nvidia 说超大规模客户约 1 个月把 Vera Rubin 投入生产，是 Grace Blackwell 的一半",value_months=1,source="NVDA FY27Q3 电话会",url="https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript",note="暗示 GB 时代约 2 个月"),
 S(item="Rubin：8 月开始量产出货，约 3 个月后各大超大规模云与头部 neocloud 都在落地",value_months=3,source="NVDA FY27Q3 电话会",url="https://www.nasdaq.com/articles/nvidia-nvda-q3-2027-earnings-call-transcript",note="8/26 财报时已在 CoreWeave、Google Cloud、Azure、OCI、Nebius 运行"),
 S(item="Epoch AI Chip Users：出售→运行时滞 0.5–2 个季度，中位约 1 个季度",value_months=3,source="Epoch AI Chip Users methodology",url="https://epoch.ai/data/ai-chip-users-documentation/methodology",note="Google DeepMind 2025 运行/拥有比 0.69（0.55–0.87），Meta MSL 0.75（0.62–0.90）"),
 S(item="CoreWeave 2025Q1 披露约 3 个月安装时间，后称缩短到几周",value_months=3,source="Epoch AI Chip Users methodology 引 CoreWeave",url="https://epoch.ai/data/ai-chip-users-documentation/methodology",note=""),
 S(item="Amazon “1.4 million chips landed”的 landed 含义不明（到货 or 运行）",value_months=None,source="Epoch methodology",url=EP_METH,note=""),
 S(item="Trainium3：主板级 5 月出货、机柜组装 7 月量产",value_months=2,source="TradingKey",url="https://www.tradingkey.com/analysis/stocks/us-stocks/262013038-amazon-aws-hiking-q3-asic-server-shipment-targets-up-30-tradingkey",note="零件到整柜约 2 个月，非到卡时滞"),
]

other=[
 S(item="Epoch：季度新增 H100e 从 2024Q1 的 0.8M 涨到 2026Q2 的 6.3M，约 9 个月翻倍（2024 起约 2.5×/年）",source="Epoch Data Insight 2026-10-29",url="https://epoch.ai/data-insights/ai-computing-capacity-additions-doubling"),
 S(item="Epoch：所覆盖厂商 2025 年共售出 >10M H100e（累计约 20M）",source="Epoch methodology",url=EP_METH),
 S(item="Epoch AI Chip Users：2025 年末 H100e——OpenAI 1.74M、Anthropic 1.19M、Google DeepMind 1.58M、Meta MSL 0.996M、SpaceXAI 0.635M（中位数）",source="Epoch AI Chip Users methodology",url="https://epoch.ai/data/ai-chip-users-documentation/methodology"),
 S(item="博通 FY26Q3：Anthropic 2027 年再部署 5 GW TPU v8i，2028 年再增 10 GW；OpenAI 2027 年部署 1.3 GW Jalapeño；Meta MTIA 计划 Q4 量产出货",source="Nasdaq Broadcom Q3 要点",url="https://www.nasdaq.com/articles/broadcom-q3-earnings-call-highlights"),
 S(item="Morgan Stanley（2026-08-24）：Google 2026H2 卖出 0.3 GW TPU 系统，2027 年 3.2 GW，2028 年 4.2 GW",source="IEEE ComSoc techblog",url="https://techblog.comsoc.org/2026/09/08/googles-tpu-business-outpaces-rivals-as-hyperscalers-accelerate-custom-ai-silicon-strategies/"),
 S(item="TrendForce：2027 年 NVL72（GB+VR）机柜出货同比 +50% 以上，VR200 占最大份额；2026 年 GB300 仍是出货主力",source="TrendForce 2026-08-28",url="https://www.trendforce.com/presscenter/news/20260828-13204.html"),
 S(item="Nvidia FY27Q2 电话会：AWS 从本季起到 FY29Q2 追加部署 200 万颗 GPU",source="NVDA FY27Q2 电话会 PDF",url="https://s201.q4cdn.com/141608511/files/content_files/TRANSCRIPT_-NVIDIA-Corp-NVDA-US-Q2-2027-Earnings-Call-26-August-2026-5_00-PM-ET.pdf"),
 S(item="推算（非来源数字）：博通 FY26Q4 AI 指引 21.7B × XPU 约 73% ≈ 15.8B XPU，比 FY26Q3 的 12.2B 高约 30%；若 TPU 均价不变，FY26Q4 TPU 约 100 万颗——仅作量级参考，v8i 占比上升会让颗数变少、H100e 变多",source="本研究推算",url="https://www.nasdaq.com/articles/broadcom-q3-earnings-call-highlights"),
 S(item="未找到：SemiAnalysis / UBS / 摩根士丹利 的 2026 年 Blackwell、Rubin 按季颗数（付费墙或无公开转述）；AMD MI355X/MI455X 2026 按季颗数（Epoch 只到 2026Q2，且无 MI4xx）；AWS 2026Q3 Trainium 颗数",source="",url=""),
]

out=dict(meta=dict(generated="2026-11-22",note="Epoch 行=日历季、封装颗数；其余来源口径各异，见 period_kind/unit_type。Epoch 数据集版本 2026-11-19。"),
  shipments=shipments,specs=specs,h100e_methods=h100e_methods,h100e_series=h100e_series,revenue=revenue,asp=asp,lags=lags,other=other)
json.dump(out,open('findings.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(shipments),len(specs),len(h100e_series))
