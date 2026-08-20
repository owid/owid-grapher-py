# owid-grapher-py

Create interactive [Our World in Data](https://ourworldindata.org) charts in Jupyter notebooks.

```python
from owid.grapher import Chart

Chart(df, config={"title": "Life expectancy at birth", "hasMapTab": True})
```

## Status

✅ Working (experimental)

Charts are rendered by the [`@ourworldindata/grapher`](https://github.com/owid/owid-grapher/tree/master/packages/%40ourworldindata/grapher)
npm package, whose standalone bundle is loaded straight from OWID's package host.

> [!IMPORTANT]
> That host is currently only reachable from OWID's Tailnet, so charts render for
> OWID staff only. This will be fixed once the package is published publicly; until
> then the package is not releasable to PyPI. Point `OWID_GRAPHER_BUNDLE_URL` at
> another host serving the package's `dist/` files to render elsewhere.

## Requirements

- Python 3.10+
- Jupyter notebook or JupyterLab

## Installing

```bash
pip install owid-grapher-py
```

## Quick start

```python
import pandas as pd
from owid.grapher import Chart

df = pd.DataFrame({
    "year": [2000, 2010, 2020] * 2,
    "entity": ["France"] * 3 + ["Japan"] * 3,
    "population": [59.0, 63.0, 65.0, 127.0, 128.0, 126.0],
})

Chart(
    df,
    config={"title": "Population", "chartTypes": ["LineChart"]},
    columns={"population": {"name": "Population", "shortUnit": " million"}},
)
```

Every chart type this package can draw, next to the code that draws it, is in
[`examples/showcase.py`](examples/showcase.py):

```bash
.venv/bin/python examples/showcase.py && open /tmp/owid-grapher-py-showcase.html
```

## How it works

This package is a thin proxy over Grapher, not an API of its own. `config` is
Grapher's [chart config](https://files.ourworldindata.org/schemas/) — the same
JSON OWID stores for every chart on its site — and `columns` is Grapher's column
metadata. Both are passed to the JavaScript library unchanged, so:

- **Every key Grapher has is available**, spelled the way Grapher spells it, with
  the [chart editor](https://ourworldindata.org/grapher), the JSON schema and the
  package's [readme](https://github.com/owid/owid-grapher/blob/master/packages/%40ourworldindata/grapher/readme.md)
  all serving as documentation.
- **Any published OWID chart's config can be pasted in** (append `.config.json` to
  a chart URL to fetch one).
- **Type checkers and editors know the keys**: `config` is typed as
  `GrapherConfig`, generated from the published schema, so a wrong key or an
  invalid enum value is an error before you run anything. Unknown keys are
  rejected at runtime too, with a suggestion.

What the Python side does is turn a DataFrame into what Grapher reads: it renames
the entity column to `entityName`, works out whether time is years or dates, and
selects the frame's entities if you haven't said which to select.

```python
Chart(
    df,
    config={...},         # Grapher's chart config
    columns={...},        # Grapher's column metadata, keyed by column name
    entity="country",     # which column holds entities (default: found by name)
    time="year",          # which column holds time (default: found by name)
    height=600,           # how tall the chart is in a notebook
)
```

`entity` and `time` are found automatically when they're named `entityName`,
`entity`, `country` or `location`, and `year`, `date` or `day`.

## Chart types

`chartTypes` picks the chart; Grapher opens on the first entry, and gives the
reader tabs when there is more than one.

```python
# A line chart, a bar chart, and a map, all in one chart
Chart(df, config={
    "chartTypes": ["LineChart", "DiscreteBar"],
    "hasMapTab": True,
    "tab": "map",  # which view it opens on
})
```

The types Grapher draws: `LineChart`, `DiscreteBar`, `StackedDiscreteBar`,
`StackedArea`, `StackedBar`, `ScatterPlot`, `SlopeChart`, `Marimekko`,
`Dumbbell`.

### Scatter plots

A scatter reads its axes and its point colour and size from named columns:

```python
Chart(df, config={
    "chartTypes": ["ScatterPlot"],
    "xSlug": "gdp_per_capita",
    "ySlugs": "life_expectancy",
    "colorSlug": "region",
    "sizeSlug": "population",
    "minTime": "latest",              # one year; drag the timeline for more
    "xAxis": {"scaleType": "log"},
})
```

### Maps

```python
Chart(df, config={
    "hasMapTab": True,
    "tab": "map",
    "map": {
        "colorScale": {
            "baseColorScheme": "YlGnBu",
            "binningStrategy": "manual",
            "customNumericValues": [60, 65, 70, 75, 80, 85],
        },
        "region": "Africa",           # zoom the projection to a continent
        "timeTolerance": 5,
    },
})
```

### Which columns to plot

Grapher plots every numeric column unless you say otherwise. `ySlugs` is a
space-separated list, in Grapher's own spelling:

```python
Chart(df, config={"ySlugs": "anomaly anomaly_lower anomaly_upper"})
```

That is also how you draw a confidence band: three series, with the bounds given
a muted colour through `columns`.

## Column metadata

`columns` carries what Grapher shows around the data — the display name and unit,
the series colour, and the source information behind *Learn more about this
data*:

```python
Chart(df, columns={
    "emissions": {
        "name": "Annual CO₂ emissions",
        "unit": "billion tonnes",
        "shortUnit": "Gt",                     # what axis ticks show
        "descriptionShort": "Emissions from fossil fuels and industry.",
        "descriptionKey": "Territorial emissions, excluding land use change.",
        "sourceName": "Global Carbon Budget (2024)",
        "sourceLink": "https://globalcarbonbudget.org",
        "origins": [{
            "producer": "Global Carbon Project",
            "title": "Global Carbon Budget",
            "citationFull": "Global Carbon Budget (2024).",
        }],
    },
})
```

## Interactivity

The controls are config, like everything else:

```python
Chart(df, config={
    "addCountryMode": "add-country",           # or "change-country", "disabled"
    "hideRelativeToggle": False,               # show the relative-change toggle
    "yAxis": {"canChangeScaleType": True},     # show the log/linear switch
    "selectedEntityNames": ["France", "Japan"],
    "minTime": 2000,
    "maxTime": 2020,
})
```

## Replicating a published OWID chart

Because `config` is Grapher's own format, a published chart can be replayed over
your own data by fetching its config and dropping the keys that only mean
something on the site:

```python
import requests
from owid.grapher import Chart
from owid.grapher.notebook import local_config

published = requests.get(
    "https://ourworldindata.org/grapher/life-expectancy.config.json"
).json()

Chart(df, config=local_config(published, df))
```

`owid.site` fetches the data of published charts, and
`owid.grapher.notebook.generate_notebook()` writes a whole notebook that
recreates one.

## Exporting charts

```python
chart = Chart(df, config={"title": "Population"})

chart.save_png("chart.png")          # needs: pip install playwright
chart.save_svg("chart.svg")          #        playwright install chromium

open("chart.html", "w").write(chart.to_html())   # standalone HTML page

chart.export()   # the CSV, column defs and config handed to Grapher
```

## Development

```bash
git clone https://github.com/owid/owid-grapher-py
cd owid-grapher-py

make .venv     # install dependencies
make test      # run all checks
make check     # check changed files only
```

`owid/grapher/config.py` is generated from Grapher's published JSON schema. When
Grapher publishes a new schema version, bump `SCHEMA_URL` in
`scripts/generate_config_types.py` and run `make config.types`.

To bump the version of Grapher itself, change `GRAPHER_VERSION` in
`owid/grapher/__init__.py`; the bundles it points at are listed at
`https://owid-packages.tail6e23.ts.net/ourworldindata/grapher/`.

### Useful resources

- **Chart configs**: append `.config.json` to any chart URL, e.g.
  `https://ourworldindata.org/grapher/annual-co2-emissions-per-country.config.json`
- **Chart data**: append `.csv?useColumnShortNames=true` to any chart URL
- **Config schema**: `https://files.ourworldindata.org/schemas/grapher-schema.011.json`
- **Grapher package docs**: [`packages/@ourworldindata/grapher/readme.md`](https://github.com/owid/owid-grapher/blob/master/packages/%40ourworldindata/grapher/readme.md)

## Changelog

- unreleased
    - Render charts with the `@ourworldindata/grapher` npm package (`GrapherLoader`) instead of the JS bundle scraped from ourworldindata.org
    - **Breaking**: replace the chained `mark_*()`/`encode()`/`label()` API and `plot()` with a single `Chart(df, config=..., columns=...)` that passes Grapher's own chart config through untouched, typed by `GrapherConfig` (generated from Grapher's published JSON schema)
- `0.3.5`
    - Support Python 3.13 and 3.14 (tested in CI)
- `0.3.4`
    - Add `region` parameter to `mark_map()` and `plot()` to focus the map on a continent
- `0.3.3`
    - Support multi-indicator charts: `encode()` and `plot()` accept a list of `y` columns, drawing each as a separate series (line/area charts)
    - Default the selection for multi-indicator charts to a single reference entity (`World`, else the best-covered entities) to avoid entities × indicators overload
- `0.3.2`
    - Add `to_html()` method for getting standalone HTML
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
