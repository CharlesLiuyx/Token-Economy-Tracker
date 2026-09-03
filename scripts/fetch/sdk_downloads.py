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
PYPI_REQUEST_SPACING_S = 10.0

# 无数据 429 的包级耐心重试：net 层退避（8→16→24→放弃，约 48s）在 CI 共享出口
# IP 被邻居 job 耗尽突发桶时不够（见 09-02/09-03 复发）。经验上端点约 30–60s/包
# 就会恢复，故对「429 且 body 无 data」再补几轮长间隔重试，把整源丢一天的概率压到最低。
PYPI_NODATA_429_RETRIES = 4
PYPI_NODATA_429_SLEEP_S = 18.0


def _pypi_recent(pkg: str) -> dict:
    """取单个 pypi 包的 recent 下载量。

    pypistats 的 429 有两种形态，都要兜住，否则整源会因为一个包的限流丢掉一整天
    （历史复发点见 docs/sources/sdk_downloads.md）：

    1. **429 带有效数据**（老形态，限流走 CDN 缓存、数据照发）：net 层退避重试后
       若仍 429，只要 body 能解析出 `data` 就直接采用。
    2. **429 无数据**（新形态，53b HTML 限流页，无 `data`）：net 层退避（约 48s）
       不足以躲过 CI 共享 IP 的持续限流，故再做包级耐心重试——端点约 30–60s/包
       即恢复，多等几轮长间隔通常就能拿到 200。

    两种都失败才向上抛。"""
    url = PYPISTATS_RECENT.format(package=pkg)
    for attempt in range(PYPI_NODATA_429_RETRIES + 1):
        try:
            return net.get_json(url)
        except requests.HTTPError as exc:
            resp = getattr(exc, "response", None)
            if resp is None or resp.status_code != 429:
                raise
            try:
                body = resp.json()
            except ValueError:
                body = None
            if isinstance(body, dict) and body.get("data"):
                return body  # 形态 1：429 但带数据，直接用
            if attempt < PYPI_NODATA_429_RETRIES:
                time.sleep(PYPI_NODATA_429_SLEEP_S)  # 形态 2：无数据 429，耐心再等
                continue
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
