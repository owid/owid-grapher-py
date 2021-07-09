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
from typing import Optional, Iterator
import json

# import jsonschema
import pandas as pd
import nbformat as nbf
import click

from owid.site import get_owid_data, owid_data_to_frame

# all the types of charts we know how to translate back to python
WHITELIST_SCHEMA = {
    "$oneOf": [{"$ref": "/schemas/line_chart"}],
    "definitions": {
        "line_chart": {
            "$id": "/schemas/line_chart",
            "$allOf": [
                {
                    "type": "object",
                    "properties": {
                        "tab": {"enum": ["chart"]},
                    },
                },
                {"$ref": "/schemas/text_fields"},
            ],
        },
        "text_fields": {
            "$id": "/schemas/text_fields",
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "note": {"type": "string"},
                "sourceDesc": {"type": "string"},
            },
        },
    },
}


def translate_config(config: dict, data: pd.DataFrame) -> str:
    "Turn a grapher config into a python string describing the chart."
    # jsonschema.validate(config, WHITELIST_SCHEMA)

    tab = config.get("tab", "LineChart")

    if tab == "LineChart":
        return translate_line_chart(config, data)

    raise Exception(f"chart type {tab} not supported yet")


def translate_line_chart(config: dict, data: pd.DataFrame) -> str:
    encoding = _gen_encoding(data)
    selection = _gen_selection(config, data)
    labels = _gen_labels(config)
    interaction = _gen_interaction(config, data)

    return f"""
grapher.Chart(
    data
){encoding}{selection}{labels}{interaction}
""".strip()


def _gen_encoding(data: pd.DataFrame) -> str:
    if "date" in data:
        x = "date"
    else:
        x = "year"

    c: Optional[str] = None
    if len(data.entity.unique()) > 1:
        c = "entity"
    elif len(data.variable.unique()) > 1:
        c = "variable"

    parts = [f'x="{x}"', 'y="value"']
    if c:
        parts.append(f'c="{c}"')
    encoding = ",\n    ".join(parts)

    return f".encode(\n    {encoding}\n)"


def _gen_selection(config: dict, data: pd.DataFrame) -> str:
    if len(config["selectedData"]) == len(data.entity.unique()):
        return ""

    selected_ids = [str(s["entityId"]) for s in config["selectedData"]]

    owid_data = get_owid_data(config)
    entities = [owid_data["entityKey"][entity_id]["name"] for entity_id in selected_ids]

    # we have an actual selection
    entity_str = '",\n    "'.join(entities)
    return f'.select([\n    "{entity_str}"\n])'


def _gen_interaction(config: dict, data: pd.DataFrame) -> str:
    parts = []

    entity_control = not config.get("hideEntityControls")
    if entity_control:
        parts.append("entity_control=True")

    scale_control = config.get("yAxis", {}).get("canChangeScaleType")
    if scale_control is not None:
        parts.append(f"scale_control={scale_control}")

    disable_relative = config.get("hideRelativeControls")
    if disable_relative is not None:
        parts.append(f"allow_relative={not disable_relative}")

    if parts:
        return ".interact(\n    " + ",\n    ".join(parts) + "\n)"

    return ""


def _gen_labels(config: dict) -> str:
    to_snake = {"sourceDesc": "source_desc"}

    labels = {}
    for label in ["title", "subtitle", "sourceDesc", "note"]:
        if config.get(label):
            labels[to_snake.get(label, label)] = " ".join(config[label].split())

    if not labels:
        return ""

    return (
        ".label(\n    "
        + ",\n    ".join(f'{k}="{v}"' for k, v in labels.items())
        + "\n)"
    )


def generate_notebook(config: dict, path: str) -> None:
    "Generate a jupyter notebook for the given config in the provided folder."
    owid_data = get_owid_data(config)
    data = owid_data_to_frame(owid_data)
    py = translate_config(config, data)

    slug = config["slug"]
    title = config["title"]
    save_to_notebook(slug, title, py, path)

    data_file = join(path, "_data", f"{slug}.csv")
    data.to_csv(data_file, index=False)


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
        nbf.v4.new_code_cell("import pandas as pd\n" "from owid import grapher")
    )

    cells.append(
        nbf.v4.new_code_cell(f'data = pd.read_csv("_data/{slug}.csv")\ndata.head()')
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
        except:  # noqa
            print(f"✗ [{i}/{total}] {slug}")

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
