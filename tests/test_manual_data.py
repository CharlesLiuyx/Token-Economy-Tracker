"""人工 / agent 维护数据的双语护栏：页面英文模式不允许漏出中文（docs/frontend.md「i18n」）。"""
import re
from pathlib import Path

import yaml

MANUAL = Path(__file__).resolve().parents[1] / "data" / "manual"
CJK = re.compile(r"[\u4e00-\u9fff]")


def _load(name: str) -> dict:
    return yaml.safe_load((MANUAL / name).read_text(encoding="utf-8"))


def test_digest_items_are_bilingual_and_sourced():
    for day in _load("digest.yml")["digest"]:
        for it in day["items"]:
            assert it["tag"] and it["source_url"], it
            assert it["text"]["zh"].strip() and it["text"]["en"].strip(), it
            assert not CJK.search(it["text"]["en"]), f"en 文案里有中文: {it['text']['en']}"


def test_anchor_notes_with_chinese_have_english():
    for a in _load("arr_anchors.yml")["anchors"]:
        if CJK.search(str(a.get("note") or "")):
            assert a.get("note_en") and not CJK.search(a["note_en"]), a


def test_quote_roles_with_chinese_have_english():
    for q in _load("quotes.yml")["quotes"]:
        if CJK.search(str(q.get("role") or "")):
            assert q.get("role_en") and not CJK.search(q["role_en"]), q
