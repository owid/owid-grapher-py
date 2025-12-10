"""
Python typed dataclass representation of GrapherState from OWID Grapher.

This module provides a typed Python interface for configuring Grapher charts,
focusing on the most commonly used properties for chart configuration.

Generated from: packages/@ourworldindata/grapher/src/core/GrapherState.tsx
Types from: packages/@ourworldindata/types/src/grapherTypes/GrapherTypes.ts
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

# =============================================================================
# Literal Types (provide autocomplete with simple strings)
# =============================================================================

GrapherChartType = Literal[
    "LineChart",
    "ScatterPlot",
    "StackedArea",
    "DiscreteBar",
    "StackedDiscreteBar",
    "SlopeChart",
    "StackedBar",
    "Marimekko",
]

GrapherTabName = Literal[
    "Table",
    "WorldMap",
    "LineChart",
    "ScatterPlot",
    "StackedArea",
    "DiscreteBar",
    "StackedDiscreteBar",
    "SlopeChart",
    "StackedBar",
    "Marimekko",
]

GrapherTabConfigOption = Literal[
    "table",
    "map",
    "chart",
    "line",
    "scatter",
    "stacked-area",
    "discrete-bar",
    "stacked-discrete-bar",
    "slope",
    "stacked-bar",
    "marimekko",
]

StackMode = Literal["absolute", "relative"]

EntitySelectionMode = Literal["add-country", "change-country", "disabled"]

FacetStrategy = Literal["none", "entity", "metric"]

FacetAxisDomain = Literal["independent", "shared"]

ScaleType = Literal["linear", "log"]

SortBy = Literal["custom", "entityName", "column", "total"]

SortOrder = Literal["asc", "desc"]

LogoOption = Literal["owid", "core+owid", "gv+owid"]

ScatterPointLabelStrategy = Literal["year", "x", "y"]

MissingDataStrategy = Literal["auto", "hide", "show"]

MapRegionName = Literal[
    "World",
    "Africa",
    "NorthAmerica",
    "SouthAmerica",
    "Asia",
    "Europe",
    "Oceania",
]

ToleranceStrategy = Literal["closest", "backwards", "forwards"]


# Literal type for color schemes - provides autocomplete with simple strings
ColorSchemeName = Literal[
    # Brewer schemes
    "YlGn",
    "YlGnBu",
    "GnBu",
    "BuGn",
    "PuBuGn",
    "BuPu",
    "RdPu",
    "PuRd",
    "OrRd",
    "YlOrRd",
    "YlOrBr",
    "Purples",
    "Blues",
    "Greens",
    "Oranges",
    "Reds",
    "Greys",
    "PuOr",
    "BrBG",
    "PRGn",
    "PiYG",
    "RdBu",
    "RdGy",
    "RdYlBu",
    "Spectral",
    "RdYlGn",
    "Accent",
    "Dark2",
    "Paired",
    "Pastel1",
    "Pastel2",
    "Set1",
    "Set2",
    "Set3",
    "PuBu",
    # Custom schemes
    "Magma",
    "Inferno",
    "Plasma",
    "Viridis",
    "continents",
    "stackedAreaDefault",
    "owid-distinct",
    "SingleColorDenim",
    "SingleColorTeal",
    "SingleColorPurple",
    "SingleColorDustyCoral",
    "SingleColorDarkCopper",
    "OwidCategoricalA",
    "OwidCategoricalB",
    "OwidCategoricalC",
    "OwidCategoricalD",
    "OwidCategoricalE",
    "OwidEnergy",
    "OwidEnergyLines",
    "OwidDistinctLines",
    "BinaryMapPaletteA",
    "BinaryMapPaletteB",
    "BinaryMapPaletteC",
    "BinaryMapPaletteD",
    "BinaryMapPaletteE",
]

# Literal type for binning strategies
BinningStrategy = Literal["auto", "equalInterval", "quantiles", "manual"]


# =============================================================================
# Type Aliases
# =============================================================================

Time = int  # A concrete point in time (year or date)
TimeBound = Union[int, float]  # Can be ±Infinity or a concrete time
EntityName = str
SeriesName = str
ColumnSlug = str  # URL-friendly name for a column
ColumnSlugs = str  # Space-separated column slugs
Color = str


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class AnnotationFieldsInTitle:
    """Configuration for which annotation fields to show in the title."""

    entity: Optional[bool] = None
    time: Optional[bool] = None
    changeInPrefix: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.entity is not None:
            result["entity"] = self.entity
        if self.time is not None:
            result["time"] = self.time
        if self.changeInPrefix is not None:
            result["changeInPrefix"] = self.changeInPrefix
        return result


@dataclass
class AxisConfig:
    """Configuration for an axis (x or y)."""

    scaleType: Optional[ScaleType] = None
    label: Optional[str] = None
    min: Optional[Union[float, Literal["auto"]]] = None
    max: Optional[Union[float, Literal["auto"]]] = None
    canChangeScaleType: Optional[bool] = None
    removePointsOutsideDomain: Optional[bool] = None
    hideAxis: Optional[bool] = None
    hideTickLabels: Optional[bool] = None
    hideGridlines: Optional[bool] = None
    facetDomain: Optional[FacetAxisDomain] = None
    nice: Optional[bool] = None
    maxTicks: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.scaleType is not None:
            result["scaleType"] = self.scaleType
        if self.label is not None:
            result["label"] = self.label
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.canChangeScaleType is not None:
            result["canChangeScaleType"] = self.canChangeScaleType
        if self.removePointsOutsideDomain is not None:
            result["removePointsOutsideDomain"] = self.removePointsOutsideDomain
        if self.hideAxis is not None:
            result["hideAxis"] = self.hideAxis
        if self.hideTickLabels is not None:
            result["hideTickLabels"] = self.hideTickLabels
        if self.hideGridlines is not None:
            result["hideGridlines"] = self.hideGridlines
        if self.facetDomain is not None:
            result["facetDomain"] = self.facetDomain
        if self.nice is not None:
            result["nice"] = self.nice
        if self.maxTicks is not None:
            result["maxTicks"] = self.maxTicks
        return result


@dataclass
class ColorScaleConfig:
    """Configuration for color scales."""

    baseColorScheme: Optional[ColorSchemeName] = None
    colorSchemeInvert: Optional[bool] = None
    binningStrategy: Optional[BinningStrategy] = None
    minValue: Optional[float] = None
    maxValue: Optional[float] = None
    customNumericValues: Optional[List[float]] = None
    customNumericLabels: Optional[List[Optional[str]]] = None
    customNumericColors: Optional[List[Optional[Color]]] = None
    customCategoryColors: Optional[Dict[str, Optional[str]]] = None
    customCategoryLabels: Optional[Dict[str, Optional[str]]] = None
    legendDescription: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.baseColorScheme is not None:
            result["baseColorScheme"] = self.baseColorScheme
        if self.colorSchemeInvert is not None:
            result["colorSchemeInvert"] = self.colorSchemeInvert
        if self.binningStrategy is not None:
            result["binningStrategy"] = self.binningStrategy
        if self.minValue is not None:
            result["minValue"] = self.minValue
        if self.maxValue is not None:
            result["maxValue"] = self.maxValue
        if self.customNumericValues is not None:
            result["customNumericValues"] = self.customNumericValues
        if self.customNumericLabels is not None:
            result["customNumericLabels"] = self.customNumericLabels
        if self.customNumericColors is not None:
            result["customNumericColors"] = self.customNumericColors
        if self.customCategoryColors is not None:
            result["customCategoryColors"] = self.customCategoryColors
        if self.customCategoryLabels is not None:
            result["customCategoryLabels"] = self.customCategoryLabels
        if self.legendDescription is not None:
            result["legendDescription"] = self.legendDescription
        return result


@dataclass
class GlobeConfig:
    """Configuration for the globe view."""

    isActive: bool = False
    rotation: tuple[float, float] = (0, 0)
    zoom: float = 1.0
    focusCountry: Optional[EntityName] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "isActive": self.isActive,
            "rotation": list(self.rotation),
            "zoom": self.zoom,
        }
        if self.focusCountry is not None:
            result["focusCountry"] = self.focusCountry
        return result


@dataclass
class MapConfig:
    """Configuration for the map tab."""

    columnSlug: Optional[ColumnSlug] = None
    time: Optional[TimeBound] = None
    timeTolerance: Optional[int] = None
    toleranceStrategy: Optional[ToleranceStrategy] = None
    hideTimeline: Optional[bool] = None
    region: Optional[MapRegionName] = None
    globe: Optional[GlobeConfig] = None
    colorScale: Optional[ColorScaleConfig] = None
    tooltipUseCustomLabels: Optional[bool] = None
    selectedEntityNames: Optional[List[EntityName]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.columnSlug is not None:
            result["columnSlug"] = self.columnSlug
        if self.time is not None:
            result["time"] = self.time
        if self.timeTolerance is not None:
            result["timeTolerance"] = self.timeTolerance
        if self.toleranceStrategy is not None:
            result["toleranceStrategy"] = self.toleranceStrategy
        if self.hideTimeline is not None:
            result["hideTimeline"] = self.hideTimeline
        if self.region is not None:
            result["region"] = self.region
        if self.globe is not None:
            result["globe"] = self.globe.to_dict()
        if self.colorScale is not None:
            result["colorScale"] = self.colorScale.to_dict()
        if self.tooltipUseCustomLabels is not None:
            result["tooltipUseCustomLabels"] = self.tooltipUseCustomLabels
        if self.selectedEntityNames is not None:
            result["selectedEntityNames"] = self.selectedEntityNames
        return result


@dataclass
class RelatedQuestion:
    """Configuration for a related question link."""

    text: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "url": self.url}


@dataclass
class ComparisonLine:
    """Configuration for a comparison line (vertical or custom equation)."""

    xEquals: Optional[float] = None
    yEquals: Optional[str] = None  # Equation like "2*x^2" or "sqrt(x)"
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.xEquals is not None:
            result["xEquals"] = self.xEquals
        if self.yEquals is not None:
            result["yEquals"] = self.yEquals
        if self.label is not None:
            result["label"] = self.label
        return result


@dataclass
class GrapherState:
    """
    Typed Python representation of Grapher chart configuration.

    This class represents the persistent state of a Grapher chart.
    When a chart is saved and loaded again under the same rendering
    conditions, it should remain visually identical.
    """

    # =========================================================================
    # Chart Type and Display
    # =========================================================================

    chartTypes: List[GrapherChartType] = field(default_factory=lambda: ["LineChart"])
    tab: GrapherTabConfigOption = "chart"
    hasMapTab: bool = False

    # =========================================================================
    # Title and Text
    # =========================================================================

    title: Optional[str] = None
    subtitle: Optional[str] = None
    sourceDesc: Optional[str] = None
    note: Optional[str] = None
    variantName: Optional[str] = None
    hideAnnotationFieldsInTitle: Optional[AnnotationFieldsInTitle] = None

    # =========================================================================
    # Time Configuration
    # =========================================================================

    minTime: Optional[TimeBound] = None
    maxTime: Optional[TimeBound] = None
    timelineMinTime: Optional[Time] = None
    timelineMaxTime: Optional[Time] = None
    hideTimeline: Optional[bool] = None

    # =========================================================================
    # Entity/Selection Configuration
    # =========================================================================

    selectedEntityNames: List[EntityName] = field(default_factory=list)
    focusedSeriesNames: List[SeriesName] = field(default_factory=list)
    excludedEntityNames: Optional[List[EntityName]] = None
    includedEntityNames: Optional[List[EntityName]] = None
    addCountryMode: EntitySelectionMode = "add-country"
    entityType: str = "country"
    entityTypePlural: str = "countries"
    matchingEntitiesOnly: Optional[bool] = None
    selectedEntityColors: Dict[str, Optional[str]] = field(default_factory=dict)

    # =========================================================================
    # Data Column Configuration
    # =========================================================================

    ySlugs: Optional[ColumnSlugs] = None
    xSlug: Optional[ColumnSlug] = None
    colorSlug: Optional[ColumnSlug] = None
    sizeSlug: Optional[ColumnSlug] = None
    tableSlugs: Optional[ColumnSlugs] = None

    # =========================================================================
    # Axis Configuration
    # =========================================================================

    xAxis: Optional[AxisConfig] = None
    yAxis: Optional[AxisConfig] = None

    # =========================================================================
    # Visual Configuration
    # =========================================================================

    stackMode: StackMode = "absolute"
    baseColorScheme: Optional[ColorSchemeName] = None
    invertColorScheme: Optional[bool] = None
    colorScale: Optional[ColorScaleConfig] = None
    hideLegend: Optional[bool] = False
    logo: Optional[LogoOption] = None
    hideLogo: Optional[bool] = None
    hideRelativeToggle: Optional[bool] = True
    showNoDataArea: bool = True
    zoomToSelection: Optional[bool] = None
    showYearLabels: Optional[bool] = None
    hideTotalValueLabel: Optional[bool] = None

    # =========================================================================
    # Scatter Plot Specific
    # =========================================================================

    hideConnectedScatterLines: Optional[bool] = None
    hideScatterLabels: Optional[bool] = None
    scatterPointLabelStrategy: Optional[ScatterPointLabelStrategy] = None
    compareEndPointsOnly: Optional[bool] = None

    # =========================================================================
    # Faceting Configuration
    # =========================================================================

    selectedFacetStrategy: Optional[FacetStrategy] = None
    hideFacetControl: bool = True
    facettingLabelByYVariables: str = "metric"

    # =========================================================================
    # Sorting Configuration
    # =========================================================================

    sortBy: Optional[SortBy] = "total"
    sortOrder: Optional[SortOrder] = "desc"
    sortColumnSlug: Optional[str] = None

    # =========================================================================
    # Map Configuration
    # =========================================================================

    map: Optional[MapConfig] = None

    # =========================================================================
    # Missing Data
    # =========================================================================

    missingDataStrategy: Optional[MissingDataStrategy] = None

    # =========================================================================
    # Comparison Lines & Related Questions
    # =========================================================================

    comparisonLines: Optional[List[ComparisonLine]] = None
    relatedQuestions: Optional[List[RelatedQuestion]] = None

    # =========================================================================
    # Metadata
    # =========================================================================

    id: Optional[int] = None
    slug: Optional[str] = None
    version: int = 1
    isPublished: Optional[bool] = None
    originUrl: Optional[str] = None
    internalNotes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        result: Dict[str, Any] = {}

        # Chart type and display
        if self.chartTypes:
            result["chartTypes"] = list(self.chartTypes)
        if self.tab != "chart":
            result["tab"] = self.tab
        if self.hasMapTab:
            result["hasMapTab"] = self.hasMapTab

        # Title and text
        if self.title is not None:
            result["title"] = self.title
        if self.subtitle is not None:
            result["subtitle"] = self.subtitle
        if self.sourceDesc is not None:
            result["sourceDesc"] = self.sourceDesc
        if self.note is not None:
            result["note"] = self.note
        if self.variantName is not None:
            result["variantName"] = self.variantName
        if self.hideAnnotationFieldsInTitle is not None:
            result["hideAnnotationFieldsInTitle"] = (
                self.hideAnnotationFieldsInTitle.to_dict()
            )

        # Time configuration
        if self.minTime is not None:
            result["minTime"] = self.minTime
        if self.maxTime is not None:
            result["maxTime"] = self.maxTime
        if self.timelineMinTime is not None:
            result["timelineMinTime"] = self.timelineMinTime
        if self.timelineMaxTime is not None:
            result["timelineMaxTime"] = self.timelineMaxTime
        if self.hideTimeline is not None:
            result["hideTimeline"] = self.hideTimeline

        # Entity/selection configuration (always include, even if empty)
        result["selectedEntityNames"] = self.selectedEntityNames
        if self.focusedSeriesNames:
            result["focusedSeriesNames"] = self.focusedSeriesNames
        if self.excludedEntityNames is not None:
            result["excludedEntityNames"] = self.excludedEntityNames
        if self.includedEntityNames is not None:
            result["includedEntityNames"] = self.includedEntityNames
        if self.addCountryMode != "add-country":
            result["addCountryMode"] = self.addCountryMode
        if self.entityType != "country":
            result["entityType"] = self.entityType
        if self.entityTypePlural != "countries":
            result["entityTypePlural"] = self.entityTypePlural
        if self.matchingEntitiesOnly is not None:
            result["matchingEntitiesOnly"] = self.matchingEntitiesOnly
        if self.selectedEntityColors:
            result["selectedEntityColors"] = self.selectedEntityColors

        # Data column configuration
        if self.ySlugs is not None:
            result["ySlugs"] = self.ySlugs
        if self.xSlug is not None:
            result["xSlug"] = self.xSlug
        if self.colorSlug is not None:
            result["colorSlug"] = self.colorSlug
        if self.sizeSlug is not None:
            result["sizeSlug"] = self.sizeSlug
        if self.tableSlugs is not None:
            result["tableSlugs"] = self.tableSlugs

        # Axis configuration
        if self.xAxis is not None:
            result["xAxis"] = self.xAxis.to_dict()
        if self.yAxis is not None:
            result["yAxis"] = self.yAxis.to_dict()

        # Visual configuration
        if self.stackMode != "absolute":
            result["stackMode"] = self.stackMode
        if self.baseColorScheme is not None:
            result["baseColorScheme"] = self.baseColorScheme
        if self.invertColorScheme is not None:
            result["invertColorScheme"] = self.invertColorScheme
        if self.colorScale is not None:
            result["colorScale"] = self.colorScale.to_dict()
        if self.hideLegend not in (None, False):
            result["hideLegend"] = self.hideLegend
        if self.logo is not None:
            result["logo"] = self.logo
        if self.hideLogo is not None:
            result["hideLogo"] = self.hideLogo
        if self.hideRelativeToggle not in (None, True):
            result["hideRelativeToggle"] = self.hideRelativeToggle
        if not self.showNoDataArea:
            result["showNoDataArea"] = self.showNoDataArea
        if self.zoomToSelection is not None:
            result["zoomToSelection"] = self.zoomToSelection
        if self.showYearLabels is not None:
            result["showYearLabels"] = self.showYearLabels
        if self.hideTotalValueLabel is not None:
            result["hideTotalValueLabel"] = self.hideTotalValueLabel

        # Scatter plot specific
        if self.hideConnectedScatterLines is not None:
            result["hideConnectedScatterLines"] = self.hideConnectedScatterLines
        if self.hideScatterLabels is not None:
            result["hideScatterLabels"] = self.hideScatterLabels
        if self.scatterPointLabelStrategy is not None:
            result["scatterPointLabelStrategy"] = self.scatterPointLabelStrategy
        if self.compareEndPointsOnly is not None:
            result["compareEndPointsOnly"] = self.compareEndPointsOnly

        # Faceting configuration
        if self.selectedFacetStrategy is not None:
            result["selectedFacetStrategy"] = self.selectedFacetStrategy
        if not self.hideFacetControl:
            result["hideFacetControl"] = self.hideFacetControl
        if self.facettingLabelByYVariables != "metric":
            result["facettingLabelByYVariables"] = self.facettingLabelByYVariables

        # Sorting configuration
        if self.sortBy not in (None, "total"):
            result["sortBy"] = self.sortBy
        if self.sortOrder not in (None, "desc"):
            result["sortOrder"] = self.sortOrder
        if self.sortColumnSlug is not None:
            result["sortColumnSlug"] = self.sortColumnSlug

        # Map configuration
        if self.map is not None:
            result["map"] = self.map.to_dict()

        # Missing data
        if self.missingDataStrategy is not None:
            result["missingDataStrategy"] = self.missingDataStrategy

        # Comparison lines
        if self.comparisonLines is not None:
            result["comparisonLines"] = [cl.to_dict() for cl in self.comparisonLines]

        # Related questions
        if self.relatedQuestions is not None:
            result["relatedQuestions"] = [rq.to_dict() for rq in self.relatedQuestions]

        # Metadata
        if self.id is not None:
            result["id"] = self.id
        if self.slug is not None:
            result["slug"] = self.slug
        if self.version != 1:
            result["version"] = self.version
        if self.isPublished is not None:
            result["isPublished"] = self.isPublished
        if self.originUrl is not None:
            result["originUrl"] = self.originUrl
        if self.internalNotes is not None:
            result["internalNotes"] = self.internalNotes

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrapherState":
        """Create a GrapherState from a dictionary (e.g., parsed JSON)."""
        # Parse axis configs
        xAxis = None
        if "xAxis" in data:
            xAxis = AxisConfig(
                scaleType=data["xAxis"].get("scaleType"),
                label=data["xAxis"].get("label"),
                min=data["xAxis"].get("min"),
                max=data["xAxis"].get("max"),
                canChangeScaleType=data["xAxis"].get("canChangeScaleType"),
                hideAxis=data["xAxis"].get("hideAxis"),
                hideGridlines=data["xAxis"].get("hideGridlines"),
            )

        yAxis = None
        if "yAxis" in data:
            yAxis = AxisConfig(
                scaleType=data["yAxis"].get("scaleType"),
                label=data["yAxis"].get("label"),
                min=data["yAxis"].get("min"),
                max=data["yAxis"].get("max"),
                canChangeScaleType=data["yAxis"].get("canChangeScaleType"),
                hideAxis=data["yAxis"].get("hideAxis"),
                hideGridlines=data["yAxis"].get("hideGridlines"),
            )

        # Parse map config
        mapConfig = None
        if "map" in data:
            mapData = data["map"]
            colorScale = None
            if "colorScale" in mapData:
                cs = mapData["colorScale"]
                colorScale = ColorScaleConfig(
                    baseColorScheme=cs.get("baseColorScheme"),
                    binningStrategy=cs.get("binningStrategy"),
                    customNumericValues=cs.get("customNumericValues"),
                )
            mapConfig = MapConfig(
                columnSlug=mapData.get("columnSlug"),
                time=mapData.get("time"),
                timeTolerance=mapData.get("timeTolerance"),
                region=mapData.get("region"),
                colorScale=colorScale,
            )

        return cls(
            chartTypes=data.get("chartTypes", ["LineChart"]),
            tab=data.get("tab", "chart"),
            hasMapTab=data.get("hasMapTab", False),
            title=data.get("title"),
            subtitle=data.get("subtitle"),
            sourceDesc=data.get("sourceDesc"),
            note=data.get("note"),
            variantName=data.get("variantName"),
            minTime=data.get("minTime"),
            maxTime=data.get("maxTime"),
            timelineMinTime=data.get("timelineMinTime"),
            timelineMaxTime=data.get("timelineMaxTime"),
            hideTimeline=data.get("hideTimeline"),
            selectedEntityNames=data.get("selectedEntityNames", []),
            focusedSeriesNames=data.get("focusedSeriesNames", []),
            excludedEntityNames=data.get("excludedEntityNames"),
            includedEntityNames=data.get("includedEntityNames"),
            addCountryMode=data.get("addCountryMode", "add-country"),
            entityType=data.get("entityType", "country"),
            entityTypePlural=data.get("entityTypePlural", "countries"),
            matchingEntitiesOnly=data.get("matchingEntitiesOnly"),
            selectedEntityColors=data.get("selectedEntityColors", {}),
            ySlugs=data.get("ySlugs"),
            xSlug=data.get("xSlug"),
            colorSlug=data.get("colorSlug"),
            sizeSlug=data.get("sizeSlug"),
            tableSlugs=data.get("tableSlugs"),
            xAxis=xAxis,
            yAxis=yAxis,
            stackMode=data.get("stackMode", "absolute"),
            baseColorScheme=data.get("baseColorScheme"),
            invertColorScheme=data.get("invertColorScheme"),
            hideLegend=data.get("hideLegend", False),
            logo=data.get("logo"),
            hideLogo=data.get("hideLogo"),
            hideRelativeToggle=data.get("hideRelativeToggle", True),
            showNoDataArea=data.get("showNoDataArea", True),
            zoomToSelection=data.get("zoomToSelection"),
            showYearLabels=data.get("showYearLabels"),
            hideTotalValueLabel=data.get("hideTotalValueLabel"),
            hideConnectedScatterLines=data.get("hideConnectedScatterLines"),
            hideScatterLabels=data.get("hideScatterLabels"),
            scatterPointLabelStrategy=data.get("scatterPointLabelStrategy"),
            compareEndPointsOnly=data.get("compareEndPointsOnly"),
            selectedFacetStrategy=data.get("selectedFacetStrategy"),
            hideFacetControl=data.get("hideFacetControl", True),
            sortBy=data.get("sortBy", "total"),
            sortOrder=data.get("sortOrder", "desc"),
            sortColumnSlug=data.get("sortColumnSlug"),
            map=mapConfig,
            missingDataStrategy=data.get("missingDataStrategy"),
            id=data.get("id"),
            slug=data.get("slug"),
            version=data.get("version", 1),
            isPublished=data.get("isPublished"),
            originUrl=data.get("originUrl"),
            internalNotes=data.get("internalNotes"),
        )
