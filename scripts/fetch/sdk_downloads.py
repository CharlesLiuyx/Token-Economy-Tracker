"""SDK 下载量：npm (api.npmjs.org) + pypi (pypistats.org)，均为官方/公开 API。

口径与坑见 docs/sources/sdk_downloads.md。包列表配置在 data/sources.yml。
"""

from __future__ import annotations

import sys
import time
from datetime import date, datetime, timezone
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
# IP 被邻居 job 耗尽突发桶时不够（见 09-02/09-03/09-04 连续三日复发）。经验上端点约
# 30–60s/包就会恢复，故对「429 且 body 无 data」再补几轮长间隔重试，把整源丢一天的概率压到最低。
#
# 09-04 复盘：4×18s（约 5.5min，含 net 层退避）仍被 CI 共享 IP 的持续限流击穿——当日
# anthropic 包连续 ~5 次尝试跨越 5m28s 都没等到限流窗口清空（同一时刻本地异 IP 首拉即成）。
# 每次耐心尝试真正贡献的是「多一个 net.get_json 周期（约 48s 退避）＝多给 CI IP 一个恢复窗口」，
# 故加大**尝试次数**（拓宽总等待窗口）比单纯拉长单次 sleep 更有效。7×20s 把总耐心窗口从
# ~5.5min 拓到 ~9min，提高在 CI 内自愈的概率、减少对巡检回补的依赖。
# 注：真正与「CI 共享出口 IP」解耦的通路（BigQuery pypi 公共数据集）需人类提供 GCP 凭据，
# 非无人值守巡检可自助，故先做此可自助的加固；若本预算仍被击穿，再评估引入凭据走 BigQuery。
PYPI_NODATA_429_RETRIES = 7
PYPI_NODATA_429_SLEEP_S = 20.0

# npm 官方下载量 API 偶发「冻结」：连续多日 200 返回同一 last-day.end 的陈旧数据而非报错
# （见 2026-08-29→09-07 连续 9 日冻结，Issue #2）。validate 原本只查 last-week>0，会让陈旧
# 数据每天静默落盘、series 被假新鲜的重复值污染。故加新鲜度守卫：npm 最新 last-day.end 落后
# 当日 UTC 超过阈值即判失败，让冻结显性化到 _status.json（宁可当天留缺口，也不写重复陈旧值），
# 供每日巡检发现。阈值 4 天以容忍正常 1–2 日滞后 + 周末规律性延迟，同时在冻结数日内即触发。
# 注：pypistats /recent 只返回滚动汇总数（last_day/week/month）、无日期字段，无法据此守卫。
NPM_STALE_MAX_DAYS = 4


def _parse_iso_date(value) -> date | None:
    """把 npm 响应里的 YYYY-MM-DD 解析成 date；非法/缺失返回 None（跳过、不新增失败面）。"""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


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
    ends: list[date] = []
    for pkg, entry in payload["npm"].items():
        schema.require_keys(entry, ["last-day", "last-week"], where=f"npm.{pkg}")
        schema.require_positive_number(
            entry["last-week"]["downloads"], where=f"npm.{pkg}.last-week.downloads"
        )
        end = _parse_iso_date(entry["last-day"].get("end"))
        if end is not None:
            ends.append(end)
    # 新鲜度守卫：npm 上游冻结检测（见 NPM_STALE_MAX_DAYS 说明）。
    if ends:
        freshest = max(ends)
        lag = (datetime.now(timezone.utc).date() - freshest).days
        if lag > NPM_STALE_MAX_DAYS:
            raise schema.SchemaError(
                f"npm 疑似上游冻结：最新 last-day.end={freshest.isoformat()}，"
                f"落后当日 {lag} 天（>{NPM_STALE_MAX_DAYS}），拒绝写入陈旧数据"
            )
    for pkg, entry in payload["pypi"].items():
        schema.require_keys(entry, ["last_week"], where=f"pypi.{pkg}")
        schema.require_positive_number(entry["last_week"], where=f"pypi.{pkg}.last_week")


def main(argv: list[str] | None = None) -> int:
    return runner.run(SOURCE, fetch, validate, argv)


if __name__ == "__main__":
    raise SystemExit(main())
