# -*- coding: utf-8 -*-
#
#  grapher.py
#  notebooks
#

import datetime as dt
import json
import random
import re
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd
from dataclasses_json import LetterCase, dataclass_json
from dateutil.parser import parse

from owid.grapher.grapher_state import (  # noqa: F401 - re-exported for public API
    BinningStrategy,
    ColorScaleConfig,
    ColorSchemeName,
    GrapherState,
    MapConfig,
)

DATE_DISPLAY = {"yearIsDay": True, "zeroDay": "1970-01-01"}

# Characters that are safe in OWID slugs (alphanumeric, underscore, hyphen)
_UNSAFE_SLUG_CHARS = re.compile(r"[^a-zA-Z0-9_\-]")


def _sanitize_slug(name: str) -> str:
    """Sanitize a column name for use as a slug.

    OWID uses space-separated slug strings, so spaces and other special characters
    must be replaced. Only alphanumeric characters, underscores, and hyphens are kept.
    """
    return _UNSAFE_SLUG_CHARS.sub("_", name)


# Mapping from GrapherChartType to tab name
_CHART_TYPE_TO_TAB: Dict[str, str] = {
    "LineChart": "line",
    "DiscreteBar": "discrete-bar",
    "StackedDiscreteBar": "stacked-discrete-bar",
    "ScatterPlot": "scatter",
    "StackedArea": "stacked-area",
    "SlopeChart": "slope",
    "StackedBar": "stacked-bar",
    "Marimekko": "marimekko",
}


class Chart:
    """Create interactive OWID charts from pandas DataFrames.

    The Chart class provides a declarative API for building interactive visualizations
    using OWID's Grapher library. Charts are configured through method chaining and
    render directly in Jupyter notebooks.

    Multiple chart types can be enabled by chaining mark_*() methods. The first one
    called becomes the default view, or use show() to set a specific default tab.

    Args:
        data: A pandas DataFrame containing the data to visualize. The DataFrame should
            have columns for time/x-axis, values/y-axis, and optionally entities for grouping.

    Example:
        ```python
        import pandas as pd
        from owid.grapher import Chart

        df = pd.DataFrame({
            'year': [2020, 2021, 2022],
            'country': ['USA', 'China', 'India'],
            'gdp': [21.4, 14.7, 2.9]
        })

        # Single chart type
        Chart(df).mark_line().encode(
            x='year',
            y='gdp',
            entity='country'
        ).label(
            title='GDP by Country'
        )

        # Multiple chart types with bar as default
        Chart(df).mark_line().mark_bar().show("discrete-bar").encode(...)
        ```
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.config = ChartConfig()
        self.chart_types: List[str] = []  # Available chart types
        self.default_tab: Optional[str] = None  # Which tab to show by default
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
        self.variable_configs: Dict[str, "VariableConfig"] = {}  # Column metadata

    def encode(
        self,
        x: Optional[str] = None,
        y: Optional[str] = None,
        entity: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
    ) -> "Chart":
        """Map DataFrame columns to visual properties.

        This method establishes the visual encoding by mapping DataFrame columns to
        chart dimensions. The behavior varies by chart type:

        - **Line/Bar charts**: `x` is time, `y` is values, `entity` groups lines/bars
        - **Scatter plots**: `x` and `y` are both numeric values, `entity` groups points

        Args:
            x: Column name for x-axis. For line/bar charts, typically a time column
                ('year', 'date'). For scatter plots, a numeric value column.
            y: Column name for y-axis values to plot. For bar charts, can be the entity
                column if you want entities on the y-axis.
            entity: Column name for grouping data (e.g., 'country', 'region'). Each unique
                value becomes a separate line/series. Optional for single-series charts.
            color: Column name for color encoding in scatter plots. Values map to colors.
            size: Column name for size encoding in scatter plots. Values map to point sizes.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If a specified column name is not found in the DataFrame.

        Example:
            ```python
            # Line chart with multiple countries
            Chart(df).mark_line().encode(
                x='year',
                y='population',
                entity='country'
            )

            # Scatter plot with color and size
            Chart(df).mark_scatter().encode(
                x='gdp_per_capita',
                y='life_expectancy',
                entity='country',
                color='continent',
                size='population'
            )
            ```
        """
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
        """Add labels and text to the chart.

        Args:
            title: Chart title.
            subtitle: Chart subtitle.
            source_desc: Data source attribution.
            note: Additional notes or footnotes.

        Returns:
            Self for method chaining.
        """
        self.config.title = title
        self.config.subtitle = subtitle
        self.config.source_desc = source_desc
        self.config.note = note
        return self

    def xaxis(
        self,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        scale: Optional[Literal["linear", "log"]] = None,
        scale_control: Optional[bool] = None,
    ) -> "Chart":
        """Configure the x-axis.

        Args:
            label: Axis label text.
            unit: Unit of measurement (e.g., '$', 'kg').
            scale: Scale type ('linear' or 'log').
            scale_control: Allow users to toggle scale.

        Returns:
            Self for method chaining.
        """
        if label is not None:
            self.config.x_axis["label"] = label
        if unit is not None:
            self.x_unit = unit
        if scale is not None:
            self.config.x_axis["scaleType"] = scale
        if scale_control is not None:
            self.config.x_axis["canChangeScaleType"] = scale_control
        return self

    def yaxis(
        self,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        scale: Optional[Literal["linear", "log"]] = None,
        scale_control: Optional[bool] = None,
    ) -> "Chart":
        """Configure the y-axis.

        Args:
            label: Axis label text.
            unit: Unit of measurement (e.g., '$', 'kg').
            scale: Scale type ('linear' or 'log').
            scale_control: Allow users to toggle scale.

        Returns:
            Self for method chaining.
        """
        if label is not None:
            self.config.y_axis["label"] = label
        if unit is not None:
            self.y_unit = unit
        if scale is not None:
            self.config.y_axis["scaleType"] = scale
        if scale_control is not None:
            self.config.y_axis["canChangeScaleType"] = scale_control
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
        """Configure both axes at once.

        Convenience method for setting properties on both axes. For single-axis
        configuration, use xaxis() or yaxis() instead.

        Args:
            x_label: Label text for x-axis.
            y_label: Label text for y-axis.
            x_unit: Unit suffix for x-axis values (e.g., '$', '%', 'kg').
            y_unit: Unit suffix for y-axis values.
            x_scale: Scale type for x-axis ('linear' or 'log').
            y_scale: Scale type for y-axis ('linear' or 'log').
            x_scale_control: If True, adds UI control to toggle x-axis scale.
            y_scale_control: If True, adds UI control to toggle y-axis scale.

        Returns:
            Self for method chaining.
        """
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

    def _add_chart_type(self, chart_type: str) -> None:
        """Add a chart type if not already present."""
        if chart_type not in self.chart_types:
            self.chart_types.append(chart_type)
        # First chart type added becomes the default tab
        if self.default_tab is None:
            self.default_tab = _CHART_TYPE_TO_TAB.get(chart_type, "chart")

    def mark_scatter(self) -> "Chart":
        """Add scatter plot to available chart types.

        Scatter plots display individual data points with x and y positions. Use `color`
        and `size` encodings for additional dimensions. Best for showing relationships
        between two numeric variables.

        Can be combined with other mark_*() methods to enable multiple chart types.

        Returns:
            Self for method chaining.
        """
        self._add_chart_type("ScatterPlot")
        return self

    def mark_line(self) -> "Chart":
        """Add line chart to available chart types.

        Line charts connect data points with lines, ideal for showing trends over time.
        Multiple entities create multiple lines.

        Can be combined with other mark_*() methods to enable multiple chart types.

        Returns:
            Self for method chaining.
        """
        self._add_chart_type("LineChart")
        return self

    def mark_bar(self, stacked: bool = False) -> "Chart":
        """Add bar chart to available chart types.

        Bar charts display categorical data with rectangular bars. Bars can be shown
        side-by-side (default) or stacked on top of each other.

        Can be combined with other mark_*() methods to enable multiple chart types.

        Args:
            stacked: If True, creates a stacked bar chart where bars for different
                entities are stacked vertically. If False (default), bars are shown
                side-by-side.

        Returns:
            Self for method chaining.
        """
        chart_type = "StackedDiscreteBar" if stacked else "DiscreteBar"
        self._add_chart_type(chart_type)
        return self

    def mark_map(
        self,
        time_tolerance: Optional[int] = None,
        color_scheme: Optional[ColorSchemeName] = None,
        binning_strategy: Optional[BinningStrategy] = None,
        custom_numeric_values: Optional[List[float]] = None,
    ) -> "Chart":
        """Enable the map tab with optional configuration.

        Adds a world map visualization showing data geographically. Can be combined
        with other mark_*() methods.

        Args:
            time_tolerance: How many years to look back/forward for data
            color_scheme: Color scheme name (e.g., "Reds", "Blues", "YlOrRd")
            binning_strategy: How to bin values ("auto", "manual", "equalInterval", "quantiles")
            custom_numeric_values: Custom bin boundaries when using manual binning

        Returns:
            Self for method chaining.

        Example:
            ```python
            # Line chart with map, defaulting to map view
            Chart(df).mark_line().mark_map().show("map").encode(...)

            # Line chart with customized map
            Chart(df).mark_line().mark_map(
                color_scheme='Reds',
                binning_strategy='manual',
                custom_numeric_values=[0, 1000, 10000, 100000]
            ).encode(...)
            ```
        """
        self.config.has_map_tab = True

        # Set default tab to map if this is the first mark_*() call
        if self.default_tab is None:
            self.default_tab = "map"

        # Configure map options if any provided
        if any([time_tolerance, color_scheme, binning_strategy, custom_numeric_values]):
            color_scale = ColorScaleConfig(
                baseColorScheme=color_scheme,
                binningStrategy=binning_strategy,
                customNumericValues=custom_numeric_values,
            )
            self.config.map_config = MapConfig(
                timeTolerance=time_tolerance,
                colorScale=color_scale
                if any([color_scheme, binning_strategy, custom_numeric_values])
                else None,
            )

        return self

    def show(
        self,
        tab: Literal[
            "line",
            "discrete-bar",
            "stacked-discrete-bar",
            "scatter",
            "stacked-area",
            "slope",
            "stacked-bar",
            "marimekko",
            "map",
            "table",
        ],
    ) -> "Chart":
        """Set which tab to display by default.

        Use this to control which visualization is shown when the chart first loads.
        The tab must correspond to an enabled chart type (via mark_*() methods).

        Args:
            tab: The tab to show by default. Options:
                - "line": Line chart
                - "discrete-bar": Bar chart
                - "stacked-discrete-bar": Stacked bar chart
                - "scatter": Scatter plot
                - "map": World map
                - "table": Data table

        Returns:
            Self for method chaining.

        Example:
            ```python
            # Enable line and bar, but show bar by default
            Chart(df).mark_line().mark_bar().show("discrete-bar").encode(...)
            ```
        """
        self.default_tab = tab
        return self

    def interact(
        self,
        allow_relative: Optional[bool] = None,
        scale_control: Optional[bool] = None,
        entity_control: Optional[bool] = None,
    ) -> "Chart":
        """Add interactive controls to the chart.

        Args:
            allow_relative: Show relative/absolute toggle.
            scale_control: Show log/linear scale toggle.
            entity_control: Show entity/country picker.

        Returns:
            Self for method chaining.
        """
        if allow_relative is not None:
            self.config.hide_relative_toggle = False

        if scale_control is not None:
            # Update y_axis without overwriting existing settings
            self.config.y_axis["scaleType"] = "linear"
            self.config.y_axis["canChangeScaleType"] = scale_control

        if entity_control is not None:
            self.config.hide_entity_controls = not entity_control

        return self

    def select(
        self,
        entities: Optional[List[str]] = None,
        timespan: Optional[Tuple[Any, Any]] = None,
    ) -> "Chart":
        """Pre-select entities and time range.

        Args:
            entities: List of entity names to display.
            timespan: Tuple of (start, end) for time range.

        Returns:
            Self for method chaining.
        """
        if entities:
            self.selection = entities

        if timespan:
            if isinstance(timespan, (str, int)):
                timespan = (timespan, None)
            self.timespan = timespan

        return self

    def transform(self, relative: bool) -> "Chart":
        """Transform data to relative or absolute values.

        Display values as percentage change from a baseline (relative mode) or as
        absolute values (default). In relative mode, the first time period serves
        as the baseline (100%).

        Args:
            relative: If True, show values as percentage change from baseline.
                If False, show absolute values.

        Returns:
            Self for method chaining.
        """
        self.config.stack_mode = "relative" if relative else "absolute"
        return self

    def filter(self, matching_entities_only: bool = True) -> "Chart":
        """Filter entities to only show those with complete data.

        When enabled, only entities that have data for all time periods and dimensions
        will be shown. Useful for ensuring fair comparisons by excluding entities with
        incomplete data.

        Args:
            matching_entities_only: If True, only show entities with complete data across
                all dimensions and time periods. If False, show all entities even with gaps.

        Returns:
            Self for method chaining.
        """
        self.config.matching_entities_only = matching_entities_only
        return self

    def variable(
        self,
        column: str,
        name: Optional[str] = None,
        description_short: Optional[str] = None,
        description_from_producer: Optional[str] = None,
        description_processing: Optional[str] = None,
        description_key: Optional[List[str]] = None,
        unit: Optional[str] = None,
        short_unit: Optional[str] = None,
        source_name: Optional[str] = None,
        source_link: Optional[str] = None,
    ) -> "Chart":
        """Add rich metadata to a data column/variable.

        Configures display properties and documentation for a column that will
        appear in tooltips, the data table, and source information.

        Args:
            column: Name of the DataFrame column to configure.
            name: Display name (e.g., "Population" instead of "pop").
            description_short: Brief description shown in tooltips.
            description_from_producer: Original description from data source.
            description_processing: How the data was processed/transformed.
            description_key: List of key points about the variable.
            unit: Full unit name (e.g., "million people").
            short_unit: Abbreviated unit for compact display (e.g., "M").
            source_name: Name of the data source.
            source_link: URL to the data source.

        Returns:
            Self for method chaining.

        Note:
            The timespan is computed automatically from the data's time column.

        Example:
            ```python
            Chart(df).mark_line().encode(
                x='year',
                y='population',
                entity='country'
            ).variable(
                'population',
                name='Population',
                description_short='Total population in millions',
                unit='million people',
                short_unit='M',
                source_name='World Bank',
                source_link='https://data.worldbank.org'
            )
            ```
        """
        self.variable_configs[column] = VariableConfig(
            name=name,
            description_short=description_short,
            description_from_producer=description_from_producer,
            description_processing=description_processing,
            description_key=description_key,
            unit=unit,
            short_unit=short_unit,
            source_name=source_name,
            source_link=source_link,
        )
        return self

    def _repr_html_(self):
        export = self.export()
        html = generate_iframe(
            export["csv_data"], export["column_defs"], export["grapher_config"]
        )
        return html

    def _get_primary_chart_type(self) -> "ChartType":
        """Get the primary chart type (first in the list, or LineChart as default)."""
        if self.chart_types:
            return self.chart_types[0]  # type: ignore
        return "LineChart"

    def _prepare_data(
        self,
    ) -> Tuple[
        pd.DataFrame,
        str,
        List[str],
        Optional[str],
        Optional[str],
        Optional[str],
        List[str],
        Optional[Any],
        Optional[int],
    ]:
        """Prepare the dataframe and compute column mappings for export.

        Returns a tuple of:
            (df, x_col, y_cols, entity_col, color_col, year_col, selected_entities, min_time, max_time)
        """
        if not self.x or not self.y:
            raise ValueError("must provide an x and y encoding")

        df = self.data.copy()
        x_col = self.x
        y_col = self.y
        entity_col = self.entity
        color_col = self.color
        size_col = self.size
        chart_type = self._get_primary_chart_type()

        # Sanitize column names (special characters break OWID's slug format)
        rename_map = {
            col: _sanitize_slug(col)
            for col in df.columns
            if _UNSAFE_SLUG_CHARS.search(col)
        }
        if rename_map:
            df = df.rename(columns=rename_map)
            if x_col in rename_map:
                x_col = rename_map[x_col]
            if y_col in rename_map:
                y_col = rename_map[y_col]
            if entity_col and entity_col in rename_map:
                entity_col = rename_map[entity_col]
            if color_col and color_col in rename_map:
                color_col = rename_map[color_col]
            if size_col and size_col in rename_map:
                size_col = rename_map[size_col]

        # Determine column mappings based on chart type
        year_col: Optional[str] = None
        y_cols: List[str]
        selected_entities: List[str]

        if chart_type == "ScatterPlot":
            y_cols = [x_col, y_col]  # Both are "value" columns for scatter
            if self.selection is None:
                selected_entities = []  # Don't auto-select for scatter plots
            else:
                selected_entities = self.selection
            if "year" in df.columns:
                year_col = "year"
        elif chart_type in ("DiscreteBar", "StackedDiscreteBar"):
            if entity_col:
                y_cols = [y_col]
                if self.selection is None:
                    selected_entities = list(df[entity_col].unique())
                else:
                    selected_entities = self.selection
            else:
                # Fall back to y as entity, x as value (horizontal bars)
                entity_col = y_col
                y_cols = [x_col]
                if self.selection is None:
                    selected_entities = list(df[y_col].unique())
                else:
                    selected_entities = self.selection
        else:
            # Line charts: x is time, y is value, entity is grouping
            y_cols = [y_col]
            if self.selection is None:
                if entity_col:
                    selected_entities = list(df[entity_col].unique())
                else:
                    selected_entities = [y_col]  # Use column name as entity
            else:
                selected_entities = self.selection

        # Handle timespan
        min_time: Optional[Any] = None
        max_time: Optional[int] = None
        if self.timespan:
            timespan = self.timespan
            if self.time_type == TimeType.DAY:
                timespan = _timespan_from_date(timespan)
            min_time, max_time = timespan

        # For scatter plots, default to 'latest'
        if chart_type == "ScatterPlot" and min_time is None:
            min_time = "latest"

        # Rename entity column to entityName for OwidTable
        if entity_col and entity_col in df.columns:
            df = df.rename(columns={entity_col: "entityName"})

        # Rename x column to expected time column name for OwidTable
        if chart_type not in ("ScatterPlot", "DiscreteBar", "StackedDiscreteBar"):
            expected_time_col = "date" if self.time_type == TimeType.DAY else "year"
            if x_col != expected_time_col and x_col in df.columns:
                df = df.rename(columns={x_col: expected_time_col})

        return (
            df,
            x_col,
            y_cols,
            entity_col,
            color_col,
            year_col,
            selected_entities,
            min_time,
            max_time,
        )

    def _build_csv(self, df: pd.DataFrame) -> str:
        """Build CSV string from prepared dataframe."""
        return df.to_csv(index=False)

    def _build_column_defs(
        self, y_cols: List[str], x_col: str, year_col: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Build column definitions for OwidTable."""
        chart_type = self._get_primary_chart_type()
        display = DATE_DISPLAY if self.time_type == TimeType.DAY else {}

        column_defs: List[Dict[str, Any]] = []
        for col in y_cols:
            col_display = display.copy()

            # Apply units based on chart type
            if chart_type == "ScatterPlot":
                if col == y_cols[0] and self.x_unit:
                    col_display["unit"] = self.x_unit
                elif col == y_cols[1] and self.y_unit:
                    col_display["unit"] = self.y_unit
            else:
                if self.y_unit:
                    col_display["unit"] = self.y_unit

            col_def: Dict[str, Any] = {"slug": col, "type": "Numeric"}
            if col_display:
                col_def["display"] = col_display

            # Add rich metadata from variable_configs if available
            if col in self.variable_configs:
                var_config = self.variable_configs[col]
                var_dict = var_config.to_dict()  # type: ignore
                col_def.update(var_dict)

                # Auto-compute timespan from the time column
                time_col = year_col if chart_type == "ScatterPlot" else x_col
                if time_col and time_col in self.data.columns:
                    min_val = self.data[time_col].min()
                    max_val = self.data[time_col].max()
                    if min_val == max_val:
                        col_def["timespan"] = str(min_val)
                    else:
                        col_def["timespan"] = f"{min_val}–{max_val}"

            column_defs.append(col_def)

        return column_defs

    def _build_grapher_config(
        self,
        y_cols: List[str],
        x_col: str,
        color_col: Optional[str],
        selected_entities: List[str],
        min_time: Optional[Any],
        max_time: Optional[int],
    ) -> Dict[str, Any]:
        """Build GrapherState configuration dict."""
        chart_types = self.chart_types if self.chart_types else ["LineChart"]
        chart_type = self._get_primary_chart_type()
        is_scatter = chart_type == "ScatterPlot"

        grapher_config: Dict[str, Any] = {
            "hideLogo": self.config.hide_logo,
            "selectedEntityNames": selected_entities,
            "chartTypes": chart_types,
        }

        # Set tab
        if self.default_tab:
            grapher_config["tab"] = self.default_tab
        elif chart_types:
            grapher_config["tab"] = _CHART_TYPE_TO_TAB.get(chart_types[0], "line")

        # Set column slugs based on chart type
        if is_scatter:
            grapher_config["ySlugs"] = y_cols[1]  # y-axis value
            grapher_config["xSlug"] = y_cols[0]  # x-axis value
        else:
            grapher_config["ySlugs"] = " ".join(y_cols)

        # Title and text
        if self.config.title:
            grapher_config["title"] = self.config.title
        if self.config.subtitle:
            grapher_config["subtitle"] = self.config.subtitle
        if self.config.note:
            grapher_config["note"] = self.config.note
        if self.config.source_desc:
            grapher_config["sourceDesc"] = self.config.source_desc

        # Map tab
        if self.config.has_map_tab:
            grapher_config["hasMapTab"] = True

        # Stack mode
        if self.config.stack_mode != "absolute":
            grapher_config["stackMode"] = self.config.stack_mode

        # Time bounds
        if min_time is not None:
            grapher_config["minTime"] = min_time
        if max_time is not None:
            grapher_config["maxTime"] = max_time

        # Axis configuration
        if self.config.x_axis:
            grapher_config["xAxis"] = self.config.x_axis
        if self.config.y_axis:
            grapher_config["yAxis"] = self.config.y_axis

        # Additional slugs
        if self.size:
            grapher_config["sizeSlug"] = self.size
        if color_col:
            grapher_config["colorSlug"] = color_col

        # Hide toggles
        if self.config.hide_relative_toggle:
            grapher_config["hideRelativeToggle"] = True
        if self.config.hide_entity_controls:
            grapher_config["hideEntityControls"] = True
        if self.config.matching_entities_only:
            grapher_config["matchingEntitiesOnly"] = True

        # Map configuration
        if self.config.map_config is not None:
            map_config = self.config.map_config.to_dict()
            # Auto-set columnSlug from the first y column if not specified
            if "columnSlug" not in map_config and y_cols:
                map_config["columnSlug"] = y_cols[0]
            grapher_config["map"] = map_config

        return grapher_config

    def export(self) -> Dict[str, Any]:
        """Export the chart as the three components needed for rendering.

        Returns:
            Dictionary with keys:
                - csv_data: CSV string of the data
                - column_defs: List of column definition dicts for OwidTable
                - grapher_config: Dict of GrapherState configuration
        """
        (
            df,
            x_col,
            y_cols,
            entity_col,
            color_col,
            year_col,
            selected_entities,
            min_time,
            max_time,
        ) = self._prepare_data()

        return {
            "csv_data": self._build_csv(df),
            "column_defs": self._build_column_defs(y_cols, x_col, year_col),
            "grapher_config": self._build_grapher_config(
                y_cols, x_col, color_col, selected_entities, min_time, max_time
            ),
        }


class TimeType(Enum):
    """Enumeration for time dimension types.

    Determines how time values are interpreted and displayed in charts.

    Attributes:
        DAY: Daily or date-based data. Automatically detected when x='date'.
            Uses ISO date format (YYYY-MM-DD).
        YEAR: Annual data (default). Standard yearly time series.
    """

    DAY = "day"
    YEAR = "year"


ChartType = Literal["LineChart", "DiscreteBar", "ScatterPlot", "StackedDiscreteBar"]
"""Type alias for supported chart types.

Chart types:
    - LineChart: Time series line chart
    - DiscreteBar: Bar chart (side-by-side bars)
    - StackedDiscreteBar: Stacked bar chart
    - ScatterPlot: Scatter plot with x/y numeric dimensions
"""


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class ChartConfig:
    """Configuration for OWID chart display and behavior.

    This dataclass holds all chart-level settings including title, subtitle,
    axis configuration, and UI control visibility. Properties use snake_case in Python
    but are automatically converted to camelCase for the JavaScript Grapher library.

    Note: Chart types are now managed by the Chart class via chart_types list,
    not in this config class.

    Attributes:
        title: Main chart title.
        subtitle: Additional context below title.
        note: Footnote text displayed at bottom.
        source_desc: Data source attribution.
        hide_logo: If True, hides OWID logo (default for embedded charts).
        is_published: Publication status flag.
        hide_title_annotation: If True, hides the annotation arrow on title.
        hide_legend: If True, hides the chart legend.
        hide_entity_controls: If True, hides the entity/country picker UI.
        hide_relative_toggle: If True, hides relative/absolute toggle button.
        has_map_tab: If True, enables the map visualization tab.
        stack_mode: For stacked charts, 'absolute' or 'relative' (percentage).
        matching_entities_only: If True, only show entities with complete data.
        x_axis: Dictionary of x-axis configuration (label, scale, etc).
        y_axis: Dictionary of y-axis configuration (label, scale, etc).
    """

    title: str = ""
    subtitle: str = ""
    note: str = ""
    source_desc: str = ""
    hide_logo: bool = True
    is_published: bool = True
    hide_title_annotation: bool = True
    hide_legend: bool = False
    hide_entity_controls: bool = True
    hide_relative_toggle: bool = True
    has_map_tab: bool = False
    map_config: Optional[MapConfig] = None
    stack_mode: Literal["relative", "absolute"] = "absolute"
    matching_entities_only: bool = False
    x_axis: dict = field(default_factory=dict)
    y_axis: dict = field(default_factory=dict)


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class VariableConfig:
    """Configuration for a data variable/column.

    Provides rich metadata for a column that appears in the chart's data table
    and tooltips. Maps to OWID's columnDefs format.

    Attributes:
        name: Display name for the variable (e.g., "Population").
        description_short: Brief description shown in tooltips.
        description_from_producer: Original description from data source.
        description_processing: How the data was processed/transformed.
        description_key: List of key points about the variable.
        unit: Full unit name (e.g., "million people").
        short_unit: Abbreviated unit (e.g., "M").
        source_name: Name of the data source.
        source_link: URL to the data source.
    """

    name: Optional[str] = None
    description_short: Optional[str] = None
    description_from_producer: Optional[str] = None
    description_processing: Optional[str] = None
    description_key: Optional[List[str]] = None
    unit: Optional[str] = None
    short_unit: Optional[str] = None
    source_name: Optional[str] = None
    source_link: Optional[str] = None


def generate_iframe(
    csv_data: str, column_defs: List[Dict[str, Any]], grapher_config: Dict[str, Any]
) -> str:
    """Generate an iframe HTML for rendering the chart.

    Args:
        csv_data: CSV string of the data
        column_defs: List of column definition dicts for OwidTable
        grapher_config: Dict of GrapherState configuration

    Returns:
        HTML string containing the iframe and initialization script
    """
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))

    # Hide sources section if no sourceDesc provided
    hide_sources_css = (
        ".sources { display: none !important; }"
        if not grapher_config.get("sourceDesc")
        else ""
    )

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
      .ActionButtons, .learn-more-about-data {{ display: none !important; }}
      {hide_sources_css}
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
      const columnDefs = {json.dumps(column_defs)};
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


def _timespan_from_date(timespan: Tuple[str, str]) -> Tuple[int, int]:
    from_date_d = parse(timespan[0]).date()
    to_date_d = parse(timespan[1]).date()

    offset = dt.date(1970, 1, 1).toordinal()

    return (from_date_d.toordinal() - offset, to_date_d.toordinal() - offset)
