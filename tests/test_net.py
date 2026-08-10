"""net.get 的重试行为单测（不打真网络）：重点覆盖 pypistats 式 429 软限流。"""

import pytest
import requests

from scripts.lib import net


class _FakeResp:
    def __init__(self, status_code, *, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = {} if payload is None else payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error for url")


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """把退避 sleep 换成记录器，测试不真的等待。"""
    slept = []
    monkeypatch.setattr(net.time, "sleep", lambda s: slept.append(s))
    return slept


def _seq_getter(responses):
    it = iter(responses)

    def _get(url, params=None, headers=None, timeout=None):
        return next(it)

    return _get


def test_429_then_success_retries(monkeypatch, _no_real_sleep):
    responses = [_FakeResp(429), _FakeResp(429), _FakeResp(200, payload={"ok": 1})]
    monkeypatch.setattr(net.requests, "get", _seq_getter(responses))
    assert net.get_json("http://x") == {"ok": 1}
    assert len(_no_real_sleep) == 2  # 两次 429 各退避一次


def test_429_exhausts_and_raises(monkeypatch, _no_real_sleep):
    monkeypatch.setattr(net.requests, "get", _seq_getter([_FakeResp(429)] * 4))
    with pytest.raises(requests.HTTPError):
        net.get("http://x", retries=4)


def test_429_respects_retry_after_when_longer(monkeypatch, _no_real_sleep):
    responses = [_FakeResp(429, headers={"Retry-After": "30"}), _FakeResp(200)]
    monkeypatch.setattr(net.requests, "get", _seq_getter(responses))
    net.get("http://x")
    assert _no_real_sleep[0] == 30.0  # 尊重比默认退避更长的 Retry-After


def test_success_no_sleep(monkeypatch, _no_real_sleep):
    monkeypatch.setattr(net.requests, "get", _seq_getter([_FakeResp(200, payload=[])]))
    assert net.get_json("http://x") == []
    assert _no_real_sleep == []
