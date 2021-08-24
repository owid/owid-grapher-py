#
#  internal.py
#

"""
Grapher config and data formats internal to OWID. They're isolated in this module
since they're not yet a stable API.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict, Any, Tuple
from enum import Enum

from dataclasses_json import dataclass_json, LetterCase
import pandas as pd


ChartType = Literal["LineChart", "DiscreteBar", "ScatterPlot", "StackedDiscreteBar"]


class TimeType(Enum):
    DAY = "day"
    YEAR = "year"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ChartConfig:
    id: int = 1
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
    stack_mode: Literal["relative", "absolute"] = "absolute"
    y_axis: dict = field(default_factory=dict)
    dimensions: List["Dimension"] = field(default_factory=list)
    selected_data: List[Dict[str, int]] = field(default_factory=list)
    min_time: Optional[int] = None
    max_time: Optional[int] = None
    has_map_tab: bool = True
    version: int = 1

    def auto_improve(self):
        if self.title and self.type == "LineChart":
            self.hide_title_annotation = False

    @property
    def is_standalone(self) -> bool:
        return False


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


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Dataset:
    variables: Dict[str, Variable]
    entity_key: Dict[str, Entity]

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
        entity_key = {str(e.id): e for e in entities.values()}
        df["entity_id"] = df.entity.apply(lambda v: entities[v].id)
        variables = {}
        for variable_id, variable in enumerate(sorted(df.variable.unique()), 1):
            var_data = df[df.variable == variable]
            variables[str(variable_id)] = Variable(
                id=variable_id,
                name=variable,
                years=var_data.year.to_list(),
                entities=var_data.entity_id.to_list(),
                values=var_data.value.to_list(),
                display=DATE_DISPLAY if time_type == TimeType.DAY else {},
            )

        return Dataset(variables, entity_key)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DataConfig:
    """
    The data and the view of it that has been selected.
    """

    owid_data: "Dataset"

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
            selected_data = [{"entityId": e.id} for e in entities]
        else:
            selected_data = [
                {"entityId": e.id} for e in entities if e.name in selection
            ]

        min_time, max_time = None, None
        if timespan:
            if time_type == TimeType.DAY:
                # remap to a timespan in integer days
                timespan = _timespan_from_date(timespan)

            min_time, max_time = timespan

        return DataConfig(
            owid_dataset=dataset,
            dimensions=Dimension.from_dataset(dataset),
            selected_data=selected_data,
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


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Source:
    id: int
    name: str
    data_published_by: str
    data_publisher_source: str
    link: str
    retrieved_data: Optional[str]
    additional_info: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Variable:
    id: int
    name: str
    unit: Optional[str]
    description: str
    created_at: str
    updated_at: str
    code: Optional[str]
    coverage: Optional[str]
    timespan: Optional[str]
    datasetId: int
    sourceId: int
    shortUnit: Optional[str]
    display: dict
    columnOrder: int
    original_metadata: Optional[dict]
    dataset_name: str
    s_id: int
    s_name: str
    source: Source
    years: List[int]
    entities: List[int]
    values: List[float]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Entity:
    name: str
    code: Optional[str]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class StandaloneChartConfig(ChartConfig, DataConfig):
    "A chart config that contains all its own data."

    @property
    def is_standalone(self) -> bool:
        return True

    @classmethod
    def merge(cls, config: ChartConfig, data: DataConfig) -> "StandaloneChartConfig":
        kwargs = config.to_dict()  # type: ignore
        kwargs.update(data.to_dict())  # type: ignore
        return cls(**kwargs)
