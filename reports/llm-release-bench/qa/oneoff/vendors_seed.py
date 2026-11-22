import json
# 留档：2026-11-22 从手写版报告反抽数据用的一次性脚本，依赖当时的 HTML 结构，以后不要再跑。
def L(s): return {"zh": s, "en": ""}
V = [
 dict(key='google', name='Google', product='Gemini', group=L('前沿'), css_var='--g', light='#2a78d6', dark='#3987e5', legend_tip=L('Google Gemini 4 系列。悬停只看这一家。'), t22_class='vg', builtin_css=True),
 dict(key='anthropic', name='Anthropic', product='Claude', group=L('前沿'), css_var='--a', light='#eb6834', dark='#d95926', legend_tip=L('Anthropic Claude 系列。悬停只看这一家。'), t22_class='va', builtin_css=True),
 dict(key='openai', name='OpenAI', product='ChatGPT / GPT', group=L('前沿'), css_var='--o', light='#1baf7a', dark='#199e70', legend_tip=L('OpenAI GPT 系列。悬停只看这一家。'), t22_class='vo', builtin_css=True),
 dict(key='xai', name='xAI', product='Grok', group=L('大厂'), css_var='--xa', light='#eda100', dark='#c98500', legend_tip=L('xAI Grok 系列。悬停只看这一家。'), t22_class='vx', builtin_css=False),
 dict(key='meta', name='Meta', product='Muse', group=L('大厂'), css_var='--me', light='#e87ba4', dark='#d55181', legend_tip=L('Meta Muse 系列。悬停只看这一家。'), t22_class='vm', builtin_css=False),
 dict(key='deepseek', name='DeepSeek', product='DeepSeek', group=L('开源'), css_var='--ds', light='#008300', dark='#0ca30c', legend_tip=L('DeepSeek 系列。悬停只看这一家。'), t22_class='vd', builtin_css=False),
 dict(key='moonshot', name='Moonshot', product='Kimi', group=L('开源'), css_var='--ms', light='#6250d6', dark='#9085e9', legend_tip=L('Moonshot Kimi 系列。悬停只看这一家。'), t22_class='vk', builtin_css=False),
 dict(key='zhipu', name='Zhipu', product='GLM', group=L('开源'), css_var='--zp', light='#e34948', dark='#e66767', legend_tip=L('智谱 GLM 系列。悬停只看这一家。'), t22_class='vz', builtin_css=False),
]
lanes = [dict(lane='google', vendor='google'), dict(lane='anthropic', vendor='anthropic'),
         dict(lane='internal', vendor='anthropic', label=L('内部代号'), hollow_swatch=True), dict(lane='openai', vendor='openai')] + \
        [dict(lane=k, vendor=k) for k in ('xai', 'meta', 'deepseek', 'moonshot', 'zhipu')]
ref = [dict(key='nvidia', role=L('算力泳道 Nvidia（compute/build.py 管）'), light='#494845', dark='#b8b7b4'),
       dict(key='tpu', role=L('算力泳道 TPU，与 Google 同色（compute/build.py 管）'), light='#2a78d6', dark='#3987e5'),
       dict(key='other', role=L('算力泳道 Trainium + AMD（compute/build.py 管）'), light='#a8418b', dark='#a8418b')]
out = {'_readme': L('厂商表：顺序＝表 2-1 分组顺序＝图 3-x 图例顺序。builtin_css=true 的三家颜色写在报告原 CSS 里；其余由 build_tables.py 生成 <style id="data-css">（只在该厂商有模型或时间轴事件时才生成）。改颜色后跑 qa/palette_check.py。'),
       'vendors': V, 'timeline_lanes': lanes, 'reference_colors': ref,
       'surfaces': {'light': '#ffffff', 'dark': '#1a1a19'}}
json.dump(out, open('data/vendors.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
