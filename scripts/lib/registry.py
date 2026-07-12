"""data/sources.yml 源注册表读取。fetcher 的配置（endpoint、包列表、白名单）都在注册表里。"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.lib.store import DATA


def load(data_dir: Path = DATA) -> dict:
    path = data_dir / "sources.yml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def source_config(source: str, data_dir: Path = DATA) -> dict:
    cfg = load(data_dir).get(source)
    if cfg is None:
        raise KeyError(f"data/sources.yml 中没有源 {source!r}")
    return cfg
