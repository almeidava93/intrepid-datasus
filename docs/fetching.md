# Fetching data

```bash
# what's on the FTP, and how big (nothing is downloaded)
uv run datasus available -s SP -f 2025

# one state, one year
uv run datasus fetch -s SP -f 2025

# several states, a range of months
uv run datasus fetch -s SP,RJ,MG -f 202401 -t 202406

# a region, or the whole country
uv run datasus fetch -s Nordeste -f 2025
uv run datasus fetch -s all -f 202605

# preview the plan first
uv run datasus fetch -s all -f 2024 --dry-run

# choose the SIA file type(s): pa is the default
uv run datasus fetch -T pa -s AC -f 202605
uv run datasus fetch -T all -s AC -f 202605
```

- `--table/-T`: which SIA file types (tables) to work on: a code like `pa`, several like
  `pa,bi`, or `all`. Default: `pa`, so commands without it behave as they always have.
  `available`, `fetch`, `status`, `schema` and `remove` all take it. Each file type is one
  table family (see [Tables](tables/index.md)); the registered ones are listed in
  `datasus fetch --help`. (`-t` is `--to`; the table flag is a capital `-T`.)
- `--states/-s`: `all` (default), codes like `SP,RJ`, or a region: `Norte`, `Nordeste`,
  `Sudeste`, `Sul`, `Centro-Oeste`.
- `--from/-f`, `--to/-t`: `YYYY` or `YYYYMM`. `--to` defaults to the end of `--from`.
- `--workers/-w` (default 3), `--force`, `--keep-dbc`, `--yes/-y`.

Re-running the same command is safe and cheap: state-months that match the FTP are skipped;
any whose files changed (DATASUS silently revises recent months, and sometimes re-splits
them into parts) are rebuilt. An interrupted run resumes where it stopped.

**Sizes** (May/2026, all 27 states): ~2.7 GB to download, ~1 GB as Parquet, ~71M rows.
A year is roughly 11–13 GB of Parquet. While converting, each worker needs a few GB of
temporary disk.
