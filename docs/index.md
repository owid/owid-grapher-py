# OWID Grapher Python

Create interactive [Our World in Data](https://ourworldindata.org) charts in Jupyter notebooks.

This library provides a Python API for building charts using OWID's Grapher visualization library. It's useful for exploring datasets with interactive visualizations, creating publication-ready charts for research and education, and documenting data analysis in reproducible notebooks. The package integrates seamlessly with pandas DataFrames and renders directly in Jupyter environments.

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

!!! tip "Learn from more examples!"
    - Check out our [Jupyter notebook](https://github.com/owid/owid-grapher-py/blob/master/examples/quickstart.ipynb)!
    - Check our examples on [GitHub](https://github.com/owid/owid-grapher-py)

## Community & Support

- **GitHub**: [owid/owid-grapher-py](https://github.com/owid/owid-grapher-py)
- **Issues**: [Report bugs or request features](https://github.com/owid/owid-grapher-py/issues)
- **PyPI**: [owid-grapher-py](https://pypi.org/project/owid-grapher-py/)

!!! info "You can learn more about our data and engineering work [here](https://docs.owid.io/projects/etl/)."

## License

MIT License - see the [LICENSE](https://github.com/owid/owid-grapher-py/blob/master/LICENSE) file for details.
