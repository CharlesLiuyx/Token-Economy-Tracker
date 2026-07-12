"""fetcher 公共入口：--date 回补参数、schema 校验、落盘、_status 上报、退出码。

每个 scripts/fetch/<source>.py 只需提供：
- SOURCE: str
- fetch(cfg) -> dict payload（网络请求 + 解析）
- validate(payload) -> None（schema 断言，失败抛 SchemaError）
"""

from __future__ import annotations

import argparse
import sys
import traceback

from scripts.lib import registry, status, store


def run(source: str, fetch_fn, validate_fn, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=f"fetch.{source}")
    parser.add_argument(
        "--date",
        default=None,
        help="回补指定日期 YYYY-MM-DD（受 sources.yml refetch_window_days 约束）",
    )
    args = parser.parse_args(argv)

    cfg = registry.source_config(source)
    try:
        payload = fetch_fn(cfg)
        validate_fn(payload)
        path = store.write_snapshot(
            source,
            payload,
            date=args.date,
            refetch_window_days=int(cfg.get("refetch_window_days", 3)),
            source_meta={"kind": cfg.get("kind", "unknown")},
        )
    except Exception as exc:  # noqa: BLE001 — 单源失败不拖垮整次运行，状态入库
        status.record(source, ok=False, error=f"{type(exc).__name__}: {exc}")
        print(f"[{source}] FAILED: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    status.record(source, ok=True)
    print(f"[{source}] ok -> {path}")
    return 0
