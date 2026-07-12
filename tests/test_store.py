import datetime as dt

import pytest

from scripts.lib import store


def test_write_and_read_snapshot(tmp_path):
    path = store.write_snapshot("demo", {"x": 1}, date="2026-07-12", data_dir=tmp_path)
    assert path == tmp_path / "demo" / "daily" / "2026" / "2026-07-12.json"
    env = store.read_json(path)
    assert env["schema_version"] == store.SCHEMA_VERSION
    assert env["payload"] == {"x": 1}
    assert store.read_latest("demo", data_dir=tmp_path)["snapshot_date"] == "2026-07-12"


def test_overwrite_inside_refetch_window_allowed(tmp_path):
    today = store.utc_today()
    store.write_snapshot("demo", {"v": 1}, date=today, data_dir=tmp_path)
    store.write_snapshot("demo", {"v": 2}, date=today, data_dir=tmp_path)
    assert store.read_latest("demo", data_dir=tmp_path)["payload"] == {"v": 2}


def test_overwrite_outside_window_forbidden(tmp_path):
    old = (store.utc_now().date() - dt.timedelta(days=30)).isoformat()
    store.write_snapshot("demo", {"v": 1}, date=old, data_dir=tmp_path)
    with pytest.raises(store.ImmutableSnapshotError):
        store.write_snapshot("demo", {"v": 2}, date=old, data_dir=tmp_path)


def test_backfill_does_not_rollback_latest(tmp_path):
    store.write_snapshot("demo", {"v": "new"}, date="2026-07-12", data_dir=tmp_path)
    store.write_snapshot("demo", {"v": "old"}, date="2026-07-10", data_dir=tmp_path)
    assert store.read_latest("demo", data_dir=tmp_path)["payload"] == {"v": "new"}
