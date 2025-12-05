# OWID Grapher Python

Create interactive [Our World in Data](https://ourworldindata.org) charts in Jupyter notebooks.

## Installation

```bash
pip install owid-grapher-py
```

## Quick Example

```python
import pandas as pd
from owid.grapher import Chart

df = pd.DataFrame({
    'year': [2020, 2021, 2022],
    'country': ['USA', 'USA', 'USA'],
    'population': [331, 332, 333]
})

Chart(df).mark_line().encode(x='year', y='population')
```

## Documentation

- [API Reference](api-reference/chart.md)
- [Examples Notebook](https://github.com/owid/owid-grapher-py/blob/master/examples/quickstart.ipynb)


## Use Cases

- **Data Analysis**: Explore datasets with interactive visualizations
- **Education**: Create engaging charts for teaching and presentations
- **Research**: Visualize research data with professional, publication-ready charts
- **Reproducible Science**: Document your analysis with interactive notebooks
- **Prototyping**: Quickly iterate on data visualizations

## How It Works

OWID's Grapher library uses a JSON config format for all charts. This package:

1. Takes your pandas DataFrame and chart configuration
2. Converts it to the Grapher's internal format (CSV + GrapherState config)
3. Renders an iframe in Jupyter that loads the OWID Grapher library
4. The Grapher library renders the interactive chart

## Get Started

Ready to create your first chart? Check out the [Installation Guide](getting-started/installation.md) and [Quick Start Tutorial](getting-started/quickstart.md).

## Community & Support

- **GitHub**: [owid/owid-grapher-py](https://github.com/owid/owid-grapher-py)
- **Issues**: [Report bugs or request features](https://github.com/owid/owid-grapher-py/issues)
- **PyPI**: [owid-grapher-py](https://pypi.org/project/owid-grapher-py/)

## License

MIT License - see the [LICENSE](https://github.com/owid/owid-grapher-py/blob/master/LICENSE) file for details.
