from scripts.lib import status


def test_success_then_failure_keeps_last_success(tmp_path):
    status.record("s1", ok=True, data_dir=tmp_path)
    first = status.load(tmp_path)["s1"]
    assert first["last_success"] and first["error"] is None

    status.record("s1", ok=False, error="boom", data_dir=tmp_path)
    after = status.load(tmp_path)["s1"]
    assert after["last_success"] == first["last_success"]
    assert after["error"] == "boom"


def test_sources_do_not_clobber_each_other(tmp_path):
    status.record("s1", ok=True, data_dir=tmp_path)
    status.record("s2", ok=False, error="x", data_dir=tmp_path)
    all_status = status.load(tmp_path)
    assert set(all_status) == {"s1", "s2"}
