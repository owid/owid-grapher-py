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
        self.entity: Optional[str] = None
        self.color: Optional[str] = None
        self.size: Optional[str] = None
        self.time_type = TimeType.YEAR
        self.selection: Optional[List[str]] = None
        self.timespan: Optional[Tuple[Any, Any]] = None
        self.x_unit: Optional[str] = None
        self.y_unit: Optional[str] = None

    def encode(
        self,
        x: Optional[str] = None,
        y: Optional[str] = None,
        entity: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
    ) -> "Chart":
        self.x = x
        self.y = y
        self.entity = entity
        self.color = color
        self.size = size

        # fail early if there's been a typo
        for col in [x, y, entity, color, size]:
            if col and col not in self.data.columns:
                raise ValueError(f"no such column: {col}")

        if x == "date":
            self.time_type = TimeType.DAY

        self.config.hide_legend = not entity

        return self

    def label(
        self, title: str = "", subtitle: str = "", source_desc: str = "", note: str = ""
    ) -> "Chart":
        self.config.title = title
        self.config.subtitle = subtitle
        self.config.source_desc = source_desc
        self.config.note = note
        return self

    def axis(
        self,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        x_unit: Optional[str] = None,
        y_unit: Optional[str] = None,
        x_scale: Optional[Literal["linear", "log"]] = None,
        y_scale: Optional[Literal["linear", "log"]] = None,
        x_scale_control: Optional[bool] = None,
        y_scale_control: Optional[bool] = None,
    ) -> "Chart":
        if x_label is not None:
            self.config.x_axis["label"] = x_label
        if y_label is not None:
            self.config.y_axis["label"] = y_label
        if x_unit is not None:
            self.x_unit = x_unit
        if y_unit is not None:
            self.y_unit = y_unit
        if x_scale is not None:
            self.config.x_axis["scaleType"] = x_scale
        if y_scale is not None:
            self.config.y_axis["scaleType"] = y_scale
        if x_scale_control is not None:
            self.config.x_axis["canChangeScaleType"] = x_scale_control
        if y_scale_control is not None:
            self.config.y_axis["canChangeScaleType"] = y_scale_control
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
            # Update y_axis without overwriting existing settings
            self.config.y_axis["scaleType"] = "linear"
            self.config.y_axis["canChangeScaleType"] = scale_control

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

    def export(self, include_data=True) -> Dict[str, Any]:
        """Export the full config including data (for debugging)."""
        self.config.auto_improve()
        config = self.config.to_dict()  # type: ignore
        config.update(self.data_config().to_dict(self.config.type))
        config = prune(config)
        if not include_data:
            del config["owidDataset"]["data"]
        return config

    def data_config(self) -> "DataConfig":
        if not self.x or not self.y:
            raise ValueError("must provide an x and y encoding")
        return DataConfig.from_data(
            self.data,
            x=self.x,
            y=self.y,
            entity=self.entity,
            color=self.color,
            size=self.size,
            time_type=self.time_type,
            chart_type=self.config.type,
            selection=self.selection,
            timespan=self.timespan,
            x_unit=self.x_unit,
            y_unit=self.y_unit,
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
    x_axis: dict = field(default_factory=dict)
    y_axis: dict = field(default_factory=dict)

    def auto_improve(self):
        if self.title and self.type == "LineChart":
            self.hide_title_annotation = False


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class Dimension:
    """
    "dimensions": [{"property": "y", "variableName": "population"}],
    """

    property: Literal["y", "x", "color"]
    variable_name: str
    display: Optional[dict] = field(default_factory=dict)


@dataclass
class DataConfig:
    """Stores data and column mappings for chart rendering."""

    df: pd.DataFrame
    x_col: str  # Time column (or x-axis for scatter)
    y_cols: List[str]  # Value column(s)
    entity_col: Optional[str]  # Entity/grouping column
    year_col: Optional[str]  # Year column (for scatter plots with time)
    color_col: Optional[str]  # Color column (for scatter plots, maps to colorSlug)
    size_col: Optional[str]  # Size column (for scatter plots)
    time_type: TimeType
    chart_type: ChartType
    selected_entity_names: List[str]
    min_time: Optional[Any] = None
    max_time: Optional[int] = None
    x_unit: Optional[str] = None  # Unit for x-axis variable
    y_unit: Optional[str] = None  # Unit for y-axis variable

    @classmethod
    def from_data(
        cls,
        df: pd.DataFrame,
        x: str,
        y: str,
        entity: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        time_type: "TimeType" = TimeType.YEAR,
        chart_type: ChartType = "LineChart",
        selection: Optional[List[str]] = None,
        timespan: Optional[Tuple[Any, Any]] = None,
        x_unit: Optional[str] = None,
        y_unit: Optional[str] = None,
    ) -> "DataConfig":
        df = df.copy()

        year_col: Optional[str] = None
        color_col: Optional[str] = None

        # Determine entity column and selection
        if chart_type == "ScatterPlot":
            # For scatter: x and y are both value columns, entity is grouping
            entity_col = entity
            y_cols = [x, y]  # Both are "value" columns for scatter
            color_col = color  # Optional color encoding for scatter
            # Don't auto-select all entities for scatter plots - let grapher handle it
            if selection is None:
                selection = []
            # Check if dataframe has a year column
            if "year" in df.columns:
                year_col = "year"
        elif chart_type in ("DiscreteBar", "StackedDiscreteBar"):
            # For bar charts: y is entity, x is value
            entity_col = y
            y_cols = [x]
            if selection is None:
                selection = list(df[y].unique())
        else:
            # For line charts: x is time, y is value, entity is grouping
            entity_col = entity
            y_cols = [y]
            if selection is None:
                if entity:
                    selection = list(df[entity].unique())
                else:
                    selection = [y]  # Use column name as entity

        # Handle timespan
        min_time, max_time = None, None
        if timespan:
            if time_type == TimeType.DAY:
                timespan = _timespan_from_date(timespan)
            min_time, max_time = timespan

        # For scatter plots, always use 'latest'
        if chart_type == "ScatterPlot" and min_time is None:
            min_time = "latest"

        return DataConfig(
            df=df,
            x_col=x,
            y_cols=y_cols,
            entity_col=entity_col,
            year_col=year_col,
            color_col=color_col,
            size_col=size,
            time_type=time_type,
            chart_type=chart_type,
            selected_entity_names=selection,
            min_time=min_time,
            max_time=max_time,
            x_unit=x_unit,
            y_unit=y_unit,
        )

    def _get_dimensions(self) -> List[Dimension]:
        """Build dimension list based on chart type."""
        if self.chart_type == "ScatterPlot":
            # For scatter: y_cols[0] is x-axis, y_cols[1] is y-axis
            return [
                Dimension(property="y", variable_name=self.y_cols[1]),
                Dimension(property="x", variable_name=self.y_cols[0]),
            ]
        else:
            # For other charts: one dimension per y column
            return [Dimension(property="y", variable_name=col) for col in self.y_cols]

    def to_dict(self, chart_type: ChartType) -> Dict[Any, Any]:
        display = DATE_DISPLAY if self.time_type == TimeType.DAY else {}

        # Build metadata for columns
        metadata: Dict[str, Any] = {}
        for col in self.y_cols:
            col_display = display.copy()
            # For scatter plots: y_cols[0] is x-axis, y_cols[1] is y-axis
            if chart_type == "ScatterPlot":
                if col == self.y_cols[0] and self.x_unit:
                    col_display["unit"] = self.x_unit
                elif col == self.y_cols[1] and self.y_unit:
                    col_display["unit"] = self.y_unit
            else:
                # For other charts, apply y_unit to all y columns
                if self.y_unit:
                    col_display["unit"] = self.y_unit
            metadata[col] = {"display": col_display} if col_display else {"display": {}}

        # Rename entity column to entityName for OwidTable
        df = self.df.copy()
        if self.entity_col and self.entity_col in df.columns:
            df = df.rename(columns={self.entity_col: "entityName"})

        doc: Dict[str, Any] = {
            "selectedEntityNames": self.selected_entity_names,
            "owidDataset": {
                "data": df.to_dict(orient="list"),
                "metadata": metadata,
            },
            "dimensions": [d.to_dict() for d in self._get_dimensions()],  # type: ignore
            "chartTypes": [chart_type],
        }

        if self.min_time is not None:
            doc["minTime"] = self.min_time
        if self.max_time is not None:
            doc["maxTime"] = self.max_time
        if self.size_col is not None:
            doc["sizeSlug"] = self.size_col
        if self.color_col is not None:
            doc["colorSlug"] = self.color_col

        return doc


def _build_column_defs(config: Dict[str, Any]) -> str:
    """Build columnDefs array from metadata for OwidTable constructor."""
    owid_dataset = config.get("owidDataset", {})
    metadata = owid_dataset.get("metadata", {})

    column_defs = []
    for col_name, col_metadata in metadata.items():
        col_def = {
            "slug": col_name,
            "type": "Numeric"
        }

        # Extract display settings if present
        display = col_metadata.get("display", {})
        if display:
            col_def["display"] = display

        column_defs.append(col_def)

    # Return as JSON string for embedding in JavaScript
    return json.dumps(column_defs)


def _config_to_grapher(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build GrapherState config from the export config."""
    dimensions = config.get("dimensions", [])
    chart_types = config.get("chartTypes", [])
    is_scatter = "ScatterPlot" in chart_types

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
            var_name = dim.get("variableName")
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
        # For non-scatter plots, collect variable names from dimensions as ySlugs
        y_slugs = [
            dim.get("variableName") for dim in dimensions if dim.get("variableName")
        ]
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
        "xAxis",
        "yAxis",
        "sizeSlug",
        "colorSlug",
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

    # Build column definitions from metadata
    column_defs = _build_column_defs(config)

    # Build grapher config from the config dict
    grapher_config = _config_to_grapher(config)

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
      const columnDefs = {column_defs};
      const table = new OwidTable(csvData, columnDefs);

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
    """Convert the owidDataset format to CSV for OwidTable."""
    owid_dataset = config.get("owidDataset", {})
    data = owid_dataset.get("data", {})

    if not data:
        return ""

    # Convert dict of lists back to dataframe and then to CSV
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def prune(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: prune(v) if isinstance(v, dict) else v for k, v in d.items() if v is not None
    }


def _timespan_from_date(timespan: Tuple[str, str]) -> Tuple[int, int]:
    from_date_d = parse(timespan[0]).date()
    to_date_d = parse(timespan[1]).date()

    offset = dt.date(1970, 1, 1).toordinal()

    return (from_date_d.toordinal() - offset, to_date_d.toordinal() - offset)
