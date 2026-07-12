"""轻量 schema 断言：校验失败 => 抓取失败 => 不写入坏数据，保留上次 latest。"""

from __future__ import annotations


class SchemaError(Exception):
    pass


def require_keys(obj: dict, keys: list[str], where: str = "payload") -> None:
    if not isinstance(obj, dict):
        raise SchemaError(f"{where}: 应为 dict，实际 {type(obj).__name__}")
    missing = [k for k in keys if k not in obj]
    if missing:
        raise SchemaError(f"{where}: 缺少字段 {missing}")


def require_type(value, expected: type | tuple, where: str) -> None:
    if not isinstance(value, expected):
        raise SchemaError(f"{where}: 应为 {expected}，实际 {type(value).__name__}")


def require_nonempty_list(value, where: str) -> None:
    require_type(value, list, where)
    if not value:
        raise SchemaError(f"{where}: 列表为空")


def require_positive_number(value, where: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise SchemaError(f"{where}: 应为正数，实际 {value!r}")
