"""SDK 下载量：npm (api.npmjs.org) + pypi (pypistats.org)，均为官方/公开 API。

口径与坑见 docs/sources/sdk_downloads.md。包列表配置在 data/sources.yml。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "sdk_downloads"

NPM_POINT = "https://api.npmjs.org/downloads/point/{period}/{package}"
PYPISTATS_RECENT = "https://pypistats.org/api/packages/{package}/recent"

# pypistats.org 是按 IP 的突发限流（约每几秒 1 次，无 Retry-After 头），
# 连续拉多个包会撞 429。请求间留间隔，配合 net 层的 429 退避重试兜底。
PYPI_REQUEST_SPACING_S = 6.0


def _pypi_recent(pkg: str) -> dict:
    """取单个 pypi 包的 recent 下载量。

    pypistats 在 IP 突发限流下常返回 **429，但响应体仍带有效数据**（限流走
    CDN 缓存，数据照发）。net 层退避重试后若仍 429，只要 body 能解析出 `data`
    就采用它——否则整源会因为一个包的限流丢掉一整天（历史复发点见
    docs/sources/sdk_downloads.md）。真正拿不到 data 时才向上抛。"""
    url = PYPISTATS_RECENT.format(package=pkg)
    try:
        return net.get_json(url)
    except requests.HTTPError as exc:
        resp = getattr(exc, "response", None)
        if resp is not None and resp.status_code == 429:
            try:
                body = resp.json()
            except ValueError:
                body = None
            if isinstance(body, dict) and body.get("data"):
                return body
        raise


def fetch(cfg: dict) -> dict:
    out: dict = {"npm": {}, "pypi": {}}
    for pkg in cfg["npm_packages"]:
        entry = {}
        for period in ("last-day", "last-week"):
            data = net.get_json(NPM_POINT.format(period=period, package=pkg))
            entry[period] = {
                "downloads": data.get("downloads"),
                "start": data.get("start"),
                "end": data.get("end"),
            }
        out["npm"][pkg] = entry
    for i, pkg in enumerate(cfg["pypi_packages"]):
        if i:
            time.sleep(PYPI_REQUEST_SPACING_S)  # 避免撞 pypistats 突发限流
        data = _pypi_recent(pkg)  # 429-with-body 容忍见 _pypi_recent
        out["pypi"][pkg] = data.get("data", {})  # {last_day, last_week, last_month}
    return out


def validate(payload: dict) -> None:
    schema.require_keys(payload, ["npm", "pypi"])
    for eco in ("npm", "pypi"):
        if not payload[eco]:
            raise schema.SchemaError(f"{eco}: 没有任何包数据")
    for pkg, entry in payload["npm"].items():
        schema.require_keys(entry, ["last-day", "last-week"], where=f"npm.{pkg}")
        schema.require_positive_number(
            entry["last-week"]["downloads"], where=f"npm.{pkg}.last-week.downloads"
        )
    for pkg, entry in payload["pypi"].items():
        schema.require_keys(entry, ["last_week"], where=f"pypi.{pkg}")
        schema.require_positive_number(entry["last_week"], where=f"pypi.{pkg}.last_week")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
