# -*- coding: utf-8 -*-
#
#  notebook.py
#  owid-grapher-py
#

"""
Automatically generating notebooks from graphers.
"""

from os.path import join, isdir
from os import mkdir
from typing import Optional, Iterator, List, Tuple
import json

# import jsonschema
import pandas as pd
import nbformat as nbf
import click

from owid.grapher.engine import compile, reverse_compile
from owid.grapher.internal import StandaloneChartConfig


def generate_notebook(config: StandaloneChartConfig, path: str) -> None:
    "Generate a jupyter notebook for the given config in the provided folder."
    data = config.to_frame()
    decl_config = reverse_compile(config)
    py = decl_config.to_py()

    slug = config["slug"]
    title = config["title"]
    save_to_notebook(slug, title, py, path)


def save_to_notebook(slug: str, title: str, py: str, path: str) -> None:
    nb_file = join(path, f"{slug}.ipynb")

    nb = _new_notebook(slug, title, py)

    with open(nb_file, "w") as ostream:
        nbf.write(nb, ostream)


def _new_notebook(slug: str, title: str, py: str):
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
        nbf.v4.new_code_cell("import pandas as pd\n" "from owid import grapher, site")
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
        except UnsupportedChartType:
            print(f"✗ [{i}/{total}] {slug}")

        except Exception as e:
            print(f"ERROR: {slug}")
            raise e

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
