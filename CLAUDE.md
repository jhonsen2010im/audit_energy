# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`audit-leads` — a Python CLI tool that finds, scores, and tracks prospects for energy audit services. Single Click-based binary backed by a local SQLite database.

## Commands

```bash
# Install the package and the `audit-leads` console entry point in editable mode
pip install -e .

# Run the full test suite
pytest tests/

# Run a single test file or test
pytest tests/test_scoring.py
pytest tests/test_scoring.py::test_score_lead_all_high

# Invoke the CLI (after install). All subcommands take an optional --db path
# that defaults to ./leads.db in the current working directory.
audit-leads --help
audit-leads --db /tmp/work.db list --min-score 60
```

There is no separate lint/format config; match existing style.

## Architecture

The codebase is a small layered Python package. Reading `cli.py` alone is misleading because it just dispatches to the modules below.

### Click + Database lifecycle (`audit_leads/cli.py`)

The root `@click.group` opens a `Database` once and stashes it on `ctx.obj`; every subcommand declares `@click.pass_obj` to receive it. A `@cli.result_callback()` (`cleanup`) closes the connection after the command finishes — do not open/close the DB inside individual commands. When adding a new command, follow this pattern instead of constructing a `Database` yourself.

### Storage (`audit_leads/db.py`)

`Database` is a thin wrapper over stdlib `sqlite3` (no ORM). Schema is created idempotently in `init_db()` with three tables: `leads`, `contacts` (FK to leads, `ON DELETE CASCADE`), `interactions` (FK to leads). Foreign keys are enabled per-connection via `PRAGMA foreign_keys = ON`.

`add_lead` and `update_lead` accept arbitrary `**kwargs` but **whitelist** the columns they will actually write. When you add a column to the schema, you must also extend the whitelist set in both methods or writes will silently drop the field. `lead_exists(company, address)` is the dedup primitive used by importers — prefer it over ad-hoc duplicate checks.

### Scoring (`audit_leads/scoring.py`)

Pure functions, no I/O except `score_all_leads(db)`. Four factors with equal `WEIGHTS` (each 0.25): building age, building size, industry, energy spend. Each `_score_*` helper returns 0–100; **missing inputs return 50.0** (neutral) rather than 0.0, so partial leads aren't penalized like bad leads. `explain_score` mirrors `score_lead` and must be kept in sync — both call the same `_score_*` helpers, so add new factors in one place and wire them into both dicts plus `WEIGHTS`. `score_all_leads` only writes rows whose computed score actually changed.

### Lead sources (`audit_leads/sources/`)

Three pluggable importers, each with the same contract: take a `Database` and write leads via `db.add_lead(..., source=<name>)` after checking `db.lead_exists(...)`.

- `csv_import.py` — the most reliable source. `DEFAULT_COLUMN_MAP` maps canonical field names to lists of accepted CSV header aliases (case/space-insensitive). Numeric fields strip `$` and `,` before parsing. New header variants belong in this map. Sets `source="csv_import"`.
- `scraper.py` — framework only. `scrape_commercial_listings` is a stub with the requests/BeautifulSoup pattern in a comment; `scrape_government_energy_data` just prints links to public benchmarking portals (NYC LL84, Chicago, Seattle) and tells the user to download + `import-csv`. Both gracefully degrade when `requests`/`bs4` aren't installed (`HAS_DEPS` flag).
- `search.py` — uses SerpAPI when `SERPAPI_KEY` is set; otherwise prints manual-search suggestions and returns 0. Do not hard-fail when the key is missing.

### Outreach (`audit_leads/outreach.py`)

Renders `audit_leads/templates/email_*.txt` and `call_script.txt` with `string.Template.safe_substitute` so missing keys render as `$key` rather than raising. `_build_context` derives the context dict from a lead + its contacts; it picks the `is_primary` contact (or the first one), computes a `building_description` string from sqft/year, and selects a tier-based `score_reason`. When adding a placeholder to a template, also add it to `_build_context`. `list_templates()` discovers email templates by scanning the directory for `email_*.txt`, so naming matters.

## Conventions specific to this repo

- DB path defaults to `./leads.db` and is gitignored (`*.db`).
- The `source` column is a free-form string; existing values are `manual`, `csv_import`, `scrape`, `search`. Pick one of these (or add a new one consistently) when introducing a new importer.
- Lead status enum is duplicated as a `click.Choice` in `cli.py` (`new`, `contacted`, `qualified`, `proposal`, `won`, `lost`). If you add a status, update both the CLI choices and any docs.
- Tests use `tempfile.mkstemp` + `Database(path)` fixtures — there is no in-memory DB shortcut. Follow the existing fixture pattern in `tests/test_db.py` and `tests/test_csv_import.py`.
- Type hints use PEP 604 union syntax (`int | None`); the package targets modern Python.
