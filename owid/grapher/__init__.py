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
            self.config.tab = "map"

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
        """Export the full config including data (for debugging)."""
        self.config.auto_improve()
        config = self.config.to_dict()  # type: ignore
        config.update(self.data_config().to_dict(self.config.type))
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


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
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


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class Dimension:
    """
    "dimensions": [{"property": "y", "variableId": 1}],
    """

    property: Literal["y", "x", "color"]
    variable_id: int
    display: Optional[dict] = field(default_factory=dict)

    @classmethod
    def single_y(cls) -> "Dimension":
        return Dimension(property="y", variable_id=1)

    @classmethod
    def from_dataset(
        cls,
        dataset: "Dataset",
        chart_type: ChartType = "LineChart",
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
    ) -> List["Dimension"]:
        if chart_type == "ScatterPlot":
            # Scatter plots need x and y dimensions
            # Find variables by name for correct mapping
            y_var_id = None
            x_var_id = None

            for var_id, var in dataset.variables.items():
                if y_col and var.name == y_col:
                    y_var_id = var_id
                if x_col and var.name == x_col:
                    x_var_id = var_id

            if y_var_id and x_var_id:
                return [
                    Dimension(property="y", variable_id=y_var_id),
                    Dimension(property="x", variable_id=x_var_id),
                ]
            else:
                # Fallback to old behavior if names not found
                variables = list(dataset.variables.values())
                if len(variables) >= 2:
                    return [
                        Dimension(property="y", variable_id=variables[0].id),
                        Dimension(property="x", variable_id=variables[1].id),
                    ]
                else:
                    return [
                        Dimension(property="y", variable_id=v.id) for v in variables
                    ]
        else:
            return [
                Dimension(property="y", variable_id=v.id)
                for v in dataset.variables.values()
            ]


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class Variable:
    id: int
    name: str
    years: List[int]
    entities: List[int]
    values: List[float]
    short_unit: Optional[str] = None
    display: Optional[Dict[str, Any]] = None


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
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
    min_time: Optional[Any] = None  # Can be int, "latest", or None
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
        elif chart_type == "ScatterPlot":
            df = cls._reshape_scatter_plot(df, x, y, c)
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

        # For scatter plots, use 'latest' by default
        if chart_type == "ScatterPlot" and min_time is None:
            min_time = "latest"  # type: ignore

        return DataConfig(
            dataset=dataset,
            dimensions=Dimension.from_dataset(dataset, chart_type, x_col=x, y_col=y),
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

    @staticmethod
    def _reshape_scatter_plot(
        df: pd.DataFrame, x: str, y: str, c: Optional[str] = None
    ) -> pd.DataFrame:
        """Reshape data for scatter plots.

        For scatter plots, we need both x and y values in a single row per entity,
        stored as separate variables (columns) in the normalized format.
        Each observation gets a unique year (using row index) to prevent merging.
        """
        if c:
            # c is the entity dimension
            entity_col = c
        else:
            # No color dimension, create a single entity
            df = df.copy()
            df["__entity"] = "data"
            entity_col = "__entity"

        # Create normalized format with entity, year, and both x/y as separate columns
        # Use row index as year to ensure each point is separate
        result_rows = []

        for idx, row in df.iterrows():
            entity_name = row[entity_col]
            # Use index as year to make each observation unique
            year = idx if isinstance(idx, int) else 2021

            # Create a row with x value
            result_rows.append(
                {
                    "entity": entity_name,
                    "year": year,
                    "variable": x,
                    "value": row[x],
                }
            )

            # Create a row with y value
            result_rows.append(
                {
                    "entity": entity_name,
                    "year": year,
                    "variable": y,
                    "value": row[y],
                }
            )

        return pd.DataFrame(result_rows)

    def to_dict(self, chart_type: ChartType) -> Dict[Any, Any]:
        ds = {}
        doc = {
            "selectedEntityNames": self.selected_entity_names,
            "owidDataset": ds,
            "dimensions": [d.to_dict() for d in self.dimensions],  # type: ignore
            "chartTypes": [chart_type],
        }

        if self.min_time is not None:
            doc["minTime"] = self.min_time
        if self.max_time is not None:
            doc["maxTime"] = self.max_time

        for var_id, var in self.dataset.variables.items():
            ds[var_id] = {
                "data": {
                    "entities": var.entities,
                    "years": var.years,
                    "values": var.values,
                },
                "metadata": {
                    "id": var_id,
                    "name": var.name,
                    "display": var.display,
                    "dimensions": {
                        "entities": {
                            "values": [
                                {"id": e.id, "name": e.name}
                                for e in self.dataset.entity_key.values()
                            ],
                        },
                        "years": {
                            "values": [{"id": y} for y in sorted(set(var.years))]
                        },
                    },
                },
            }

        return doc


def _build_grapher_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build GrapherState config from the export config."""
    owid_dataset = config.get("owidDataset", {})
    dimensions = config.get("dimensions", [])
    chart_types = config.get("chartTypes", [])
    is_scatter = "ScatterPlot" in chart_types

    # Build mapping of variable IDs to names
    var_id_to_name = {}
    for var_data in owid_dataset.values():
        metadata = var_data.get("metadata", {})
        var_id = metadata.get("id")
        var_name = metadata.get("name", "")
        if var_id and var_name:
            var_id_to_name[var_id] = var_name

    grapher_config: Dict[str, Any] = {
        "hideLogo": config.get("hideLogo", True),
        "selectedEntityNames": config.get("selectedEntityNames", []),
    }

    # Use chartTypes directly from config
    if config.get("chartTypes"):
        grapher_config["chartTypes"] = config["chartTypes"]

    # For scatter plots, separate x and y slugs
    if is_scatter:
        y_var_names = []
        x_var_name = None

        for dim in dimensions:
            var_id = dim.get("variableId")
            var_name = var_id_to_name.get(var_id)
            if var_name:
                if dim.get("property") == "y":
                    y_var_names.append(var_name)
                elif dim.get("property") == "x":
                    x_var_name = var_name

        if y_var_names:
            grapher_config["ySlugs"] = " ".join(y_var_names)
        if x_var_name:
            grapher_config["xSlug"] = x_var_name
    else:
        # For non-scatter plots, just collect all variable names as ySlugs
        y_slugs = []
        for var_data in owid_dataset.values():
            metadata = var_data.get("metadata", {})
            var_name = metadata.get("name", "")
            if var_name:
                y_slugs.append(var_name)

        if y_slugs:
            grapher_config["ySlugs"] = " ".join(y_slugs)

    # Pass through common fields
    for field_name in [
        "title",
        "subtitle",
        "note",
        "sourceDesc",
        "hasMapTab",
        "tab",
        "stackMode",
        "minTime",
        "maxTime",
        "yAxis",
    ]:
        if config.get(field_name):
            grapher_config[field_name] = config[field_name]

    # Pass through hide toggles
    for field_name in ["hideRelativeToggle", "hideEntityControls"]:
        if field_name in config:
            grapher_config[field_name] = config[field_name]

    return grapher_config


def generate_iframe(config: Dict[str, Any]) -> str:
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))

    # Extract data for CSV and prepare config for GrapherState API
    csv_data = _config_to_csv(config)

    print(csv_data)

    # Build grapher config from the config dict
    grapher_config = _build_grapher_config(config)

    iframe_contents = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Lato:300,400,400i,700,700i|Playfair+Display:400,700&display=swap"
      rel="stylesheet"
    />
    <link
      rel="stylesheet"
      href="https://expose-grapher-state.owid.pages.dev/assets/owid.css"
    />
    <style>
      body {{ margin: 0; padding: 0; }}
      figure {{ width: 100%; height: 100%; margin: 0; }}
      .error {{ color: red; padding: 20px; background: #fee; border-radius: 5px; }}
      /* Hide UI elements for cleaner notebook display */
      .grapher-share-button, .shareMenuOuter, .GrapherShareMenu,
      a[data-track-note="chart_click_explore"], .exploreDataButton,
      .originUrl, .SourcesFooter, .SourcesFooterHTML,
      .GrapherFooter__sourcesAndLicense {{ display: none !important; }}
    </style>
  </head>
  <body>
    <figure id="grapher-container"></figure>
    <script type="module" src="https://expose-grapher-state.owid.pages.dev/assets/owid.mjs"></script>
    <script type="module">
      await new Promise((resolve) => setTimeout(resolve, 500));

      const {{ Grapher, GrapherState, OwidTable, React, createRoot }} = window;
      const container = document.getElementById("grapher-container");

      if (!GrapherState || !OwidTable || !React || !createRoot) {{
        container.innerHTML = '<div class="error">Required exports not available. Check console.</div>';
        throw new Error("Required exports not available");
      }}

      const csvData = `{csv_data}`;
      const table = new OwidTable(csvData);

      const grapherState = new GrapherState({{
        table: table,
        ...{json.dumps(grapher_config)},
        isConfigReady: true,
        isDataReady: true,
      }});

      const reactRoot = createRoot(container);
      reactRoot.render(React.createElement(Grapher, {{ grapherState }}));
    </script>
  </body>
</html>
"""  # noqa
    # Escape for the outer template literal (order matters: backslash first)
    iframe_contents = iframe_contents.replace("\\", "\\\\")
    iframe_contents = iframe_contents.replace("`", "\\`")
    iframe_contents = iframe_contents.replace("${", "\\${")
    iframe_contents = iframe_contents.replace("</script>", "<\\/script>")
    return f"""
        <div id="{iframe_name}_wrapper" style="position: relative; width: 100%; height: 600px;">
            <iframe id="{iframe_name}" style="width: 100%; height: 100%; border: 0px none; pointer-events: none;"></iframe>
        </div>
        <script>
            document.getElementById("{iframe_name}").contentDocument.write(`{iframe_contents}`);
            document.getElementById("{iframe_name}").contentDocument.close();
            // Enable interaction on click (wrapper captures click), disable on mouse leave
            document.getElementById("{iframe_name}_wrapper").addEventListener("click", function() {{
                document.getElementById("{iframe_name}").style.pointerEvents = "auto";
            }});
            document.getElementById("{iframe_name}").addEventListener("mouseleave", function() {{
                this.style.pointerEvents = "none";
            }});
        </script>
    """  # noqa


def _config_to_csv(config: Dict[str, Any]) -> str:
    """Convert the old owidDataset format to CSV for OwidTable."""
    owid_dataset = config.get("owidDataset", {})

    # Build entity name lookup from the first variable's metadata
    entity_lookup: Dict[int, str] = {}
    # Use dict to merge rows by (entity_id, year) key
    rows_dict: Dict[Tuple[int, int], Dict[str, Any]] = {}

    for var_id, var_data in owid_dataset.items():
        metadata = var_data.get("metadata", {})
        var_name = metadata.get("name", f"var_{var_id}")

        # Build entity lookup from dimensions
        dims = metadata.get("dimensions", {})
        entity_values = dims.get("entities", {}).get("values", [])
        for e in entity_values:
            entity_lookup[e["id"]] = e["name"]

        # Extract data points
        data = var_data.get("data", {})
        entities = data.get("entities", [])
        years = data.get("years", [])
        values = data.get("values", [])

        for entity_id, year, value in zip(entities, years, values):
            entity_name = entity_lookup.get(entity_id, f"entity_{entity_id}")
            key = (entity_id, year)

            # Get or create row for this entity/year
            if key not in rows_dict:
                rows_dict[key] = {
                    "entityName": entity_name,
                    "entityId": entity_id,
                    "year": year,
                }

            # Add this variable's value to the row
            rows_dict[key][var_name] = value

    if not rows_dict:
        return "entityName,entityId,year,value\n"

    # Convert dict to list of rows
    rows = list(rows_dict.values())

    # Get all unique column names (variable names)
    all_columns = ["entityName", "entityId", "year"]
    var_columns = set()
    for row in rows:
        var_columns.update(k for k in row.keys() if k not in all_columns)
    all_columns.extend(sorted(var_columns))

    # Build CSV
    csv_lines = [",".join(all_columns)]
    for row in rows:
        csv_lines.append(",".join(str(row.get(col, "")) for col in all_columns))

    return "\n".join(csv_lines)


def prune(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: prune(v) if isinstance(v, dict) else v for k, v in d.items() if v is not None
    }


def _timespan_from_date(timespan: Tuple[str, str]) -> Tuple[int, int]:
    from_date_d = parse(timespan[0]).date()
    to_date_d = parse(timespan[1]).date()

    offset = dt.date(1970, 1, 1).toordinal()

    return (from_date_d.toordinal() - offset, to_date_d.toordinal() - offset)
