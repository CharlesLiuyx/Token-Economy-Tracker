"""HTTP 封装：统一 UA、超时、指数退避重试。fetcher 一律走这里发请求。"""

from __future__ import annotations

import time

import requests

UA = "Token-Tracker/0.1 (AI monetization dashboard; github.com/token-tracker)"
DEFAULT_TIMEOUT = 30


def _retry_after_seconds(resp: requests.Response, fallback: float) -> float:
    """429 时优先尊重 Retry-After 头，否则用调用方给的退避值。"""
    raw = resp.headers.get("Retry-After")
    if raw:
        try:
            return max(float(raw), fallback)
        except ValueError:
            pass  # Retry-After 也可能是 HTTP-date，忽略后走 fallback
    return fallback


def get(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 4,
    backoff: float = 2.0,
) -> requests.Response:
    merged = {"User-Agent": UA}
    if headers:
        merged.update(headers)
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=merged, timeout=timeout)
            # 429 软性限流（如 pypistats）：退避更久再重试，而非立刻放弃。
            if resp.status_code == 429:
                if attempt < retries - 1:
                    time.sleep(_retry_after_seconds(resp, 8.0 * (attempt + 1)))
                    last_exc = requests.HTTPError(f"429 Too Many Requests for url: {url}")
                    continue
                resp.raise_for_status()
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
