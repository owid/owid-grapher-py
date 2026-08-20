# -*- coding: utf-8 -*-
#
#  config.py
#  owid-grapher-py
#
#  GENERATED FILE -- do not edit by hand.
#  Regenerate with: .venv/bin/python scripts/generate_config_types.py
#  Source: https://files.ourworldindata.org/schemas/grapher-schema.011.json
#
#  Typed keys for Grapher's chart config and column metadata. Pass them to
#  Chart(df, config=..., columns=...) -- every key goes to the JS library
#  unchanged, so these names are Grapher's own, not this package's.
#

from typing import Any, Dict, List, Literal, TypedDict, Union

SCHEMA_URL = "https://files.ourworldindata.org/schemas/grapher-schema.011.json"
SCHEMA_VERSION = "011"


class GrapherConfig(TypedDict, total=False):
    """A Grapher chart config.
    Generated from Grapher's published JSON schema, so the keys, their
    types and their descriptions are Grapher's own. Every field is
    optional.
    """

    # Whether the user can change countries, add additional ones or neither
    addCountryMode: Literal["add-country", "change-country", "disabled"]
    baseColorScheme: Any
    # Which chart types should be shown
    chartTypes: List[
        Literal[
            "LineChart",
            "ScatterPlot",
            "StackedArea",
            "DiscreteBar",
            "StackedDiscreteBar",
            "SlopeChart",
            "StackedBar",
            "Marimekko",
            "Dumbbell",
        ]
    ]
    colorScale: Any
    # Drops in between points in scatter plots
    compareEndPointsOnly: bool
    # List of comparison lines to draw
    comparisonLines: List[Any]
    # Configuration of the dumbbell chart
    dumbbell: Dict[str, Any]
    # Display string for naming the primary entities of the data. The default is 'country or region',
    entityType: str
    # Plural of the entity type (i.e. when entityType is 'country' this would be 'countries')
    entityTypePlural: str
    # Entities that should be excluded (opposite of includedEntityNames)
    excludedEntityNames: List[str]
    # Display string that replaces 'metric' in the 'Split by metric' label in facet controls (e.g. 'pr
    facettingLabelByYVariables: str
    # The initially focused chart elements. Is either a list of entity or variable names.
    focusedSeriesNames: List[Union[str]]
    # Indicates if the map tab should be shown
    hasMapTab: bool
    # Whether to hide any automatically added title annotations like the selected year
    hideAnnotationFieldsInTitle: Dict[str, Any]
    # Whether to hide connecting lines on scatter plots when a time range is selected
    hideConnectedScatterLines: bool
    # Whether to hide the faceting control
    hideFacetControl: bool
    # Whether to hide the logo
    hideLogo: bool
    # Whether to hide the relative mode UI toggle
    hideRelativeToggle: bool
    # Hide entity names in Scatter plots
    hideScatterLabels: bool
    # Whether to hide the inline series labels drawn at the end
    hideSeriesLabels: bool
    # Whether to hide the timeline from the user. If it is hidden then the user can't change the time
    hideTimeline: bool
    # Whether to hide the total value label (used on stacked discrete bar charts)
    hideTotalValueLabel: bool
    # Internal database id
    id: int
    # Entities that should be included (opposite of excludedEntityNames).
    includedEntityNames: List[str]
    # Additional text used internally to differentiate charts with the same title
    internalNotes: str
    # Reverse the order of colors in the color scheme
    invertColorScheme: bool
    # Indicates if the chart is published on Our World In Data or still in draft
    isPublished: bool
    # The license the chart is published under, linked in the chart footer
    license: Literal[
        "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"
    ]
    # Which logo to show on the upper right side
    logo: Literal["owid", "core+owid", "gv+owid"]
    # Configuration of the world map chart
    map: Dict[str, Any]
    # Exclude entities that do not belong in any color group
    matchingEntitiesOnly: bool
    # End point of the initially selected time span.
    maxTime: Any
    # Start point of the initially selected time span.
    minTime: Any
    # The desired strategy for handling entities with missing data
    missingDataStrategy: Literal["auto", "hide", "show"]
    # Note displayed in the footer of the chart
    note: str
    # The page containing this chart where more context can be found
    originUrl: str
    # Strategy for selecting peer countries for comparison
    peerCountryStrategy: Literal[
        "defaultSelection",
        "parentRegions",
        "gdpPerCapita",
        "population",
        "dataRange",
        "neighbors",
        "none",
    ]
    # Links to related questions
    relatedQuestions: List[Dict[str, Any]]
    # When a user hovers over a connected series line in a ScatterPlot we show
    scatterPointLabelStrategy: Literal["x", "y", "year"]
    # Colors for selected entities
    selectedEntityColors: Dict[str, Any]
    # The initial selection of entities
    selectedEntityNames: List[Union[str]]
    # The desired facetting strategy (none for no facetting)
    selectedFacetStrategy: Literal["none", "entity", "metric"]
    # Whether to show an area for entities that have no data (used in marimekko charts)
    showNoDataArea: bool
    # Whether to show year labels in bar charts
    showYearLabels: bool
    # Slug of the chart on Our World In Data
    slug: str
    # Sort criterion (used by discrete bar, stacked discrete bar, marimekko, and dumbbell charts).
    sortBy: Literal[
        "column", "total", "entityName", "custom", "change", "startValue", "endValue"
    ]
    # Sort column if sortBy is column
    sortColumnSlug: str
    # Sort order
    sortOrder: Literal["desc", "asc"]
    # Short comma-separated list of source names
    sourceDesc: str
    # Stack mode. Only absolute and relative are actively used.
    stackMode: Literal["absolute", "relative"]
    # The longer subtitle text to show beneath the title
    subtitle: str
    # The tab that is shown initially
    tab: Literal[
        "chart",
        "map",
        "table",
        "line",
        "slope",
        "discrete-bar",
        "marimekko",
        "scatter",
        "stacked-area",
        "stacked-bar",
        "stacked-discrete-bar",
        "dumbbell",
    ]
    # The highest year to show in the timeline. If this is set then the user is not able to see
    timelineMaxTime: Any
    # The lowest year to show in the timeline. If this is set then the user is not able to see
    timelineMinTime: Any
    # Big title text of the chart
    title: str
    # Optional internal variant name for distinguishing charts with the same title
    variantName: str
    # Chart config version
    version: int
    xAxis: Any
    yAxis: Any
    # Whether to zoom to the selected data points
    zoomToSelection: bool

    # -- CSV-mode keys ----------------------------------------------------
    # Not in the published schema, which only covers indicator-backed charts.
    # Which columns of the DataFrame to plot, as space-separated slugs.
    ySlugs: str
    # The column to use as the x axis of a scatter plot.
    xSlug: str
    # The column that colours points in a scatter plot.
    colorSlug: str
    # The column that sizes points in a scatter plot.
    sizeSlug: str
    # Extra columns to show in the data table.
    tableSlugs: str
    # Whether to hide the chart legend.
    hideLegend: bool


class ColumnDef(TypedDict, total=False):
    """Metadata for one column, as Grapher's OwidColumnDef.

    Unlike GrapherConfig this is written by hand: column metadata has no
    published schema. The full list of fields lives in the package's
    `grapher.d.ts`; these are the ones its readme documents. Any other field
    the library accepts can still be passed -- nothing is dropped at runtime.
    """

    # How the column is named in the chart and its legend.
    name: str
    # "Numeric", "Currency", "Percentage", "Integer", "Ratio", "String", ...
    type: str
    # Full unit, shown in tooltips ("million people").
    unit: str
    # Short unit, shown on axis ticks ("$", "%", " years").
    shortUnit: str
    # Colour for this series, as a hex string.
    color: str
    # Display overrides: numDecimalPlaces, conversionFactor, tolerance, ...
    display: Dict[str, Any]
    # One-line description, shown under the indicator title.
    descriptionShort: str
    # "What you should know about this data", as a markdown string.
    descriptionKey: str
    descriptionFromProducer: str
    additionalInfo: str
    # Source information, shown in the chart footer and the sources modal.
    sourceName: str
    sourceLink: str
    dataPublishedBy: str
    # Shown as "Date range" in the sources modal.
    timespan: str
    # Citation and attribution, one entry per upstream source.
    origins: List[Dict[str, Any]]
    # titlePublic, attributionShort, ...
    presentation: Dict[str, Any]


#: Every key `config` accepts. Used to reject typos at runtime, where a type
#: checker isn't watching (a notebook, mostly).
CONFIG_KEYS = frozenset(GrapherConfig.__annotations__)
