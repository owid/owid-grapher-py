# owid-grapher-py

Create interactive [Our World in Data](https://ourworldindata.org) charts in Jupyter notebooks.

## Status

✅ Working (experimental)

This package uses the OWID Grapher library to render interactive charts. The API may change as OWID's internal APIs evolve.

## Requirements

- Python 3.10+
- Jupyter notebook or JupyterLab

## Installing

```bash
pip install git+https://github.com/owid/owid-grapher-py
```

## Quick Start

Get your data into a tidy data frame, then wrap it in a chart object and explain what marks you want and how to encode the dimensions you have (inspired by Altair).

```python
import pandas as pd
from owid.grapher import Chart

# Create sample data
df = pd.DataFrame({
    'year': [2000, 2005, 2010, 2015, 2020] * 3,
    'country': ['Australia'] * 5 + ['New Zealand'] * 5 + ['Japan'] * 5,
    'population': [19.2, 20.4, 22.0, 23.8, 25.7,
                   3.9, 4.1, 4.4, 4.6, 5.1,
                   126.8, 127.8, 128.1, 127.1, 125.8]
})

# Create an interactive line chart
Chart(df).mark_line().encode(
    x='year',
    y='population',
    c='country'
).label(title='Population Over Time')
```

## Chart Types

### Line Chart

```python
Chart(df).mark_line().encode(
    x='year',
    y='population',
    c='country'  # color by country
).label(title='Population by Country')
```

### Bar Chart

```python
# Simple bar chart
Chart(df_2020).mark_bar().encode(
    x='population',
    y='country'
).label(title='Population in 2020')

# Stacked bar chart
Chart(df).mark_bar(stacked=True).encode(
    x='energy_generated',
    y='country',
    c='energy_source'
)
```

### Scatter Plot

```python
# Basic scatter plot
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy'
).label(title='GDP vs Life Expectancy')

# Scatter plot with color grouping
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    c='country'  # color by country
).label(title='GDP vs Life Expectancy by Country')
```

### Map View

```python
# Enable map tab (opens to map by default)
Chart(df).mark_line().encode(
    x='year',
    y='population',
    c='country'
).interact(enable_map=True)
```

## Labels

```python
Chart(df).mark_line().encode(
    x='year',
    y='population',
    c='country'
).label(
    title='Population Trends',
    subtitle='Select countries to compare',
    note='Data is illustrative',
    source_desc='Sample data'
)
```

## Interactivity

```python
# Enable relative mode toggle
Chart(...).interact(allow_relative=True)

# Enable log/linear scale toggle
Chart(...).interact(scale_control=True)

# Enable country/entity picker
Chart(...).interact(entity_control=True)

# Enable map tab
Chart(...).interact(enable_map=True)

# Combine multiple options
Chart(df).mark_line().encode(
    x='year', y='population', c='country'
).interact(
    allow_relative=True,
    entity_control=True,
    enable_map=True
)
```

## Data Selection

```python
# Select specific entities and time range
Chart(df).mark_line().encode(
    x='year', y='population', c='country'
).select(
    entities=['Australia', 'Japan'],
    timespan=(2000, 2015)
)
```

## Transforms

```python
# Plot relative change
Chart(...).transform(relative=True)
```

## Export Config

View the underlying JSON configuration:

```python
chart = Chart(df).mark_line().encode(x='year', y='population', c='country')
chart.export()  # Returns the grapher config dict
```

## How It Works

OWID's Grapher library uses a JSON config format for all charts. This package:

1. Takes your pandas DataFrame and chart configuration
2. Converts it to the Grapher's internal format (CSV + GrapherState config)
3. Renders an iframe in Jupyter that loads the OWID Grapher library
4. The Grapher library renders the interactive chart

## Development

```bash
# Clone the repo
git clone https://github.com/owid/owid-grapher-py
cd owid-grapher-py

# Install dependencies
make .venv

# Run tests
make test

# Check changed files
make check
```

## TODO

This project should not attempt feature parity with grapher, but should walk the line between
making an expressive charting tool and making something that can reproduce a large percentage of
our existing charts. Some ideas for improvement:

Enable `grapher.Chart()` to support more chart types:

- [x] Scatterplots
- [ ] Axis bounds
- [ ] Line charts without a time axis

Auto-generate more types of notebooks correctly

- [ ] Multi-variable single entity line-charts
- [ ] Bar charts
- [ ] Stacked bar charts
- [ ] Time selection

## Changelog

- `0.1.6`
    - Update to new GrapherState API with OwidTable
    - Fix iframe scroll behavior in notebooks
    - Hide unnecessary UI elements for cleaner notebook display
    - Update dependencies to match owid-catalog requirements
- `0.1.5`
    - Update to new module layout and Grapher config changes
- `0.1.4`
    - Fix broken charts by updating embedded JS requests
- `0.1.3`
    - Do not render the data when auto-generating notebooks
    - Allow fetching data by slug
    - Allow fetching data and config from dev environments
- `0.1.2`
    - Support timespans with `select()`
- `0.1.1`
    - Improve `select()`, `interact()` and `label()` methods on `Chart`
    - Helpers to download config/data from chart pages (`owid.site`)
    - Generate notebooks with Python plotting commands (`owid.grapher.notebook`)
- `0.1.0`
    - Plot basic line charts, bar charts and stacked bar charts
