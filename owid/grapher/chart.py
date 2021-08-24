#
#  py_to_grapher.py
#

"""
Translation from a python charting interface to the OWID unstable
grapher config API.

Chart + Frame => Config with data
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Literal, Tuple, Union, Iterator
import string
import random
from dataclasses import dataclass, field
import datetime as dt
import json

import pandas as pd
from dataclasses_json import dataclass_json, LetterCase
from dateutil.parser import parse

from .internal import ChartConfig, DataConfig, ChartType

DATE_DISPLAY = {"yearIsDay": True, "zeroDay": "1970-01-01"}


@dataclass
class Encoding:
    x: Optional[str] = None
    y: Optional[str] = None
    c: Optional[str] = None
    facet: Optional[str] = None

    def columns(self) -> Iterator[str]:
        for c in ["x", "y", "c", "facet"]:
            v = getattr(self, c)
            if v is not None:
                yield v


@dataclass
class Labels:
    title: Optional[str] = None
    subtitle: Optional[str] = None
    source_desc: Optional[str] = None
    note: Optional[str] = None

    def is_defaults(self) -> bool:
        return self == Labels()


@dataclass
class Interaction:
    allow_relative: Optional[bool] = None
    scale_control: Optional[bool] = None
    entity_control: Optional[bool] = None
    enable_map: Optional[bool] = None

    def is_defaults(self) -> bool:
        return self == Interaction()


@dataclass
class YearSpan:
    min_time: Optional[int] = None
    max_time: Optional[int] = None

    def is_defaults(self) -> bool:
        return self == YearSpan()


@dataclass
class DateSpan:
    min_time: Optional[dt.date] = None
    max_time: Optional[dt.date] = None

    def is_defaults(self) -> bool:
        return self == DateSpan()


@dataclass
class Transform:
    stacked: bool = False
    relative: bool = False

    def is_defaults(self) -> bool:
        return self == Transform()


TimeSpan = Union[YearSpan, DateSpan]

EntityNames = List[str]


@dataclass
class Selection:
    entities: Optional[EntityNames] = None
    timespan: Optional[TimeSpan] = None


@dataclass
class DeclarativeConfig:
    """
    A class for accumulating all the information we need to render a chart, purely as data,
    and without any internal knowledge of how grapher renders charts.

    Ideally this could be rendered to other charting libraries.
    """

    data: pd.DataFrame

    chart_type: Literal["line", "bar", "map", "scatter", "marimekko"] = "line"
    tab: Literal["chart", "map"] = "chart"

    encoding: Encoding = field(default_factory=Encoding)
    labels: Labels = field(default_factory=Labels)
    selection: Selection = field(default_factory=Selection)
    interaction: Interaction = field(default_factory=Interaction)
    transforms: Transform = field(default_factory=Transform)

    def encode(
        self,
        x: Optional[str] = None,
        y: Optional[str] = None,
        c: Optional[str] = None,
        facet: Optional[str] = None,
    ) -> "DeclarativeConfig":
        self.encoding.x = x
        self.encoding.y = y
        self.encoding.c = c
        self.encoding.facet = facet

        self.validate()
        return self

    def validate(self) -> None:
        # fail early if there's been a typo
        for col in self.encoding.columns():
            if col and col not in self.data.columns:
                raise ValueError(f"no such column: {col}")

        if not self.encoding.x or not self.encoding.y:
            raise ValueError("must provide x and y dimensions at minimum")

    def label(
        self, title: str = "", subtitle: str = "", source_desc: str = "", note: str = ""
    ) -> "DeclarativeConfig":
        self.labels.title = title
        self.labels.subtitle = subtitle
        self.labels.source_desc = source_desc
        self.labels.note = note
        return self

    def mark_scatter(self) -> "DeclarativeConfig":
        self.chart_type = "scatter"
        return self

    def mark_line(self) -> "DeclarativeConfig":
        self.chart_type = "line"
        return self

    def mark_bar(self) -> "DeclarativeConfig":
        self.chart_type = "bar"
        return self

    def mark_map(self):
        # the normal line chart offers a map view
        self.tab = "map"
        self.interaction.enable_map = True
        return self

    def interact(
        self,
        allow_relative: Optional[bool] = None,
        scale_control: Optional[bool] = None,
        entity_control: Optional[bool] = None,
        enable_map: Optional[bool] = None,
    ) -> "DeclarativeConfig":
        self.interaction.allow_relative = allow_relative
        self.interaction.scale_control = scale_control
        self.interaction.entity_control = entity_control
        self.interaction.enable_map = enable_map

        return self

    def select(
        self,
        entities: Optional[List[str]] = None,
        timespan: Optional[TimeSpan] = None,
    ) -> "DeclarativeConfig":
        if entities:
            self.selection.entities = entities

        if timespan:
            self.selection.timespan = timespan

        return self

    def transform(
        self, stacked: bool = False, relative: bool = False
    ) -> "DeclarativeConfig":
        self.transform.stacked = stacked
        self.transform.relative = relative
        return self


def _to_py(config: DeclarativeConfig) -> str:
    """
    Generate the Python code that would recreate this declarative config.
    """
    encoding = _encoding_to_py(config.encoding)
    preselection, selection = _selection_to_py(config.selection)
    labels = _gen_labels(config.labels)
    interaction = _gen_interaction(config.interaction)
    transform = _transform_to_py(config.transforms)

    return f"""
grapher.Chart(
    data{preselection}
){encoding}{selection}{transform}{labels}{interaction}
""".strip()


def _transform_to_py(transform: Transform) -> str:
    if transform.is_defaults():
        return ""

    scaffold = ".transform(\n    {}\n)"

    parts = []
    if transform.stacked:
        parts.append("stacked=True")
    if transform.relative:
        parts.append("relative=True")

    return scaffold.format(",\n    ".join(parts))


def _encoding_to_py(encoding: Encoding) -> str:
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


def _selection_to_py(config: dict, data: pd.DataFrame) -> Tuple[str, str]:
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
