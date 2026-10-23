# -*- coding: utf-8 -*-
#
#  notebook.py
#  owid-grapher-py
#

"""Generate Jupyter notebooks that recreate published OWID charts.

An OWID chart is a config plus its data, and `Chart` takes a config as-is, so
translating a published chart into Python is mostly a matter of dropping the
keys that only mean something on ourworldindata.org (its id, its slug, which
indicators to fetch) and printing what's left.

Example:
    ```python
    from owid.site import get_chart_config, get_chart_data
    from owid.grapher.notebook import translate_config

    url = "https://ourworldindata.org/grapher/life-expectancy"
    print(translate_config(get_chart_config(url), get_chart_data(url)))
    ```
"""

import json
import pprint
from os import mkdir
from os.path import isdir, join
from typing import Any, Dict, Iterator, cast

import click
import nbformat as nbf
import pandas as pd

from owid.grapher.config import CONFIG_KEYS, GrapherConfig
from owid.site import get_owid_data, owid_data_to_frame

# Config keys that only mean something for a chart published on
# ourworldindata.org, backed by OWID's indicator API.
SITE_ONLY_KEYS = {
    "id",
    "slug",
    "version",
    "isPublished",
    "originUrl",
    "internalNotes",
    "license",
    "dimensions",
}


def translate_config(config: dict, data: pd.DataFrame) -> str:
    """Convert an OWID chart configuration into Python code.

    Args:
        config: OWID chart configuration, as returned by
            `owid.site.get_chart_config`.
        data: the chart's data, as returned by `owid.site.get_chart_data`.
            Used to work out which column holds the values.

    Returns:
        Python code that recreates the chart with `Chart`.

    Example:
        ```python
        config = get_chart_config(slug="life-expectancy")
        data = get_chart_data(slug="life-expectancy")
        print(translate_config(config, data))
        # Chart(
        #     data,
        #     config={
        #         "title": "Life expectancy at birth",
        #         "chartTypes": ["LineChart"],
        #     },
        # )
        ```
    """
    formatted = pprint.pformat(local_config(config, data), sort_dicts=False, width=88)
    indented = "\n".join("    " + line for line in formatted.split("\n")).lstrip()
    return f"Chart(\n    data,\n    config={indented},\n)"


def local_config(config: dict, data: pd.DataFrame) -> GrapherConfig:
    """The parts of a published chart's config that apply to a local DataFrame.

    Drops what only makes sense on the site, and translates the two things the
    site's own format spells differently to what a CSV-backed chart needs.
    """
    local: Dict[str, Any] = {
        key: value
        for key, value in config.items()
        if key in CONFIG_KEYS and key not in SITE_ONLY_KEYS
    }

    # Older configs name a single chart type; newer ones list them.
    if "chartTypes" not in local and config.get("type"):
        local["chartTypes"] = [config["type"]]

    # On the site the y columns come from `dimensions`, which name indicator
    # ids. Against a DataFrame they're column names instead.
    if "ySlugs" not in local:
        value_columns = [
            column
            for column in data.columns
            if column not in ("entity", "entityName", "year", "date", "day", "variable")
            and pd.api.types.is_numeric_dtype(data[column])
        ]
        if value_columns:
            local["ySlugs"] = " ".join(map(str, value_columns))

    # Every key came from CONFIG_KEYS, so this is a GrapherConfig as far as
    # anything can tell at runtime -- the values are the site's own.
    return cast(GrapherConfig, local)


def generate_notebook(config: dict, path: str) -> None:
    """Write a notebook that recreates a chart, named after its slug.

    Args:
        config: OWID chart configuration (must include 'slug').
        path: directory to write `{slug}.ipynb` into.
    """
    data = owid_data_to_frame(get_owid_data(config))
    py = translate_config(config, data)
    save_to_notebook(config["slug"], config.get("title", ""), py, path)


def save_to_notebook(slug: str, title: str, py: str, path: str) -> None:
    """Save chart code to a Jupyter notebook file.

    Args:
        slug: chart slug, used for the filename and for loading the data.
        title: chart title, used as the notebook's heading.
        py: the Python code that draws the chart.
        path: directory to write the notebook into.
    """
    with open(join(path, f"{slug}.ipynb"), "w") as ostream:
        nbf.write(_new_notebook(slug, title, py), ostream)


def _new_notebook(slug: str, title: str, py: str):
    """A notebook with a heading, the imports, the data and the chart."""
    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }

    cells = []
    if title:
        cells.append(nbf.v4.new_markdown_cell(f"# {title}"))
    cells.append(
        nbf.v4.new_code_cell("from owid import site\nfrom owid.grapher import Chart")
    )
    cells.append(
        nbf.v4.new_code_cell(f'data = site.get_chart_data(slug="{slug}")\ndata.head()')
    )
    cells.append(nbf.v4.new_code_cell(py))
    nb["cells"] = cells
    return nb


@click.command()
@click.argument("input_file")
@click.argument("dest_path")
def main(input_file, dest_path):
    """
    Take a large list of configs in JSONL format, and attempt to render as many as we can to
    notebooks.
    """
    data_folder = join(dest_path, "_data")
    if not isdir(data_folder):
        mkdir(data_folder)

    i = 0
    for total, config in enumerate(iter_published(input_file), 1):
        slug = config["slug"]
        try:
            generate_notebook(config, dest_path)
            i += 1
            print(click.style(f"✓ [{i}/{total}] {slug}", fg="green"))
        except Exception as e:
            print(click.style(f"✗ [{i}/{total}] {slug}: {e}", fg="red"))

    print(f"Generated {i} notebooks successfully")


def iter_published(input_file: str) -> Iterator[dict]:
    for config in iter_jsonl(input_file):
        if not config.get("isPublished") or not config["slug"]:
            continue

        yield config


def iter_jsonl(input_file: str) -> Iterator[dict]:
    with open(input_file) as istream:
        for line in istream:
            yield json.loads(line)


if __name__ == "__main__":
    main()
