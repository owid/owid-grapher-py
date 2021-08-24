#
#  grapher_to_py.py
#

"""
Translation from OWID's unstable internal grapher config API
to a Python charting command.
"""

from typing import Optional, Tuple, List

import pandas as pd

from owid.site import OWIDData

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


def translate_config(config: dict, data: OWIDData) -> str:
    "Turn a grapher config into a python string describing the chart."
    # jsonschema.validate(config, WHITELIST_SCHEMA)

    chart_type = config.get("type", "LineChart")
    if chart_type == "LineChart":
        return translate_line_chart(config, data)

    raise UnsupportedChartType(chart_type)


def translate_line_chart(config: dict, data: OWIDData) -> str:
    encoding = _gen_encoding(config, data)
    preselection, selection = _gen_selection(config, data)
    labels = _gen_labels(config)
    interaction = _gen_interaction(config)
    transform = _gen_transform(config)

    return f"""
grapher.Chart(
    data{preselection}
){encoding}{selection}{transform}{labels}{interaction}
""".strip()


def _gen_transform(config: dict) -> str:
    if config.get("stackMode") == "relative":
        return ".transform(\n     relative=True\n)"

    return ""


def _gen_encoding(config: dict, data: pd.DataFrame) -> str:
    if "date" in data:
        x = "date"
    else:
        x = "year"

    c: Optional[str] = None
    if len(config["dimensions"]) > 1:
        c = "variable"
    elif len(config.get("selectedData", [])) > 1:
        c = "entity"
    elif len(config.get("selectedEntityNames", [])) > 1:
        c = "entity"

    parts = [f'x="{x}"', 'y="value"']
    if c:
        parts.append(f'c="{c}"')
    encoding = ",\n    ".join(parts)

    return f".encode(\n    {encoding}\n)"


def _gen_selection(config: dict, data: pd.DataFrame) -> Tuple[str, str]:
    """
    The config may select one variable and some of many entities, or it may select one entity and
    some of many variables.

    If we have multiple variables, pre-select the entity.
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

    if config.get("hasMapTab"):
        parts.append("enable_map=True")

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


class UnsupportedChartType(Exception):
    pass
