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
pip install owid-grapher-py
```

## Quick Start

See the [quickstart notebook in Colab](https://colab.research.google.com/github/owid/owid-grapher-py/blob/master/examples/quickstart.ipynb) for a comprehensive walkthrough with examples.

For advanced examples replicating real OWID charts, see:
- [Top 5 charts (simple API)](https://colab.research.google.com/github/owid/owid-grapher-py/blob/master/examples/top_charts_2025_simple.ipynb) - using the `plot()` function
- [Top 5 charts (full API)](https://colab.research.google.com/github/owid/owid-grapher-py/blob/master/examples/top_charts_2025.ipynb) - using the `Chart` class with method chaining

### Simple API with `plot()`

The simplest way to create a chart is with the `plot()` function:

```python
import pandas as pd
from owid.grapher import plot

df = pd.read_csv("https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?useColumnShortNames=true")
df = df.rename(columns={"Entity": "entity", "Year": "year"})

plot(
    df,
    y="ny_gdp_pcap_pp_kd",
    types=["map", "line", "bar"],
    color_scheme="GnBu",
    custom_numeric_values=[0, 1000, 2000, 5000, 10000, 20000, 50000, 100000],
    unit="$",
    title="GDP per capita",
    entities=["United States", "China", "India"],
    scale_control=True,
    entity_control=True,
)
```

### Full API with `Chart`

For more control, use the `Chart` class with method chaining (inspired by Altair):

```python
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
    entity='country'
).label(title='Population Over Time')
```

## The `plot()` Function

The `plot()` function provides a simple, single-call API for creating charts:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `y` | Y-axis column name | (required) |
| `x` | X-axis column name | `"year"` |
| `entity` | Entity grouping column | `"entity"` |
| `y_lower`, `y_upper` | Confidence interval columns | `None` |
| `color`, `size` | Scatter plot encodings | `None` |
| `types` | List of plot types: `"map"`, `"line"`, `"bar"`, `"slope"`, `"marimekko"`, `"scatter"`, `"stacked-bar"` | `["line", "bar"]` |
| `color_scheme` | Map color scheme (e.g., `"GnBu"`, `"Reds"`) | `None` |
| `custom_numeric_values` | Custom bin boundaries for map | `None` |
| `title`, `subtitle`, `source`, `note` | Chart labels | `None` |
| `unit` | Y-axis unit suffix | `None` |
| `variables` | Dict of column metadata (name, color, etc.) | `None` |
| `entities` | Pre-selected entities | `None` |
| `timespan` | Time range filter | `None` |
| `scale_control` | Show log/linear toggle | `False` |
| `entity_control` | Show entity picker | `False` |
| `entity_mode` | `"add-country"`, `"change-country"`, or `"disabled"` | `None` |
| `allow_relative` | Show relative/absolute toggle | `False` |

### Confidence Intervals with `plot()`

```python
plot(
    df,
    y="temperature",
    y_lower="temperature_lower",
    y_upper="temperature_upper",
    types=["line"],
    unit="°C",
    variables={
        "temperature": {"name": "Average", "color": "#ca2628"},
        "temperature_lower": {"name": "Lower bound (95% CI)", "color": "#c8c8c8"},
        "temperature_upper": {"name": "Upper bound (95% CI)", "color": "#c8c8c8"},
    },
    entity_mode="change-country",
)
```

## Chart Types (Full API)

### Line Chart

```python
Chart(df).mark_line().encode(
    x='year',
    y='population',
    entity='country'  # group by country
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
    entity='energy_source'
)
```

### Scatter Plot

```python
# Basic scatter plot
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy'
).label(title='GDP vs Life Expectancy')

# Scatter plot with entity grouping
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    entity='country'  # group by country
).label(title='GDP vs Life Expectancy by Country')

# Scatter plot with color and size encoding
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    entity='country',
    color='continent',  # color by a different variable
    size='population'   # size bubbles by population
).label(title='GDP vs Life Expectancy')
```

### Map View

```python
# Enable map tab with mark_map()
Chart(df).mark_line().mark_map().encode(
    x='year',
    y='population',
    entity='country'
)

# Configure map with color scheme and binning
Chart(df).mark_line().mark_map(
    color_scheme='OrRd',          # Color scheme (e.g., 'OrRd', 'BuGn', 'YlOrRd')
    binning_strategy='quantiles'  # How to bin values ('auto', 'manual', 'equalInterval', 'quantiles')
).encode(
    x='year',
    y='population',
    entity='country'
)

# Set map as the default view
Chart(df).mark_line().mark_map().show('map').encode(
    x='year',
    y='population',
    entity='country'
)
```

### Confidence Intervals

```python
# Line chart with shaded uncertainty band
Chart(df).mark_line().encode(
    x='year',
    y='temperature',
    y_lower='temperature_low',   # Lower bound column
    y_upper='temperature_high',  # Upper bound column
    entity='region'
)
```

## Labels

```python
Chart(df).mark_line().encode(
    x='year',
    y='population',
    entity='country'
).label(
    title='Population Trends',
    subtitle='Select countries to compare',
    note='Data is illustrative',
    source_desc='Sample data'
)
```

## Axis Configuration

```python
# Configure individual axes
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    entity='country'
).xaxis(
    label='GDP per Capita',
    unit='$',
    scale='log',              # Use logarithmic scale
    scale_control=True        # Allow user to toggle log/linear
).yaxis(
    label='Life Expectancy',
    unit='years'
)

# Or configure both axes at once
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    entity='country'
).axis(
    x_label='GDP per Capita',
    y_label='Life Expectancy',
    x_unit='$',
    y_unit='years',
    x_scale='log',
    x_scale_control=True
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

# Single entity mode (useful for charts with multiple lines per entity, e.g., confidence intervals)
Chart(...).interact(entity_mode='change-country')

# Combine multiple options
Chart(df).mark_line().encode(
    x='year', y='population', entity='country'
).interact(
    allow_relative=True,
    entity_control=True
)
```

## Data Selection

```python
# Select specific entities and time range
Chart(df).mark_line().encode(
    x='year', y='population', entity='country'
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

## Filtering

```python
# Only show entities that have data for all dimensions
# Useful for scatter plots where you need both x and y values
Chart(df).mark_scatter().encode(
    x='gdp_per_capita',
    y='life_expectancy',
    entity='country'
).filter(matching_entities_only=True)
```

## Variable Metadata

Configure display names, colors, and documentation for data columns:

```python
Chart(df).mark_line().encode(
    x='year',
    y='co2_emissions',
    entity='country'
).variable(
    'co2_emissions',
    name='CO₂ emissions',
    unit='tonnes',
    color='#ca2628',
    description_short='Annual carbon dioxide emissions'
)
```

## Exporting Charts

### Export to PNG/SVG

Export charts as images using Playwright (requires separate installation):

```bash
pip install playwright && playwright install chromium
```

```python
# Save to file
chart.save_png("chart.png")
chart.save_svg("chart.svg")

# Get bytes for display in notebook
from owid.grapher.export import export_chart
from IPython.display import SVG

svg_bytes = export_chart(chart, format="svg")
SVG(svg_bytes)
```

### Export Config

View the underlying JSON configuration:

```python
chart = Chart(df).mark_line().encode(x='year', y='population', entity='country')
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

### For Developers

**Useful resources when working with OWID charts:**

- **Chart configs**: Available for any existing chart by appending `.config.json` to the URL
  - Example: `https://ourworldindata.org/grapher/annual-co2-emissions-per-country.config.json`

- **Grapher schema**: The complete schema for chart configurations
  - Latest: `https://files.ourworldindata.org/schemas/grapher-schema.009.json`

- **ColumnDef schema**: TypeScript definition for column metadata
  - Source: [`CoreTableTypes.ts`](https://github.com/owid/owid-grapher/blob/928b4fce3fcf3f16e2aef810737beaadae3ab0e1/packages/%40ourworldindata/types/src/domainTypes/CoreTableTypes.ts#L190)

**Testing with real charts:**

To replicate an existing OWID chart in a notebook:
1. Fetch the chart config from the `.config.json` endpoint
2. Download the data using `.csv?useColumnShortNames=true`
3. Map the config properties to the `Chart` API methods

## TODO

This project should not attempt feature parity with grapher, but should walk the line between
making an expressive charting tool and making something that can reproduce a large percentage of
our existing charts. Some ideas for improvement:

Enable `grapher.Chart()` to support more chart types:

- [x] Scatterplots with color and size encoding
- [x] Axis labels and units
- [x] Log/linear scale controls
- [x] Entity filtering (matching_entities_only)
- [x] Map configuration (color schemes, binning strategies)
- [x] Confidence intervals (shaded uncertainty bands)
- [x] Variable metadata (names, colors, descriptions)
- [x] Simple `plot()` function API
- [ ] Axis bounds (min/max values)
- [ ] Line charts without a time axis

Auto-generate more types of notebooks correctly

- [ ] Multi-variable single entity line-charts
- [ ] Bar charts
- [ ] Stacked bar charts
- [ ] Time selection

## Changelog

- `0.3.1`
    - Add PNG/SVG export via `save_png()`, `save_svg()`, and `export_chart()`
- `0.3.0`
    - Add `plot()` function for simple, single-call chart creation
    - Support confidence intervals (`y_lower`, `y_upper`) and variable metadata in `plot()`
    - Add `entity_mode` parameter to `plot()` for single-entity selection
    - Add new example notebook using the simple `plot()` API
- `0.2.4`
    - Add `mark_map()` method for enabling map tab with color schemes and binning
    - Add `show()` method for setting the default chart view
    - Add confidence intervals via `y_lower` and `y_upper` in `encode()`
    - Add `variable()` method for column metadata (name, color, unit, descriptions)
    - Add `entity_mode` parameter to `interact()` for single-entity selection
    - Add top 5 charts notebook demonstrating real OWID chart replications
- `0.2.3`
    - Add `map()` method for configuring map tab with color schemes and binning strategies
    - Add `source_desc` support with automatic CSS hiding when empty
- `0.2.2`
    - Fix quickstart notebook to handle autoreload gracefully in Google Colab
- `0.2.1`
    - Add comprehensive PyPI metadata (keywords, classifiers, project URLs)
    - Add README.md as package long description
    - Update installation instructions to use PyPI
- `0.2.0`
    - Add scatter plot support with color and size encoding
    - Add `xaxis()` and `yaxis()` methods for axis configuration
    - Add support for logarithmic scales with `scale='log'`
    - Add `scale_control` parameter for user-toggleable log/linear scales
    - Add axis labels and units support
    - Add `filter(matching_entities_only=True)` for filtering entities with complete data
    - Add comprehensive quickstart notebook with real-world examples
    - Update documentation with all new features
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
