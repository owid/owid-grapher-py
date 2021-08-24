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


@dataclass
class Interaction:
    allow_relative: Optional[bool] = None
    scale_control: Optional[bool] = None
    entity_control: Optional[bool] = None
    enable_map: Optional[bool] = None


@dataclass
class YearSpan:
    min_time: Optional[int] = None
    max_time: Optional[int] = None


@dataclass
class DateSpan:
    min_time: Optional[dt.date] = None
    max_time: Optional[dt.date] = None


TimeSpan = Union[YearSpan, DateSpan]

EntityNames = List[str]


@dataclass
class DeclarativeConfig:
    """
    A class for accumulating all the information we need to render a chart, purely as data,
    and without any internal knowledge of how grapher renders charts.

    Ideally this could be rendered to other charting libraries.
    """

    data: pd.DataFrame
    encoding: Encoding = field(default_factory=Encoding)
    labels: Labels = field(default_factory=Labels)
    selection: Optional[EntityNames] = None
    interaction: Interaction = field(default_factory=Interaction)
    timespan: Optional[TimeSpan] = None
    chart_type: Literal["line", "bar", "map", "scatter", "marimekko"] = "line"
    tab: Literal["chart", "map"] = "chart"
    stacked: bool = False
    stack_mode: Literal["relative", "absolute"] = "absolute"

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

    def mark_line(self, stacked=False) -> "DeclarativeConfig":
        self.chart_type = "line"
        self.stacked = stacked
        return self

    def mark_bar(self, stacked=False) -> "DeclarativeConfig":
        self.chart_type = "bar"
        self.stacked = stacked
        return self

    def mark_map(self):
        # the normal line chart offers a map view
        self.tab = "map"
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
            self.selection = entities

        if timespan:
            self.timespan = timespan

        return self

    def transform(self, relative: bool) -> "DeclarativeConfig":
        self.stack_mode = "relative" if relative else "absolute"
        return self
