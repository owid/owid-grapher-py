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
        full_config = self.export()
        html = generate_iframe(full_config)
        return html

    def _get_primary_chart_type(self) -> "ChartType":
        """Get the primary chart type (first in the list, or LineChart as default)."""
        if self.chart_types:
            return self.chart_types[0]  # type: ignore
        return "LineChart"

    def export(self, include_data: bool = True) -> Dict[str, Any]:
        """Export the chart configuration as a dictionary.

        Args:
            include_data: If True, includes the data in the export.

        Returns:
            Dictionary containing the full chart configuration.
        """
        config = self.config.to_dict()  # type: ignore

        # Add chart types and tab
        chart_types = self.chart_types if self.chart_types else ["LineChart"]
        config["chartTypes"] = chart_types

        # Set tab based on default_tab or first chart type
        if self.default_tab:
            config["tab"] = self.default_tab
        elif chart_types:
            config["tab"] = _CHART_TYPE_TO_TAB.get(chart_types[0], "line")

        # Auto-improve: show title annotation for line charts with titles
        if self.config.title and "LineChart" in chart_types:
            config["hideTitleAnnotation"] = False

        # Convert MapConfig to dict (dataclass_json doesn't handle it automatically)
        if self.config.map_config is not None:
            config["mapConfig"] = self.config.map_config.to_dict()

        primary_type = self._get_primary_chart_type()
        config.update(self.data_config().to_dict(primary_type))
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
            chart_type=self._get_primary_chart_type(),
            selection=self.selection,
            timespan=self.timespan,
            x_unit=self.x_unit,
            y_unit=self.y_unit,
            variable_configs=self.variable_configs,
        )


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


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore
@dataclass
class Dimension:
    """Maps a DataFrame column to a chart dimension.

    Dimensions define how data columns are used in the chart visualization. Each
    dimension specifies a visual property (x, y, color) and the source column name,
    along with optional display settings.

    Attributes:
        property: The visual property this dimension controls ('y' for y-axis, 'x' for x-axis,
            'color' for color encoding).
        variable_name: Name of the column from the DataFrame to use for this dimension.
        display: Optional dictionary of display settings (e.g., {'unit': '$', 'numDecimalPlaces': 2}).

    Example:
        ```python
        Dimension(
            property="y",
            variable_name="population",
            display={"unit": "people", "numDecimalPlaces": 0}
        )
        ```
    """

    property: Literal["y", "x", "color"]
    variable_name: str
    display: Optional[dict] = field(default_factory=dict)


@dataclass
class DataConfig:
    """Stores data and column mappings for chart rendering.

    Internal class that handles the conversion between pandas DataFrame structure and
    OWID Grapher's expected data format. This class manages column mappings, entity
    selection, time ranges, and chart-type-specific data transformations.

    Attributes:
        df: Source pandas DataFrame containing the data.
        x_col: Column name for x-axis (time for line charts, value for bar/scatter).
        y_cols: List of column names for y-axis values.
        entity_col: Column name for entity/grouping (e.g., 'country').
        year_col: Column name for year dimension (used in scatter plots with time).
        color_col: Column name for color encoding (scatter plots).
        size_col: Column name for size encoding (scatter plots).
        time_type: Whether time is yearly (YEAR) or daily (DAY).
        chart_type: Type of chart being created.
        selected_entity_names: List of entity names to display by default.
        min_time: Minimum time value for chart range (or 'latest' for scatter).
        max_time: Maximum time value for chart range.
        x_unit: Unit label for x-axis values (e.g., '$', 'kg').
        y_unit: Unit label for y-axis values.
        variable_configs: Rich metadata for columns (from Chart.variable()).
    """

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
    variable_configs: Dict[str, VariableConfig] = field(default_factory=dict)

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
        variable_configs: Optional[Dict[str, "VariableConfig"]] = None,
    ) -> "DataConfig":
        df = df.copy()

        # Sanitize column names (special characters break OWID's slug format)
        # Build rename map for columns that need sanitizing
        rename_map = {
            col: _sanitize_slug(col)
            for col in df.columns
            if _UNSAFE_SLUG_CHARS.search(col)
        }
        if rename_map:
            df = df.rename(columns=rename_map)
            # Update column references to use sanitized names
            if x in rename_map:
                x = rename_map[x]
            if y in rename_map:
                y = rename_map[y]
            if entity and entity in rename_map:
                entity = rename_map[entity]
            if color and color in rename_map:
                color = rename_map[color]
            if size and size in rename_map:
                size = rename_map[size]

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
            # For bar charts: if entity is explicitly provided, use it
            # Otherwise fall back to y as entity, x as value (horizontal bars)
            if entity:
                entity_col = entity
                y_cols = [y]
                if selection is None:
                    selection = list(df[entity].unique())
            else:
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
            variable_configs=variable_configs or {},
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

    def _get_time_column(self) -> Optional[str]:
        """Get the time column name based on chart type."""
        if self.chart_type == "ScatterPlot":
            return self.year_col  # May be None for scatter plots without time
        else:
            return self.x_col

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

            col_metadata: Dict[str, Any] = {
                "display": col_display if col_display else {}
            }

            # Add rich metadata from variable_configs if available
            if col in self.variable_configs:
                var_config = self.variable_configs[col]
                # Convert to dict and use camelCase keys for JS
                var_dict = var_config.to_dict()  # type: ignore
                col_metadata.update(var_dict)

                # Auto-compute timespan from the time column
                time_col = self._get_time_column()
                if time_col and time_col in self.df.columns:
                    min_val = self.df[time_col].min()
                    max_val = self.df[time_col].max()
                    if min_val == max_val:
                        col_metadata["timespan"] = str(min_val)
                    else:
                        col_metadata["timespan"] = f"{min_val}–{max_val}"

            metadata[col] = col_metadata

        # Rename entity column to entityName for OwidTable
        df = self.df.copy()
        if self.entity_col and self.entity_col in df.columns:
            df = df.rename(columns={self.entity_col: "entityName"})

        # Rename x column to expected time column name for OwidTable
        # (OwidTable expects 'year' or 'date', not arbitrary column names)
        if chart_type not in ("ScatterPlot", "DiscreteBar", "StackedDiscreteBar"):
            expected_time_col = "date" if self.time_type == TimeType.DAY else "year"
            if self.x_col != expected_time_col and self.x_col in df.columns:
                df = df.rename(columns={self.x_col: expected_time_col})

        doc: Dict[str, Any] = {
            "selectedEntityNames": self.selected_entity_names,
            "owidDataset": {
                "data": df.to_dict(orient="list"),
                "metadata": metadata,
            },
            "dimensions": [d.to_dict() for d in self._get_dimensions()],  # type: ignore
            # Note: chartTypes is set by Chart.export(), not here
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
        col_def: Dict[str, Any] = {"slug": col_name, "type": "Numeric"}

        # Extract display settings if present
        display = col_metadata.get("display", {})
        if display:
            col_def["display"] = display

        # Extract rich metadata fields from VariableConfig
        for field_name in [
            "name",
            "descriptionShort",
            "descriptionFromProducer",
            "descriptionProcessing",
            "descriptionKey",
            "unit",
            "shortUnit",
            "sourceName",
            "sourceLink",
            "timespan",
        ]:
            if field_name in col_metadata and col_metadata[field_name] is not None:
                col_def[field_name] = col_metadata[field_name]

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

    # Pass through hide toggles and boolean flags
    for field_name in [
        "hideRelativeToggle",
        "hideEntityControls",
        "matchingEntitiesOnly",
    ]:
        if field_name in config:
            grapher_config[field_name] = config[field_name]

    # Handle map config - auto-set columnSlug from y dimension
    map_config_raw = config.get("mapConfig")
    if map_config_raw is not None:
        # MapConfig object - use to_dict()
        if isinstance(map_config_raw, MapConfig):
            map_config = map_config_raw.to_dict()
        else:
            map_config = map_config_raw.copy()

        # Auto-set columnSlug from the first y dimension if not specified
        if "columnSlug" not in map_config:
            y_slugs = [
                dim.get("variableName")
                for dim in dimensions
                if dim.get("property") == "y" and dim.get("variableName")
            ]
            if y_slugs:
                map_config["columnSlug"] = y_slugs[0]
        grapher_config["map"] = map_config

    return grapher_config


def generate_iframe(config: Dict[str, Any]) -> str:
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))

    # Extract data for CSV and prepare config for GrapherState API
    csv_data = _config_to_csv(config)

    # Build column definitions from metadata
    column_defs = _build_column_defs(config)

    # Build grapher config from the config dict
    grapher_config = _config_to_grapher(config)

    # Hide sources section if no sourceDesc provided
    hide_sources_css = (
        ".sources { display: none !important; }" if not config.get("sourceDesc") else ""
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
