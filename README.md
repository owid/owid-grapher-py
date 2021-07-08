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

### Interactivity

```python
# enable relative mode toggle
Chart(...).interact(relative=True)
```
