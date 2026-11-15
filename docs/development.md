# Development

```bash
uv run pytest
```

Source: `src/intrepid_datasus/` — `catalog.py` (FTP listing, states, periods), `convert.py`
(.dbc → Parquet), `store.py` (local layout and manifest), `fetch.py`, `query.py` (DuckDB views),
`dictionary.py` (column descriptions), `cli.py`.

## Data source

Data: Ministério da Saúde / DATASUS, SIA/SUS. Cite DATASUS when publishing results.

## CI/CD

- **CI** (`.github/workflows/ci.yml`): runs the test suite on Python 3.11–3.13 (Linux) and
  3.12 (Windows), and builds the sdist/wheel, on every pull request and push to `main`.
- **Docs** (`.github/workflows/docs.yml`): builds this site with `mkdocs build --strict` on
  every pull request; on pushes to `main` it deploys to GitHub Pages.
- `main` is protected: changes go through a pull request with one approving review.

## Docs

```bash
uv sync --group docs
uv run mkdocs serve      # live preview at http://127.0.0.1:8000
```
