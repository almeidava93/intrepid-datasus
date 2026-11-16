# Fetching data

`datasus fetch` downloads files from the DATASUS FTP, converts them to Parquet and stores
them under `./data` (see [how data is stored](../concepts.md#how-data-is-stored)). Every
command below works the same way for every file type.

## Look before you download

```bash
# what's on the FTP for SP in 2025, and how big (nothing is downloaded)
uv run datasus available -s SP -f 2025

# the plan for a fetch, without running it
uv run datasus fetch -s all -f 2024 --dry-run
```

## Fetch

```bash
# one state, one year
uv run datasus fetch -s SP -f 2025

# several states, a range of months
uv run datasus fetch -s SP,RJ,MG -f 202401 -t 202406

# a region, or the whole country
uv run datasus fetch -s Nordeste -f 2025
uv run datasus fetch -s all -f 202605

# other SIA file types (pa is the default)
uv run datasus fetch -T aq -s SC -f 2025          # chemotherapy APACs
uv run datasus fetch -T pa,atd -s SE -f 202605    # two file types
uv run datasus fetch -T all -s AC -f 202605       # every file type

# procedure, diagnosis and occupation names (SIGTAP)
uv run datasus sigtap fetch
```

## Options

| Option | Meaning |
|---|---|
| `--table/-T` | Which file types: a code like `pa`, several like `pa,bi`, or `all`. Default `pa`. The codes are listed in `datasus fetch --help` and on the [SIA overview](../databases/sia/index.md#tables-at-a-glance). Note the capital `-T`: lower-case `-t` is `--to`. |
| `--states/-s` | `all` (default), codes like `SP,RJ`, or a region: `Norte`, `Nordeste`, `Sudeste`, `Sul`, `Centro-Oeste`. |
| `--from/-f`, `--to/-t` | `YYYY` or `YYYYMM`. `--to` defaults to the end of `--from` (`-f 2025` = all of 2025). |
| `--workers/-w` | Parallel downloads (default 3). |
| `--dry-run` | Show the plan only. |
| `--force` | Download again even if up to date. |
| `--keep-dbc` | Keep the original `.dbc` files. |
| `--yes/-y` | Don't ask for confirmation. |

`available`, `status` and `remove` take the same `-T`, `-s`, `-f`, `-t` options (`schema` takes `-T`).

To keep data somewhere other than `./data`, set `DATASUS_DATA_DIR` or pass `--data-dir/-d`
**before** the command: `uv run datasus -d /mnt/big/datasus fetch -s SP -f 2025`.

## Keeping data up to date

Re-running the same command is safe and cheap: state-months that match the FTP are skipped;
any whose files changed (DATASUS silently revises recent months, and sometimes re-splits
them into parts) are rebuilt. An interrupted run resumes where it stopped.

```bash
uv run datasus status              # what's stored locally (pa)
uv run datasus status -T all       # ... for every file type
uv run datasus remove -s RR -f 2026   # delete local data
```

## How much space?

| What | Download | Parquet |
|---|---|---|
| PA, one month, all 27 states (May/2026) | ~2.7 GB | ~1 GB, ~71M rows |
| PA, one year, all states | | ~11–13 GB |
| BI, 2008–2026, all states | ~188 GB | ~0.4× that |
| PA, one month of Acre | a few MB | |

While converting, each worker needs a few GB of temporary disk. Start with one state and
one month, then grow.
