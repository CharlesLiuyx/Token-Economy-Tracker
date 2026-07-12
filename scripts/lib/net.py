"""HTTP 封装：统一 UA、超时、指数退避重试。fetcher 一律走这里发请求。"""

from __future__ import annotations

import time

import requests

UA = "Token-Tracker/0.1 (AI monetization dashboard; github.com/token-tracker)"
DEFAULT_TIMEOUT = 30


def get(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
    backoff: float = 2.0,
) -> requests.Response:
    merged = {"User-Agent": UA}
    if headers:
        merged.update(headers)
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=merged, timeout=timeout)
            if resp.status_code >= 500:
                raise requests.HTTPError(f"{resp.status_code} from {url}")
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001 — 重试后统一抛出
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(backoff * (2**attempt))
    raise last_exc  # type: ignore[misc]


def get_json(url: str, **kwargs) -> dict | list:
    return get(url, **kwargs).json()


def get_text(url: str, **kwargs) -> str:
    return get(url, **kwargs).text
