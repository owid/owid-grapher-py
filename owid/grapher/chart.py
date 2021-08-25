#
#  chart.py
#

"""
Provides the DeclarativeConfig class, presenting a grammar of graphics
that converts easily to and from Python code.
"""

from typing import Any, Dict, List, Optional, Literal, Tuple, Union, Iterator
from dataclasses import dataclass, field
import datetime as dt

import pandas as pd
from dataclasses_json import dataclass_json
from dateutil.parser import parse

DATE_DISPLAY = {"yearIsDay": True, "zeroDay": "1970-01-01"}


@dataclass
class Encoding:
    x: Optional[str] = None
    y: Optional[str] = None
    c: Optional[str] = None
    facet: Optional[str] = None

    def __iter__(self):
        for k in ("x", "y", "c", "facet"):
            v = getattr(self, k)
            if v is not None:
                yield k, v

    def is_empty(self) -> bool:
        return all(v is None for _, v in self)

    def to_py(self) -> str:
        parts = [f'{k}="{v}"' for k, v in self]
        kwargs = ",\n    ".join(parts)
        return f".encode(\n    {kwargs}\n)"


@dataclass
class Labels:
    title: str = ""
    subtitle: str = ""
    source_desc: str = ""
    note: str = ""

    def is_defaults(self) -> bool:
        return self == Labels()

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for key in ["title", "subtitle", "source_desc", "note"]:
            value = getattr(self, key)
            if value:
                yield key, value

    def to_py(self) -> str:
        if self.is_defaults():
            return ""

        parts = [f'{key}="{value}"' for key, value in self]
        kwargs = ",\n    ".join(parts)
        return f".label(\n    {kwargs}\n)"


@dataclass
class Interaction:
    allow_relative: Optional[bool] = None
    scale_control: Optional[bool] = None
    entity_control: Optional[bool] = None
    enable_map: Optional[bool] = None

    def is_defaults(self) -> bool:
        return self == Interaction()

    def __iter__(self) -> Iterator[Tuple[str, Optional[bool]]]:
        for k in ["allow_relative", "scale_control", "entity_control", "enable_map"]:
            v = getattr(self, k)
            if v is not None:
                yield k, v

    def to_py(self) -> str:
        if self.is_defaults():
            return ""

        parts = [f"{k}={v}" for k, v in self]
        kwargs = ",\n    ".join(parts)
        return f".interact(\n    {kwargs}\n)"


@dataclass
class YearSpan:
    min_time: Optional[int] = None
    max_time: Optional[int] = None

    def is_defaults(self) -> bool:
        return self == YearSpan()

    def to_py(self):
        return f"({self.min_time}, {self.max_time})"

    @classmethod
    def from_tuple(cls, t: "YearTuple") -> "YearSpan":
        return YearSpan(*t)


@dataclass
class DateSpan:
    min_time: Optional[dt.date] = None
    max_time: Optional[dt.date] = None

    def is_defaults(self) -> bool:
        return self == DateSpan()

    @classmethod
    def from_tuple(cls, t: "DateTuple") -> "DateSpan":
        lhs, rhs = t

        # parse date strings for convenience
        if isinstance(lhs, str):
            lhs_clean = dt.date.fromisoformat(lhs)
        else:
            lhs_clean = lhs

        if isinstance(rhs, str):
            rhs_clean = dt.date.fromisoformat(rhs)
        else:
            rhs_clean = rhs

        return DateSpan(lhs_clean, rhs_clean)

    def to_py(self):
        return f"({date_to_py(self.min_time)}, {date_to_py(self.max_time)})"


@dataclass
class Transform:
    stacked: bool = False
    relative: bool = False

    def is_defaults(self) -> bool:
        return self == Transform()

    def to_py(self) -> str:
        if self.is_defaults():
            return ""

        scaffold = ".transform(\n    {}\n)"

        parts = []
        if self.stacked:
            parts.append("stacked=True")
        if self.relative:
            parts.append("relative=True")

        return scaffold.format(",\n    ".join(parts))


TimeSpan = Union[YearSpan, DateSpan]

# phew, strictly typing this interface for usability is hard!
YearTuple = Tuple[Optional[int], Optional[int]]
DateTuple = Tuple[Optional[Union[str, dt.date]], Optional[Union[str, dt.date]]]
TimeTuple = Union[YearTuple, DateTuple]

EntityNames = List[str]


@dataclass
class Selection:
    entities: Optional[EntityNames] = None
    timespan: Optional[TimeSpan] = None

    def is_empty(self):
        return self.entities is None and self.timespan is None

    def to_py(self) -> str:
        if self.is_empty():
            return ""

        parts = []
        if self.entities:
            parts.append(
                "entities=[{}]".format(", ".join(f'"{name}"' for name in self.entities))
            )

        if self.timespan:
            parts.append(f"timespan={self.timespan.to_py()}")

        kwargs = ",\n    ".join(parts)
        return f".select(\n    {kwargs}\n)"


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
        for _, col in self.encoding:
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
        timespan: Optional[TimeTuple] = None,
    ) -> "DeclarativeConfig":
        if entities:
            self.selection.entities = entities

        if timespan:
            if is_date_tuple(timespan):
                self.selection.timespan = DateSpan.from_tuple(timespan)  # type: ignore

            elif is_year_tuple(timespan):
                self.selection.timespan = YearSpan.from_tuple(timespan)  # type: ignore

            else:
                raise ValueError(
                    "couldn't understand the timespan, it can be years like (1950, 1990), or dates like ('2021-05-03',)"
                )

        return self

    def transform(
        self, stacked: bool = False, relative: bool = False
    ) -> "DeclarativeConfig":
        self.transforms.stacked = stacked
        self.transforms.relative = relative
        return self

    def to_py(self, classname="DeclarativeConfig") -> str:
        """
        Generate the Python code that would recreate this declarative config.
        """
        encoding = self.encoding.to_py()
        selection = self.selection.to_py()
        transforms = self.transforms.to_py()
        labels = self.labels.to_py()
        interaction = self.interaction.to_py()

        return f"""
{classname}(
    data
){encoding}{selection}{transforms}{labels}{interaction}
""".strip()


def date_to_py(date: Optional[dt.date]) -> str:
    if not date:
        return "None"

    return f'"{date.isoformat()}"'


def is_date_tuple(t: Tuple[Any, Any]) -> bool:
    lhs, rhs = t
    lhs_ok = lhs is None or isinstance(lhs, (str, dt.date))
    rhs_ok = rhs is None or isinstance(rhs, (str, dt.date))
    return lhs_ok and rhs_ok


def is_year_tuple(t: Tuple[Any, Any]) -> bool:
    lhs, rhs = t
    lhs_ok = lhs is None or isinstance(lhs, int)
    rhs_ok = rhs is None or isinstance(rhs, int)
    return lhs_ok and rhs_ok
