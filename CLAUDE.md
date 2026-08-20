# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Custom instructions

- Don't run `make test` unless explicitly told to (but always run it before committing).

## Project Overview

**owid-grapher-py** is a Python package for creating OWID (Our World in Data) charts in Jupyter notebooks. It is a thin proxy over the `@ourworldindata/grapher` npm package: `Chart(df, config=..., columns=...)` shapes a DataFrame into the CSV Grapher reads and passes Grapher's own chart config through untouched.

**Status**: ✅ Working (experimental) - renders with the `@ourworldindata/grapher` npm package, loaded as a standalone bundle from OWID's package host. That host is behind Tailscale until the package is published publicly, so charts only render for people on OWID's Tailnet.

## Development Setup

This project uses **uv** for dependency management and **Make** for common tasks.

### Initial Setup

```bash
make .venv
```

This creates a `.venv` virtual environment with all dependencies.

## Common Commands

### Testing

```bash
# Run all checks (formatting, linting, type checking, unit tests)
make test

# Check only changed files (faster)
make check

# Run individual checks
make check-formatting    # Check code formatting with ruff
make lint                # Run ruff linting
make check-typing        # Run ty type checking
make unittest            # Run pytest tests

# Run tests on file changes
make watch
```

### Formatting

```bash
make format              # Auto-format code with ruff
```

### Running Single Tests

```bash
.venv/bin/pytest tests/test_grapher.py::test_name
```

## Architecture

### Package Structure

The project uses a **namespace package** structure under `owid/`:

- **`owid/grapher/`** - Core charting functionality
  - `__init__.py` - Main `Chart` class, config dataclasses, and iframe rendering
  - `notebook.py` - Tools for auto-generating notebooks from existing charts

- **`owid/site/`** - Integration with live OWID website
  - `__init__.py` - Functions to fetch chart configs and data from ourworldindata.org

### Core Design Patterns

#### The proxy rule

`config` and `columns` are Grapher's own chart config and column metadata. They
are never renamed or reinterpreted here — whatever the user writes reaches the JS
library. When something is missing, the fix is a key in Grapher's config, not a
new argument in this package.

The only Python-side logic is what the browser can't do: shaping the DataFrame
(entity column → `entityName`, time column → `year` or `date`, slug-safe column
names) and defaulting `selectedEntityNames`, without which line and bar charts
draw nothing.

The few genuinely Python-side arguments are snake_case to mark them out:
`entity=`, `time=` describe the DataFrame, `height=` the notebook output.

#### Typed config

`owid/grapher/config.py` is **generated** from Grapher's published JSON schema by
`scripts/generate_config_types.py` (`make config.types`). Don't edit it by hand;
bump `SCHEMA_URL` in the generator when Grapher publishes a new schema version.
It provides `GrapherConfig` (60 schema keys + 6 CSV-mode keys) and `ColumnDef`,
plus `CONFIG_KEYS`, which `Chart` uses to reject typos at runtime — a type checker
isn't watching inside a notebook.

`ColumnDef` is the one hand-written type: column metadata has no published
schema. Unknown keys there are passed through rather than rejected.

#### Rendering pipeline

1. `Chart.export()` returns the three things Grapher's loader takes: the CSV, the
   column defs and the config
2. `_generate_chart_html()` loads `grapher.css` and `grapher.standalone.min.js`
   (React included) from `GRAPHER_BUNDLE_URL` and calls
   `GrapherLoader.fromCsv(...).mount(container)`
3. `generate_iframe()` wraps that page in an iframe for Jupyter, `to_html()`
   returns it as a standalone page, and `export.py` drives it with Playwright for
   PNG/SVG

`GRAPHER_BUNDLE_URL` defaults to the pinned version on OWID's package host and can
be overridden with the `OWID_GRAPHER_BUNDLE_URL` environment variable (e.g. to
point at a locally served `dist/`). Bumping the Grapher version means changing
`GRAPHER_VERSION` in `owid/grapher/__init__.py`. The package's own docs live in
the owid-grapher repo at `packages/@ourworldindata/grapher/readme.md`.

#### What the JS library already does

Verified against the real bundle, so don't reimplement any of it here: `ySlugs`
is derived from the numeric columns when absent; the opening tab follows
`chartTypes`; a `date` column of ISO strings gives a date timeline with no
`yearIsDay` display config; maps and scatter plots need no entity selection.

### Integration with OWID Site

The `owid.site` module fetches live chart data:
- Parses chart configs embedded in HTML as `//EMBEDDED_JSON` delimiters
- Fetches variable data from `ourworldindata.org/grapher/data/variables/` endpoints
- Converts OWID's JSON format to pandas DataFrames

## Type Checking

Uses **ty** for static type checking. Configuration in `pyproject.toml`:

```toml
[tool.ty.src]
exclude = [...]

[tool.ty.rules]
invalid-argument-type = "ignore"
```

## Code Quality Tools

- **ruff** - Linting and formatting
- **ty** - Static type checking
- **pytest** - Unit testing

## Key Dependencies

- `pandas>=2.2.3` - Data manipulation
- `dataclasses-json>=0.6.7` - Config serialization
- `requests>=2.26.0` - Fetching data from OWID site
- `python-dateutil>=2.8.1` - Date parsing
- `jsonschema>=3.2.0` - Config validation

## Publishing

The package is published to PyPI via GitHub Actions. To release:
1. Bump version in `pyproject.toml`
2. Update changelog in `README.md`
3. Push to master - the workflow auto-publishes if version changed

## Notebooks & Data Analysis
- **Notebook creation and execution**: When user requests a notebook, ALWAYS create AND execute it immediately using `uv run jupyter nbconvert --to notebook --execute --inplace <notebook_path>`
- **Notebook execution**: When running notebooks, use `--inplace` to overwrite the existing file rather than creating new ones
- **Cache location**: Store joblib cache in `.cachedir/` directory

## Replicating OWID Charts

To replicate an existing OWID chart (e.g., `https://ourworldindata.org/grapher/annual-co2-emissions-per-country`):

### Available Endpoints

For any chart URL `https://ourworldindata.org/grapher/{slug}`:
- **CSV data**: `{url}.csv` or `{url}.csv?useColumnShortNames=true` (simpler column names)
- **Chart config**: `{url}.config.json` (contains chart type, title, map settings, etc.)
- **Metadata**: `{url}.metadata.json` (variable descriptions, sources)

### Replication Workflow

1. **Fetch the config** to understand chart settings:
   ```python
   import requests
   config = requests.get("https://ourworldindata.org/grapher/annual-co2-emissions-per-country.config.json").json()
   ```

2. **Fetch the data**:
   ```python
   import pandas as pd
   df = pd.read_csv("https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv?useColumnShortNames=true")
   df = df.rename(columns={'Entity': 'entity', 'Year': 'year'})
   ```

3. **Keep the config**: it is already the format `Chart` takes, so the chart
   type, map colour scale, selection and labels carry over as they are

4. **Build the chart**: `Chart(df, config=local_config(config, df))`, then
   adjust the config keys you want to change

### Checklist for Replicating Charts

`owid.grapher.notebook.local_config(config, df)` does the mechanical part: it
keeps the config keys Grapher still understands against a local DataFrame, drops
the site-only ones (`id`, `slug`, `dimensions`, ...), and fills in `ySlugs` from
the frame. What's left to check by hand:

- [ ] The DataFrame's value column names are what `ySlugs` (and `xSlug`,
      `colorSlug`, `sizeSlug`) refer to
- [ ] `selectedEntityNames` from the published config actually exist in the frame
      — otherwise the chart renders with fewer series than the original
- [ ] Units and display names, which live in `columns`, not in the chart config
