import pytest

from scripts.lib import schema


def test_require_keys():
    schema.require_keys({"a": 1, "b": 2}, ["a", "b"])
    with pytest.raises(schema.SchemaError, match="缺少字段"):
        schema.require_keys({"a": 1}, ["a", "b"])


def test_require_positive_number():
    schema.require_positive_number(3.5, "x")
    for bad in (0, -1, None, "5", True):
        with pytest.raises(schema.SchemaError):
            schema.require_positive_number(bad, "x")


def test_require_nonempty_list():
    schema.require_nonempty_list([1], "x")
    with pytest.raises(schema.SchemaError):
        schema.require_nonempty_list([], "x")
