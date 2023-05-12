# -*- coding: utf-8 -*-
#
#  grapher.py
#  notebooks
#

import datetime as dt
import json
import random
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd
from dataclasses_json import LetterCase, dataclass_json
from dateutil.parser import parse

DATE_DISPLAY = {"yearIsDay": True, "zeroDay": "1970-01-01"}


class Chart:
    """
    Chart(df, title='Hello').mark_line().encode(x='dog', y='sheep')
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.config = ChartConfig()
        self.x: Optional[str] = None
        self.y: Optional[str] = None
        self.c: Optional[str] = None
        self.time_type = TimeType.YEAR
        self.selection: Optional[List[str]] = None
        self.timespan: Optional[Tuple[Any, Any]] = None

    def encode(
        self, x: Optional[str] = None, y: Optional[str] = None, c: Optional[str] = None
    ) -> "Chart":
        self.x = x
        self.y = y
        self.c = c

        # fail early if there's been a typo
        for col in [x, y, c]:
            if col and col not in self.data.columns:
                raise ValueError(f"no such column: {col}")

        if x == "date":
            self.time_type = TimeType.DAY

        self.config.hide_legend = not c

        return self

    def label(
        self, title: str = "", subtitle: str = "", source_desc: str = "", note: str = ""
    ) -> "Chart":
        self.config.title = title
        self.config.subtitle = subtitle
        self.config.source_desc = source_desc
        self.config.note = note
        return self

    def mark_scatter(self) -> "Chart":
        self.config.type = "ScatterPlot"
        return self

    def mark_line(self) -> "Chart":
        self.config.type = "LineChart"
        return self

    def mark_bar(self, stacked=False) -> "Chart":
        if stacked:
            self.config.type = "StackedDiscreteBar"
        else:
            self.config.type = "DiscreteBar"
        return self

    def interact(
        self,
        allow_relative: Optional[bool] = None,
        scale_control: Optional[bool] = None,
        entity_control: Optional[bool] = None,
        enable_map: Optional[bool] = None,
    ) -> "Chart":
        if allow_relative is not None:
            self.config.hide_relative_toggle = False

        if scale_control is not None:
            self.config.y_axis = {
                "scaleType": "linear",
                "canChangeScaleType": scale_control,
            }

        if entity_control is not None:
            self.config.hide_entity_controls = not entity_control

        if enable_map:
            self.config.has_map_tab = True

        return self

    def select(
        self,
        entities: Optional[List[str]] = None,
        timespan: Optional[Tuple[Any, Any]] = None,
    ) -> "Chart":
        if entities:
            self.selection = entities

        if timespan:
            if isinstance(timespan, (str, int)):
                timespan = (timespan, None)
            self.timespan = timespan

        return self

    def transform(self, relative: bool) -> "Chart":
        self.config.stack_mode = "relative" if relative else "absolute"
        return self

    def _repr_html_(self):
        full_config = self.export()
        html = generate_iframe(full_config)
        return html

    def export(self) -> Dict[str, Any]:
        self.config.auto_improve()
        config = self.config.to_dict()  # type: ignore
        config.update(self.data_config().to_dict())
        config = prune(config)
        return config

    def data_config(self) -> "DataConfig":
        if not self.x or not self.y:
            raise ValueError("must provide an x and y encoding")
        return DataConfig.from_data(
            self.data,
            x=self.x,
            y=self.y,
            c=self.c,
            time_type=self.time_type,
            chart_type=self.config.type,
            selection=self.selection,
            timespan=self.timespan,
        )


class TimeType(Enum):
    DAY = "day"
    YEAR = "year"


ChartType = Literal["LineChart", "DiscreteBar", "ScatterPlot", "StackedDiscreteBar"]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ChartConfig:
    tab: str = "chart"
    title: str = ""
    subtitle: str = ""
    note: str = ""
    source_desc: str = ""
    hide_logo: bool = True
    is_published: bool = True
    type: ChartType = "LineChart"
    hide_title_annotation: bool = True
    hide_legend: bool = False
    hide_entity_controls: bool = True
    hide_relative_toggle: bool = True
    has_map_tab: bool = False
    stack_mode: Literal["relative", "absolute"] = "absolute"
    y_axis: dict = field(default_factory=dict)

    def auto_improve(self):
        if self.title and self.type == "LineChart":
            self.hide_title_annotation = False


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Dimension:
    """
    "dimensions": [{"property": "y", "variableId": 1}],
    """

    property: Literal["y", "x"]
    variable_id: int
    display: Optional[dict] = field(default_factory=dict)

    @classmethod
    def single_y(cls) -> "Dimension":
        return Dimension(property="y", variable_id=1)

    @classmethod
    def from_dataset(cls, dataset: "Dataset") -> List["Dimension"]:
        return [
            Dimension(property="y", variable_id=v.id)
            for v in dataset.variables.values()
        ]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Variable:
    id: int
    name: str
    years: List[int]
    entities: List[int]
    values: List[float]
    short_unit: Optional[str] = None
    display: Optional[Dict[str, Any]] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Entity:
    id: int
    name: str
    code: Optional[str] = None


@dataclass
class Dataset:
    variables: Dict[int, Variable]
    entity_key: Dict[int, Entity]

    @classmethod
    def from_frame(cls, df: pd.DataFrame, time_type: TimeType) -> "Dataset":
        if set(df.columns) != {"year", "variable", "value", "entity"}:
            raise ValueError("expected normalised data frame")

        # NOTE: Grapher has separate concepts for variables and entities,
        #       but we simplify here and consider then both variables
        entities = {
            name: Entity(id=entity_id, name=name)
            for entity_id, name in enumerate(df.entity.unique(), 1)
        }
        entity_key = {e.id: e for e in entities.values()}
        df["entity_id"] = df.entity.apply(lambda v: entities[v].id)
        variables = {}
        for variable_id, variable in enumerate(sorted(df.variable.unique()), 1):
            var_data = df[df.variable == variable]
            variables[variable_id] = Variable(
                id=variable_id,
                name=variable,
                years=var_data.year.to_list(),
                entities=var_data.entity_id.to_list(),
                values=var_data.value.to_list(),
                display=DATE_DISPLAY if time_type == TimeType.DAY else {},
            )

        return Dataset(variables, entity_key)


@dataclass
class DataConfig:
    dataset: Dataset
    dimensions: List[Dimension]
    selected_entity_names: List[str]
    min_time: Optional[int] = None
    max_time: Optional[int] = None

    @classmethod
    def from_data(
        cls,
        df: pd.DataFrame,
        x: str,
        y: str,
        c: Optional[str] = None,
        time_type: "TimeType" = TimeType.YEAR,
        chart_type: ChartType = "LineChart",
        selection: Optional[List[str]] = None,
        timespan: Optional[Tuple[Any, Any]] = None,
    ) -> "DataConfig":
        # reshape tidy data into (year, entity, variable, value) form
        if chart_type == "LineChart":
            df = cls._reshape_line_chart(df, x, y, c, time_type)
        elif chart_type in ("DiscreteBar", "StackedDiscreteBar"):
            df = cls._reshape_discrete_bar(df, x, y, c)
        else:
            raise ValueError(f"chart type {chart_type} is not yet implemented")

        df = df.dropna()  # type: ignore

        dataset = Dataset.from_frame(df, time_type)
        entities = dataset.entity_key.values()
        if selection is None:
            selection = [e.name for e in entities]

        min_time, max_time = None, None
        if timespan:
            if time_type == TimeType.DAY:
                # remap to a timespan in integer days
                timespan = _timespan_from_date(timespan)

            min_time, max_time = timespan

        return DataConfig(
            dataset=dataset,
            dimensions=Dimension.from_dataset(dataset),
            selected_entity_names=selection,
            min_time=min_time,
            max_time=max_time,
        )

    @staticmethod
    def _reshape_line_chart(
        df: pd.DataFrame, x: str, y: str, c: Optional[str], time_type: TimeType
    ) -> pd.DataFrame:
        fake_variable = "dummy"
        df = (df[[x, y, c]] if c else df[[x, y]]).copy()  # type: ignore
        df["year"] = df.pop(x)

        if time_type == TimeType.DAY:
            offset = dt.date(1970, 1, 1).toordinal()
            df["year"] = pd.to_datetime(df.year).dt.date.apply(  # type: ignore
                lambda d: d.toordinal() - offset
            )

        if c:
            df["variable"] = df.pop(c)
            df["value"] = df.pop(y)
        else:
            df = df.melt("year")

        df["entity"] = df.pop("variable")
        df["variable"] = fake_variable

        return df

    @staticmethod
    def _reshape_discrete_bar(
        df: pd.DataFrame, x: str, y: str, c: Optional[str] = None
    ) -> pd.DataFrame:
        assert df[y].dtype == "object"
        if c:
            variable = df[c].values
        else:
            variable = "dummy"
        return pd.DataFrame(
            {
                "year": 2021,
                "variable": variable,
                "entity": df[y].values,
                "value": df[x].values,
            }
        )

    def to_dict(self) -> Dict[Any, Any]:
        ds = {}
        doc = {
            'selectedEntityNames': self.selected_entity_names,
            'owidDataset': ds,
            'dimensions': [d.to_dict() for d in self.dimensions],
        }

        for var_id, var in self.dataset.variables.items():
            ds[var_id] = {
                'data': {
                    'entities': var.entities,
                    'years': var.years,
                    'values': var.values,
                },
                'metadata': {
                    'id': var_id,
                    'name': var.name,
                    'display': var.display,
                    'dimensions': {
                        'entities': {
                            'values': [
                                {"id": e.id, "name": e.name}
                                for e in self.dataset.entity_key.values()
                            ],
                        },
                        'years': {
                            'values': [
                                {"id": y} for y in sorted(set(var.years))
                            ]
                        },
                    },
                },
            }

        return doc


def generate_iframe(config: Dict[str, Any]) -> str:
    #return '<iframe src="http://localhost:8000/example2.html" style="width: 100%; height: 600px; border: 0px none;" ></iframe>'
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))
    iframe_contents = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Lato:300,400,400i,700,700i|Playfair+Display:400,700&amp;display=swap"
      rel="stylesheet"
    />
    <link
      rel="stylesheet"
      href="https://ourworldindata.org/assets/common.css"
    />
    <link rel="stylesheet" href="https://ourworldindata.org/assets/owid.css" />
    <meta property="og:image:width" content="850" />
    <meta property="og:image:height" content="600" />
    <script>
      if (window != window.top)
        document.documentElement.classList.add("IsInIframe");
    </script>
  </head>
  <body class="StandaloneGrapherOrExplorerPage">
    <main>
      <figure data-grapher-src>
      </figure>
    </main>
      <div class="site-tools"></div>
      <script src="https://polyfill.io/v3/polyfill.min.js?features=es6,fetch,URL,IntersectionObserver,IntersectionObserverEntry"></script>
      <script type="module" src="https://ourworldindata.org/assets/common.mjs"></script>
      <script type="module" src="https://ourworldindata.org/assets/owid.mjs"></script>
      <script type="module">
        var jsonConfig = {json.dumps(config)};
        jsonConfig.owidDataset = new Map(Object.entries(jsonConfig.owidDataset).map(([key, value]) => [parseInt(key), value]));
        window.Grapher.renderSingleGrapherOnGrapherPage(jsonConfig);
    </script>
  </body>
</html>
"""  # noqa
    iframe_contents = iframe_contents.replace("</script>", "<\\/script>")
    return f"""
        <iframe id="{iframe_name}" style="width: 100%; height: 600px; border: 0px none;" ></iframe>
        <script>
            document.getElementById("{iframe_name}").contentDocument.write(`{iframe_contents}`)
        </script>
    """  # noqa


def prune(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: prune(v) if isinstance(v, dict) else v for k, v in d.items() if v is not None
    }


def _timespan_from_date(timespan: Tuple[str, str]) -> Tuple[int, int]:
    from_date_d = parse(timespan[0]).date()
    to_date_d = parse(timespan[1]).date()

    offset = dt.date(1970, 1, 1).toordinal()

    return (from_date_d.toordinal() - offset, to_date_d.toordinal() - offset)
