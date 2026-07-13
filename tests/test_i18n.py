"""i18n 防腐化：文案唯一出处 site/template/i18n.yml，模板/spec 只引用 key。

三道闸：目录完整（zh/en 齐全非空）、{args} 双语一致、引用与目录双向对齐
（引用不存在的 key 或目录里有死 key 都失败）。
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "site" / "template"
KEY_RE = r"(?:ui|sec|panel|chart|meth)\.[a-z0-9_]+(?:\.[a-z0-9_]+)*"


def load_catalog() -> dict:
    return yaml.safe_load((TEMPLATE / "i18n.yml").read_text(encoding="utf-8"))


def referenced_keys() -> set[str]:
    """扫源码里的 key 引用。Python 里 key 只能经 t()/L() 进入（避免误匹配
    'chart.umd.min.js' 这类文件名字面量）；模板里扫全部 key 字面量与 __i18n: token。"""
    used: set[str] = set()
    py = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    used |= set(re.findall(r"\b[tL]\(\s*[\"']({})[\"']".format(KEY_RE), py))
    for p in [*TEMPLATE.glob("*.j2"), *(TEMPLATE / "panels").glob("*.j2")]:
        text = p.read_text(encoding="utf-8")
        used |= set(re.findall(r"[\"']({})[\"']".format(KEY_RE), text))
        used |= set(re.findall(r"__i18n:({})".format(KEY_RE), text))
    return used


def test_entries_have_all_langs():
    cat = load_catalog()
    assert cat, "i18n.yml 为空"
    for key, entry in cat.items():
        assert re.fullmatch(KEY_RE, key), f"key 命名不合规: {key}"
        assert isinstance(entry, dict) and set(entry) == {"zh", "en"}, f"{key} 语言不齐"
        assert all(isinstance(v, str) and v.strip() for v in entry.values()), f"{key} 有空文案"


def test_placeholder_args_match_across_langs():
    for key, entry in load_catalog().items():
        args = {lang: set(re.findall(r"\{(\w+)\}", s)) for lang, s in entry.items()}
        assert args["zh"] == args["en"], f"{key} 的 {{name}} 参数双语不一致: {args}"


def test_referenced_keys_exist_and_no_dead_keys():
    cat, used = set(load_catalog()), referenced_keys()
    assert not used - cat, f"引用了 i18n.yml 里不存在的 key: {sorted(used - cat)}"
    assert not cat - used, f"i18n.yml 有未被引用的死 key: {sorted(cat - used)}"
