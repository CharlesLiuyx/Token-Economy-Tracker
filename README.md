# Token Economy Tracker

[![daily-update](https://github.com/CharlesLiuyx/Token-Economy-Tracker/actions/workflows/daily.yml/badge.svg)](https://github.com/CharlesLiuyx/Token-Economy-Tracker/actions/workflows/daily.yml)

**Live dashboard → <https://charlesliuyx.github.io/Token-Economy-Tracker/>**

A daily auto-updating **AI monetization dashboard**. The build artifact is a pure
static, single-file HTML page (Chart.js inlined, no CDN, works offline), refreshed
once a day by GitHub Actions and served on GitHub Pages.

## What it tracks

1. **Frontier Lab ARR (live estimate)** — big live-ticking ARR numbers for
   Anthropic / OpenAI, built from publicly disclosed anchors + curve fitting +
   extrapolation with confidence bands.
2. **Token demand & adoption** — OpenRouter model token usage (per-model, model
   comparison, network-wide total, weekly Top Models), Vercel AI Gateway share
   (Token / $ Spend Top 10 + trends), SDK downloads (npm / PyPI), expert quotes,
   and Epoch AI Top Sites.
3. **GPU rental prices** — $/GPU-hr cards for H100 / H200 / B200 / A100 /
   RTX 5090, plus price trend charts.
4. **AI datacenter buildout** — summary cards from the Epoch AI Frontier Data
   Centers dataset (site count / IT power GW / H100-equivalents), cumulative
   industry growth, and a daily news feed.

## How it works

```
GitHub Actions cron (daily)
        │
        ▼
scripts/fetch/*        one independent fetcher per source; a single source
        │              failing never blocks the run
        ▼
data/                  append-only daily JSON snapshots + latest.json per source
        │
        ▼
scripts/build.py       renders everything into one file
        │
        ▼
site/index.html        single-file static dashboard (GitHub Pages / open locally)
```

Design principles: fetch and build are fully decoupled (either half can be rerun
independently), history is append-only (any chart can be redrawn from raw
snapshots at any time), and there is no server or runtime network request.

**Stack:** Python 3.12 (`requests` / `pyyaml` / `numpy` / `jinja2` — deliberately
minimal) and vanilla JS with a vendored Chart.js inlined at build time.

## Data sources

| Source | Kind | What it provides |
|---|---|---|
| OpenRouter | unofficial API | Model token usage + weekly rankings |
| Vercel AI Gateway | unofficial API | Gateway token / spend leaderboards |
| npm + PyPI | official APIs | AI SDK download counts |
| Epoch AI | official dataset (CC-BY) | Frontier data centers dataset |
| GPU price indexes | web | GPU rental $/GPU-hr |
| Google News RSS | unofficial API | Datacenter news feed (domain-whitelisted) |
| Manual anchors | git-maintained | Publicly disclosed ARR data points |

Each source is registered in [data/sources.yml](data/sources.yml) and documented
in [docs/sources/](docs/sources/).

## Quick start

```bash
make venv     # create virtualenv and install dependencies
make update   # run all fetchers (each source independently)
make build    # data/ -> site/index.html
make serve    # preview locally
make test     # run the test suite

make fetch-<source>   # debug a single fetcher, e.g. make fetch-openrouter
```

## Hard rules

- `data/**/daily/` snapshots are immutable (append-only history).
- `site/index.html` is a build artifact — never edit it by hand; only
  `make build` may generate it.
- No external CDNs or runtime network requests; the page must open offline.
- Behavior changes must update the corresponding docs in the same PR.
- A new data source ships as a trio: `data/sources.yml` entry +
  `docs/sources/<source>.md` + a response sample.

## Commit message convention

Format: `<type>: <summary>` — written in English, imperative mood, no trailing
period, summary ≤ 72 characters. Add a body only when the *why* isn't obvious.

| Type | Use for |
|---|---|
| `feat` | New panel, fetcher, or user-visible capability |
| `fix` | Bug fix in pipeline, build, or frontend |
| `data` | Data snapshot updates or manual anchor additions |
| `docs` | Documentation only |
| `build` | Build script, Makefile, or dependency changes |
| `ci` | GitHub Actions workflow changes |
| `refactor` | Code restructuring with no behavior change |
| `test` | Test-only changes |
| `chore` | Anything else (housekeeping) |

Examples:

```
feat: add GPU price trend panel
data: add 2 ARR anchors (YipitData, as of 2026-06-30)
fix: handle empty OpenRouter rankings response
```

Automated daily commits from CI use `data: YYYY-MM-DD`.

## Documentation

Docs follow progressive disclosure: start at [AGENTS.md](AGENTS.md) (entry point
with a task routing table), then [docs/INDEX.md](docs/INDEX.md) for the full map —
plan, architecture, conventions, runbook, ARR methodology, per-source docs, and
ADRs. Most internal docs are written in Chinese.
