"""守住硬约束 5：注册的每个源必须有 fetcher 脚本 + docs/sources 文档。"""

from scripts.lib import registry
from scripts.lib.store import ROOT


def test_registered_sources_have_files():
    for name, cfg in registry.load().items():
        assert "kind" in cfg, f"{name}: 缺 kind"
        fetcher = cfg.get("fetcher")
        if fetcher:
            assert (ROOT / fetcher).exists(), f"{name}: fetcher 不存在 {fetcher}"
            assert int(cfg.get("refetch_window_days", 3)) >= 0
        doc = cfg.get("doc")
        assert doc and (ROOT / doc).exists(), f"{name}: doc 不存在 {doc}"


def test_fetcher_modules_expose_contract():
    import importlib

    for name, cfg in registry.load().items():
        if not cfg.get("fetcher"):
            continue
        mod = importlib.import_module(
            cfg["fetcher"].removesuffix(".py").replace("/", ".")
        )
        assert mod.SOURCE == name
        assert callable(mod.fetch) and callable(mod.validate)
