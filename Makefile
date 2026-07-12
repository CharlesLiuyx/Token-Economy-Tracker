# Token-Tracker — 本地与 CI 共用同一路径：make update && make build && make serve
PY  := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: venv update build serve test clean

venv: .venv/bin/python

.venv/bin/python:
	python3 -m venv .venv
	$(PIP) install -q -r requirements.txt

# 逐源抓取；单源失败（行首 -）不中断整次运行
update: venv
	-$(PY) -m scripts.fetch.epoch_datacenters
	-$(PY) -m scripts.fetch.sdk_downloads
	-$(PY) -m scripts.fetch.news
	-$(PY) -m scripts.fetch.openrouter
	-$(PY) -m scripts.fetch.vercel_gateway
	-$(PY) -m scripts.fetch.gpu_prices
	-$(PY) -m scripts.derive.arr

# data/ -> site/index.html（唯一允许生成 site/index.html 的入口）
build: venv
	$(PY) -m scripts.build

serve:
	$(PY) -m http.server 8000 -d site

test: venv
	$(PY) -m pytest -q

# 单源调试：make fetch-epoch_datacenters / fetch-sdk_downloads / fetch-news …
fetch-%: venv
	$(PY) -m scripts.fetch.$*

clean:
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
