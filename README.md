# owid-grapher-py

_Experimental grapher package for use in Jupyter notebooks._

## Status

This package relies on internal APIs that may not be supported in future, so please consider it experimental.

## Installing

```
pip install git+https://github.com/owid/owid-grapher-py
```

## How to use

The package operates off data frames, and uses an Altair-like format on top of data frames. Not all features of grapher

### Chart types

#### Line chart (`mark_line()`)

```python
from owid.grapher import Chart

# line charts are the default, so you can plot minimally
Chart(df1).encode(x='year', y='population')

# a third dimension can be encoded in the color
Chart(df2).mark_line().encode(
    x='year', y='population', c='region'
).label(title='Population by region')
```

#### Bar chart (`mark_bar()`)

```python
from owid.grapher import Chart

# regular bar chart
Chart(df1).mark_bar().encode(
    x='population', y='region'
).label(title='Population by region')

# stacked bar chart
Chart(df2).mark_bar(stacked=True).encode(
    x='energy_generated', y='country', c='energy_source'
)
```

### Interactivity

```python
# enable relative mode toggle
Chart(...).interact(relative=True)
```
