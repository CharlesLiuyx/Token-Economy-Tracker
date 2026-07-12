"""SDK 下载量：npm (api.npmjs.org) + pypi (pypistats.org)，均为官方/公开 API。

口径与坑见 docs/sources/sdk_downloads.md。包列表配置在 data/sources.yml。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib import net, runner, schema

SOURCE = "sdk_downloads"

NPM_POINT = "https://api.npmjs.org/downloads/point/{period}/{package}"
PYPISTATS_RECENT = "https://pypistats.org/api/packages/{package}/recent"


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
    for pkg in cfg["pypi_packages"]:
        data = net.get_json(PYPISTATS_RECENT.format(package=pkg))
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
