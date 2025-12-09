# -*- coding: utf-8 -*-
#
#  notebook.py
#  owid-grapher-py
#

"""Tools for generating Jupyter notebooks from OWID chart configurations.

This module provides utilities to reverse-engineer OWID chart configurations back into
Python code that recreates the charts using the owid-grapher-py API. This is useful for:

- Learning how to create specific chart types
- Converting existing OWID charts to notebooks for customization
- Generating example code from live charts

Example:
    ```python
    from owid.site import get_chart_config, get_chart_data
    from owid.grapher.notebook import translate_config

    config = get_chart_config(url='https://ourworldindata.org/grapher/life-expectancy')
    data = get_chart_data(url='https://ourworldindata.org/grapher/life-expectancy')
    python_code = translate_config(config, data)
    print(python_code)
    ```
"""

import json
from os import mkdir
from os.path import isdir, join
from typing import Iterator, List, Optional, Tuple

import click
import nbformat as nbf

# import jsonschema
import pandas as pd

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
    """Convert an OWID chart configuration into Python code.

    Takes a chart configuration dictionary (as returned by get_chart_config) and the
    corresponding data, and generates Python code that recreates the chart using the
    owid-grapher-py Chart API.

    Args:
        config: OWID chart configuration dictionary containing chart type, dimensions,
            selections, labels, and other settings.
        data: pandas DataFrame containing the chart data in long format (typically
            with 'year'/'date', 'entity', and 'value' columns).

    Returns:
        String containing Python code that recreates the chart. The code uses method
        chaining with Chart().mark_*().encode().label() etc.

    Raises:
        UnsupportedChartType: If the chart type is not yet supported for translation.
            Currently supports: LineChart.

    Example:
        ```python
        config = get_chart_config(slug='life-expectancy')
        data = get_chart_data(slug='life-expectancy')
        code = translate_config(config, data)
        print(code)
        # Output:
        # grapher.Chart(
        #     data
        # ).encode(
        #     x="year",
        #     y="value",
        #     entity="entity"
        # ).label(
        #     title="Life Expectancy"
        # )
        ```
    """
    # jsonschema.validate(config, WHITELIST_SCHEMA)

    chart_type = config.get("type", "LineChart")
    if chart_type == "LineChart":
        return translate_line_chart(config, data)

    raise UnsupportedChartType(chart_type)


def translate_line_chart(config: dict, data: pd.DataFrame) -> str:
    """Translate a LineChart configuration to Python code.

    Generates Python code for creating a line chart by analyzing the configuration
    and determining appropriate encoding, selection, labels, and interaction settings.

    Args:
        config: Chart configuration dictionary for a LineChart.
        data: DataFrame containing the chart data.

    Returns:
        Python code string for creating the line chart.
    """
    encoding = _gen_encoding(config, data)
    preselection, selection = _gen_selection(config, data)
    labels = _gen_labels(config)
    interaction = _gen_interaction(config)
    transform = _gen_transform(config)
    mark_map = _gen_mark_map(config)

    return f"""
grapher.Chart(
    data{preselection}
).mark_line(){mark_map}{encoding}{selection}{transform}{labels}{interaction}
""".strip()


def _gen_mark_map(config: dict) -> str:
    """Generate the .mark_map() method call if map tab is enabled.

    Args:
        config: Chart configuration dictionary.

    Returns:
        Python code string for .mark_map() if map tab is enabled,
        empty string otherwise.
    """
    if config.get("hasMapTab"):
        return ".mark_map()"
    return ""


def _gen_transform(config: dict) -> str:
    """Generate the .transform() method call if needed.

    Checks if the chart uses relative (percentage) mode.

    Args:
        config: Chart configuration dictionary.

    Returns:
        Python code string for .transform(relative=True) if applicable,
        empty string otherwise.
    """
    if config.get("stackMode") == "relative":
        return ".transform(\n     relative=True\n)"

    return ""


def _gen_encoding(config: dict, data: pd.DataFrame) -> str:
    """Generate the .encode() method call for the chart.

    Analyzes the config and data to determine appropriate x, y, and entity encodings.
    Detects whether to use 'date' or 'year' for x-axis, and whether an entity
    dimension is needed based on the number of dimensions and selected entities.

    Args:
        config: Chart configuration dictionary.
        data: DataFrame containing the chart data.

    Returns:
        Python code string for the .encode() method call.
    """
    if "date" in data:
        x = "date"
    else:
        x = "year"

    entity: Optional[str] = None
    if len(config["dimensions"]) > 1:
        entity = "variable"
    elif len(config.get("selectedData", [])) > 1:
        entity = "entity"
    elif len(config.get("selectedEntityNames", [])) > 1:
        entity = "entity"

    parts = [f'x="{x}"', 'y="value"']
    if entity:
        parts.append(f'entity="{entity}"')
    encoding = ",\n    ".join(parts)

    return f".encode(\n    {encoding}\n)"


def _gen_selection(config: dict, data: pd.DataFrame) -> Tuple[str, str]:
    """Generate entity pre-selection and .select() method call.

    Determines whether to pre-filter the DataFrame (for single-entity charts) or
    use the .select() method (for multi-entity charts). Also handles time range
    selection if specified in the config.

    The config may select one variable with many entities, or one entity with many
    variables. For multiple variables, we pre-select the entity in the DataFrame.

    Args:
        config: Chart configuration dictionary.
        data: DataFrame containing the chart data.

    Returns:
        Tuple of (pre_selection_string, selection_string) where:
        - pre_selection_string: DataFrame filtering code (e.g., '[data.entity == "USA"]')
        - selection_string: .select() method call code
    """
    pre_selection, selection = _gen_entity_selection(config, data)

    min_time = config.get("minTime")
    max_time = config.get("maxTime")

    # don't set something that's automatic
    time = data["year"] if "year" in data.columns else data["date"]
    if min_time == time.min():
        min_time = None
    if max_time == time.max():
        max_time = None

    if pre_selection:
        if len(pre_selection) == 1:
            pre_selection_s = f'[data.entity == "{pre_selection[0]}"]'
        else:
            pre_selection_s = (
                ".query('entity in [\"" + '", "'.join(pre_selection) + "\"]')"
            )
    else:
        pre_selection_s = ""

    if selection and not min_time:
        middle = '",\n    "'.join(selection)
        selection_s = f""".select([
    "{middle}"
])"""
    elif min_time and not selection:
        selection_s = f""".select(
    timespan=({min_time}, {max_time})
)"""

    elif selection and min_time:
        middle = '",\n        "'.join(selection)
        selection_s = f""".select(
    entities=["{middle}"],
    timespan=({min_time}, {max_time})
)"""
    else:
        selection_s = ""

    return pre_selection_s, selection_s


def _gen_entity_selection(
    config: dict, data: pd.DataFrame
) -> Tuple[List[str], List[str]]:
    """Extract entity selection from config.

    Determines which entities are selected in the chart, either from selectedEntityNames
    or by resolving entity IDs from selectedData.

    Args:
        config: Chart configuration dictionary.
        data: DataFrame containing the chart data.

    Returns:
        Tuple of (pre_selection_entities, selection_entities) where:
        - pre_selection_entities: Entities to filter in DataFrame (for multi-variable charts)
        - selection_entities: Entities to pass to .select() method (for single-variable charts)
    """
    entities: List[str] = []

    if config.get("selectedEntityNames"):
        entities = config["selectedEntityNames"]

    elif config.get("selectedData") and len(config["selectedData"]) != len(
        data.entity.unique()
    ):
        selected_ids = [str(s["entityId"]) for s in config["selectedData"]]

        # requires an HTTP request
        owid_data = get_owid_data(config)

        entities = []
        for entity_id in selected_ids:
            try:
                entities.append(owid_data["entityKey"][entity_id]["name"])
            except KeyError:
                # some charts refer to entities that no longer exist
                # e.g. total-gov-expenditure-percapita-OECD
                continue
        entities = list(set(entities))

    # we have an actual selection
    if len(config["dimensions"]) > 1:
        # do entity pre-selection
        return entities, []

    return [], entities


def _gen_interaction(config: dict) -> str:
    """Generate the .interact() method call for UI controls.

    Analyzes the config to determine which interactive controls are enabled
    (entity picker, scale toggle, relative/absolute toggle).

    Note: Map tab is now enabled via mark_map(), not interact().

    Args:
        config: Chart configuration dictionary.

    Returns:
        Python code string for .interact() method call, or empty string if no
        interaction controls are enabled.
    """
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
    """Generate the .label() method call for chart text.

    Extracts title, subtitle, source description, and notes from the config.

    Args:
        config: Chart configuration dictionary.

    Returns:
        Python code string for .label() method call, or empty string if no
        labels are present.
    """
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


class UnsupportedChartType(Exception):
    """Raised when attempting to translate an unsupported chart type.

    Currently, only LineChart is fully supported. Other chart types
    (ScatterPlot, DiscreteBar, StackedDiscreteBar) will raise this exception.
    """

    pass


def generate_notebook(config: dict, path: str) -> None:
    """Generate a Jupyter notebook from a chart configuration.

    Fetches the chart data, translates the config to Python code, and creates
    a complete Jupyter notebook with imports, data loading, and chart code.

    Args:
        config: OWID chart configuration dictionary (must include 'slug').
        path: Directory path where the notebook file will be saved. The notebook
            will be named {slug}.ipynb.

    Raises:
        UnsupportedChartType: If the chart type cannot be translated.
    """
    owid_data = get_owid_data(config)
    data = owid_data_to_frame(owid_data)
    py = translate_config(config, data)

    slug = config["slug"]
    title = config["title"]
    save_to_notebook(slug, title, py, path)


def save_to_notebook(slug: str, title: str, py: str, path: str) -> None:
    """Save chart code to a Jupyter notebook file.

    Creates a new notebook with the chart title, imports, data loading, and
    the generated Python code.

    Args:
        slug: Chart slug for the filename and data loading.
        title: Chart title for the notebook heading.
        py: Python code string to include in the notebook.
        path: Directory path where the notebook will be saved.
    """
    nb_file = join(path, f"{slug}.ipynb")

    nb = _new_notebook(slug, title, py)

    with open(nb_file, "w") as ostream:
        nbf.write(nb, ostream)


def _new_notebook(slug: str, title: str, py: str):
    """Create a new nbformat notebook object.

    Constructs a notebook with proper metadata and cells for:
    - Title (markdown)
    - Imports (code)
    - Data loading (code)
    - Chart creation (code)

    Args:
        slug: Chart slug for data loading.
        title: Chart title for heading.
        py: Python code for chart creation.

    Returns:
        nbformat NotebookNode object.
    """
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
        nbf.v4.new_code_cell("import pandas as pd\nfrom owid import grapher, site")
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
    main()  # type: ignore
