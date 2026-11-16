# Adding a database

How the documentation is organised, and what to write when a new DATASUS system (SIH,
SIM, SINASC, CNES, ...) or a new table is added. The aim is that a newcomer can find the
right table, understand what one row is, and write a correct query, without reading
everything.

For the code side of a new SIA file type, see [Development](development.md#adding-a-new-sia-file-type).

## Layout

```text
docs/
  index.md                 home: what this is, the databases, where to start
  getting-started.md       tutorial: install, fetch, first queries (uses SIA)
  concepts.md              terms shared by every system; how data is stored
  guide/                   how to use the tool: fetching.md, querying.md
  databases/
    index.md               catalog of DATASUS systems, status, shared codes
    sia/                   one folder per system
      index.md             overview: what it records, "which table do I need?", tables at a glance
      data-notes.md        pitfalls specific to this system
      examples.md          SQL cookbook
      joins.md             joins between its tables, double counting, sources
      <table>.md           one page per table
    sih/                   (next system: same files)
  lookups/                 reference data shared by every system (ufs, SIGTAP, CID-10, CBO)
  contributing/            this page, development.md
  reference/               Python API (generated)
```

Content that applies to more than one system goes **up** a level: a code table used by SIA
and SIH goes in `lookups/`, a term in `concepts.md`. Content about one system stays in its
folder.

## Checklist for a new database

1. **Create `docs/databases/<system>/`** with the five pages below. Use the system's
   usual lower-case acronym (`sih`, `sim`, `sinasc`, `cnes`).
2. **Overview (`index.md`)**, in this order:
    - what the system records, in one paragraph a non-specialist understands, and what it
      does *not* cover (with a link to the system that does);
    - *Start here*: links to the pitfalls and the cookbook;
    - how the source records care (the forms or instruments, if they matter for counting);
    - **Which table do I need?**: a table from questions ("How many admissions for
      pneumonia?") to tables;
    - **Tables at a glance**: table, *one row is*, fetch flag, coverage;
    - size of a typical download.
3. **Pitfalls (`data-notes.md`)**: the few rules that prevent wrong answers, most important
   first, each with a short SQL showing the right way. Think: what does a row stand for,
   which records are duplicated elsewhere, which month is which, what does "not informed"
   look like, what is missing.
4. **Cookbook (`examples.md`)**: queries that answer **meaningful questions** (spending, use,
   access, equity, trends, public health topics), grouped by theme, each under a heading
   phrased as the question. Rules:
    - every query runs as written on the data named at the top of the page; run them all
      before merging;
    - filter on `competencia` (and `uf` where it makes sense);
    - say in one or two sentences what the result shows, with the real number when it is
      striking ("Surgical procedures fell 58% between May/2019 and May/2020");
    - use the lookups so results show names, not codes;
    - end with a table linking to the examples on the table pages.
5. **Joins (`joins.md`)**: the join map (to the lookups and between tables), which tables
   repeat the same records, and the official layout sources.
6. **One page per table**, using the template below.
7. **Wire it up:**
    - add the system's pages to `nav` in `mkdocs.yml`, under *Databases*, in the same order
      as SIA (Overview, Pitfalls, SQL cookbook, Joins, then tables);
    - change its status to *Available* in `docs/databases/index.md` and on the home page;
    - add any new code table to `docs/lookups/index.md`, and any new term to
      `docs/concepts.md`;
    - add a short paragraph and a link to `README.md`;
    - run `uv run mkdocs build --strict` (needs `uv sync --group docs`): it fails on any broken
      link or anchor.

## Table page template

Every table page follows the same order, so readers know where to look. Copy the structure
of [`pa`](../databases/sia/pa.md) (a main table) or [`am`](../databases/sia/am.md) (a table
that shares columns described on another page).

````markdown
# <table> — <what it is, in plain words>, <period>

**Source:** file names and FTP folder.
**Coverage:** first and last month, states.
**Fetch:** `uv run datasus fetch -T <code> -s AC -f 2026`.

What one row is, in one or two sentences, and what you can learn from this table that
you can't from the main one.

!!! warning "How to count"
    The column to sum, or why `COUNT(*)` is right here.

## How <table> relates to <main table> (double counting)

Which records are the same, the check that proves it, and a "You want → Use" table.

## <table> vs <table>_raw

Which columns the typed view casts.

## Columns

Grouped by theme (facility, time, procedure, patient, diagnosis, values, ...). For each
column: name, type, size, official description (translated), and notes with the codes and
values actually seen.

## Joins

To the lookups and to other tables.

## Known quirks and layout changes

Anything that changes over time or differs from the official layout.

## Examples

2–5 queries answering real questions, each with a comment line saying what it answers.
````

## Style

- Write for someone who knows SQL but not DATASUS. Explain an acronym the first time a
  page uses it, or link to [Key concepts](../concepts.md).
- Keep official Portuguese terms in italics with an English gloss: *competência*
  (reference month).
- Put numbers where they help ("51% of procedures have no patient data") and say which
  state and month they were checked on.
- Prefer a table to a long sentence listing cases.
- Link anchors, not just pages: `[bi](bi.md#how-bi-relates-to-pa-double-counting)`.
