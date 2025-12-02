# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**owid-grapher-py** is an experimental Python package for creating OWID (Our World in Data) charts in Jupyter notebooks. It provides a declarative API similar to Altair for building interactive charts that render using OWID's grapher JS library.

**Status**: ❎ Not currently working - relies on internal APIs that change regularly.

## Development Setup

This project uses **Poetry** for dependency management and **Make** for common tasks.

### Initial Setup

```bash
poetry install
```

This creates a `.venv` virtual environment with all dependencies.

## Common Commands

### Testing

```bash
# Run all checks (formatting, linting, type checking, unit tests)
make test

# Run individual checks
make check-formatting    # Check code formatting with black
make lint                # Run flake8 linting
make check-typing        # Run pyright type checking
make unittest            # Run pytest tests

# Run tests on file changes
make watch
```

### Formatting

```bash
make format              # Auto-format code with black
```

### Running Single Tests

```bash
.venv/bin/pytest tests/test_grapher.py::test_name
```

## Architecture

### Package Structure

The project uses a **namespace package** structure under `owid/`:

- **`owid/grapher/`** - Core charting functionality
  - `__init__.py` - Main `Chart` class and config dataclasses
  - `notebook.py` - Tools for auto-generating notebooks from existing charts

- **`owid/site/`** - Integration with live OWID website
  - `__init__.py` - Functions to fetch chart configs and data from ourworldindata.org

### Core Design Patterns

#### Chart Building API

Charts are built using a fluent/method-chaining API:

```python
Chart(df).mark_line().encode(x='year', y='population', c='region')
```

The `Chart` class:
- Stores a pandas DataFrame internally
- Builds up a `ChartConfig` object through method calls
- Generates OWID's internal JSON config format via `export()`
- Renders in Jupyter via `_repr_html_()` which returns an iframe with embedded config

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

### Integration with OWID Site

The `owid.site` module fetches live chart data:
- Parses chart configs embedded in HTML as `//EMBEDDED_JSON` delimiters
- Fetches variable data from `ourworldindata.org/grapher/data/variables/` endpoints
- Converts OWID's JSON format to pandas DataFrames

## Type Checking

Uses **pyright** instead of mypy due to namespace package structure. Configuration in `pyproject.toml`:

```toml
[tool.pyright]
include = ["owid/**", "tests/**"]
```

## Code Quality Tools

- **black** - Code formatting
- **flake8** - Linting (config in `.flake8`)
- **pyright** - Static type checking
- **pytest** - Unit testing

## Key Dependencies

- `pandas` - Data manipulation
- `dataclasses-json` - Config serialization
- `requests` - Fetching data from OWID site
- `python-dateutil` - Date parsing
- `jsonschema` - Config validation
- `nbformat` - Jupyter notebook generation
