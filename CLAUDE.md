# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Custom instructions

- Don't run `make test` unless explicitly told to (but always run it before committing).

## Project Overview

**owid-grapher-py** is a Python package for creating OWID (Our World in Data) charts in Jupyter notebooks. It provides a declarative API similar to Altair for building interactive charts that render using OWID's grapher JS library.

**Status**: ✅ Working (experimental) - uses the GrapherState API from OWID's staging bundle.

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
make check-typing        # Run pyright type checking
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

#### Chart Building API

Charts are built using a fluent/method-chaining API:

```python
Chart(df).mark_line().encode(x='year', y='population', entity='country')
```

The `Chart` class:
- Stores a pandas DataFrame internally
- Builds up a `ChartConfig` object through method calls
- Generates OWID's internal config format via `export()`
- Renders in Jupyter via `_repr_html_()` which returns an iframe

#### Rendering Pipeline

The `generate_iframe()` function:
1. Converts the internal config to CSV format via `_config_to_csv()`
2. Builds GrapherState options via `_build_grapher_config()`
3. Creates an iframe that loads OWID's JS bundle from `expose-grapher-state.owid.pages.dev`
4. Uses `OwidTable` to parse CSV and `GrapherState` + `Grapher` React component to render

#### Configuration System

Uses **dataclasses with dataclasses-json** for config serialization:
- `ChartConfig` - Top-level chart settings (title, type, interaction controls)
- `Dimension` - Maps DataFrame columns to chart dimensions (x, y, color)
- `DataConfig` - Converts pandas DataFrame to OWID's expected data format

Config uses `letter_case=LetterCase.CAMEL` to convert Python snake_case to JavaScript camelCase.

#### Time Handling

Supports two time types (via `TimeType` enum):
- `YEAR` - Standard yearly data (default)
- `DAY` - Date-based data (detected when x='date'), uses "yearIsDay" display mode

#### Chart Types

Implemented via `mark_*()` methods:
- `mark_line()` → "LineChart"
- `mark_bar()` → "DiscreteBar"
- `mark_bar(stacked=True)` → "StackedDiscreteBar"
- `mark_scatter()` → "ScatterPlot"

#### Interactivity

The `interact()` method enables UI controls:
- `allow_relative=True` - Shows relative/absolute toggle
- `entity_control=True` - Shows country/entity picker
- `scale_control=True` - Shows log/linear scale toggle

#### Map Tab

Use `mark_map()` to enable the map visualization:
```python
Chart(df).mark_line().mark_map(
    color_scheme='Reds',
    binning_strategy='manual',
    custom_numeric_values=[0, 1e6, 1e7, 1e8]
).encode(...)
```

#### Multiple Chart Types

Chain `mark_*()` methods to enable multiple views (line, bar, map):
```python
Chart(df).mark_line().mark_bar().mark_map().encode(...)
```

Use `show()` to set the default tab:
```python
Chart(df).mark_line().mark_bar().show("discrete-bar").encode(...)
```

### Integration with OWID Site

The `owid.site` module fetches live chart data:
- Parses chart configs embedded in HTML as `//EMBEDDED_JSON` delimiters
- Fetches variable data from `ourworldindata.org/grapher/data/variables/` endpoints
- Converts OWID's JSON format to pandas DataFrames

## Type Checking

Uses **pyright** for static type checking. Configuration in `pyproject.toml`:

```toml
[tool.pyright]
include = ["owid", "tests"]
```

## Code Quality Tools

- **ruff** - Linting and formatting
- **pyright** - Static type checking
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

3. **Extract key settings from config**:
   - `config['type']` or `config['chartTypes']` → which `mark_*()` methods to use
   - `config['hasMapTab']` → whether to add `mark_map()`
   - `config['map']['colorScale']` → map color scheme and binning
   - `config['selectedEntityNames']` → pre-selected countries
   - `config['title']`, `config['subtitle']`, `config['sourceDesc']` → labels

4. **Build the chart**

### Checklist for Replicating Charts

When replicating OWID charts, always ensure:
- [ ] Check `chartTypes` in config:
  - If `chartTypes` is **not specified** → use both `.mark_line().mark_bar()` (default)
  - If `chartTypes: ["LineChart"]` → use only `.mark_line()` (explicitly line-only)
  - If `chartTypes` lists multiple types → include all specified
- [ ] Include `.mark_map()` if `hasMapTab` is true in config
- [ ] Set `.yaxis(unit="...")` with the appropriate unit (e.g., "t", "years", "%")
