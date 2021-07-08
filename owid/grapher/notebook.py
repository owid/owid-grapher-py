# -*- coding: utf-8 -*-
#
#  notebook.py
#  owid-grapher-py
#

"""
Automatically generating notebooks from graphers.
"""

from typing import Optional

import jsonschema
import pandas as pd

from owid.site import get_owid_data

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
    jsonschema.validate(config, WHITELIST_SCHEMA)

    tab = config.get("tab", "LineChart")

    if tab == "LineChart":
        return translate_line_chart(config, data)

    raise Exception(f"chart type {tab} not supported yet")


def translate_line_chart(config: dict, data: pd.DataFrame) -> str:
    encoding = _gen_encoding(data)
    selection = _gen_selection(config, data)
    interaction = _gen_interaction(config, data)

    return f"""
grapher.Chart(
    data
).encode(
    {encoding}
){selection}{interaction}
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

    encoding = f'x="{x}", y="value"' + (f', c="{c}"' if c else "")
    return encoding


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

    scale_control = config["yAxis"].get("canChangeScaleType")
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
    for label in ["title", "subtitle", "note", "sourceDesc"]:
        if config.get(label):
            labels[to_snake.get(label, label)] = config[label]

    if not config:
        return ""

    return (
        ".label(\n    "
        + ",\n    ".join(f'{k}="{v}"' for k, v in labels.items())
        + "\n)"
    )
