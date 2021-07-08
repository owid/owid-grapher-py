# owid-grapher-py

_Experimental grapher package for use in Jupyter notebooks._

## Status

This package relies on internal APIs that may not be supported in future, so please consider it experimental.

## Installing

```
pip install git+https://github.com/owid/owid-grapher-py
```

## How to use

Get your data into a tidy data frame, then wrap it in a chart object and explain what marks you want and how to encode the dimensions you have (inspired by Altair).

```python
from owid.grapher import Chart

Chart(df).mark_line().encode(x='year', y='population').label('Too many Koalas?')
```

### Chart types

You specify your chart type with one of:

- `mark_line()`
- `mark_bar()`

#### Line chart

```python
# a third dimension can be encoded in the color
Chart(df2).mark_line().encode(
    x='year', y='population', c='region'
).label(title='Population by region')
```

#### Bar chart

```python
# regular bar chart
Chart(df).mark_bar().encode(x='population', y='region')
```

```python
# stacked bar chart
Chart(df2).mark_bar(stacked=True).encode(
    x='energy_generated',
    y='country',
    c='energy_source'
)
```

### Labels

```python
Chart(df).encode(
    x='year', y='population'
).labels(
    title='Very important',
    subtitle='Less important'
)
```

### Interactivity

```python
# enable relative mode toggle
Chart(...).interact(relative=True)
```

## How it works

OWID's grapher JS library has an internal JSON config format that all chart are created from. When you create a chart object, you are building up this JSON config. You can see the raw config by typing `.export()` on one of your chart objects in the notebook.

When Jupyter asks to display the chart object (calling `chart._repr_html_()`), we return an html snippet containing an iframe and some js to inject dynamic iframe contents equivalent to a pre-prepared chart on the Our World In Data site. Neat, huh?
