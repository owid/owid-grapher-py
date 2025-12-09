# -*- coding: utf-8 -*-
#
#  test_grapher.py
#  notebooks
#

import json

import pandas as pd

import owid.grapher as gr


def test_prune_empty():
    data = {}
    assert gr.prune(data) == data


def test_prune_single_layer():
    data = {"x": None, "y": 34}
    assert gr.prune(data) == {"y": 34}


def test_prune_recursive():
    data = {"x": None, "y": {"z": None, "f": 234, "g": {"k": None, "j": 123}}}
    expected = {"y": {"f": 234, "g": {"j": 123}}}
    assert gr.prune(data) == expected


def test_json_export():
    df = pd.DataFrame({"year": [2000, 2010, 2020], "population": [1234, 52342, 80123]})
    ch = (
        gr.Chart(df)
        .mark_line()
        .encode(x="year", y="population")
        .label("Too many Koalas?")
    )
    export = ch.export()
    assert export["title"] == "Too many Koalas?"
    assert export["chartTypes"] == ["LineChart"]
    assert export["selectedEntityNames"] == ["population"]

    # Check owidDataset structure - data is just the dataframe as dict
    data = export["owidDataset"]["data"]
    assert data["year"] == [2000, 2010, 2020]
    assert data["population"] == [1234, 52342, 80123]

    # Check metadata
    assert "population" in export["owidDataset"]["metadata"]


def test_custom_time_column_name():
    """Test that custom time column names are renamed to 'year' for OwidTable."""
    df = pd.DataFrame(
        {
            "years": [2000, 2005, 2010, 2015, 2020] * 3,
            "country": ["Australia"] * 5 + ["New Zealand"] * 5 + ["Japan"] * 5,
            "population": [
                19.2,
                20.4,
                22.0,
                23.8,
                25.7,
                3.9,
                4.1,
                4.4,
                4.6,
                5.1,
                126.8,
                127.8,
                128.1,
                127.1,
                125.8,
            ],
        }
    )
    ch = gr.Chart(df).mark_line().encode(x="years", y="population", entity="country")
    export = ch.export()

    # The 'years' column should be renamed to 'year' in the export
    data = export["owidDataset"]["data"]
    assert "year" in data, "Time column should be renamed to 'year'"
    assert "years" not in data, "Original column name should not be present"
    assert data["year"] == [2000, 2005, 2010, 2015, 2020] * 3


def test_column_names_with_spaces():
    """Test that column names with spaces are sanitized (spaces break OWID's slug format)."""
    df = pd.DataFrame(
        {
            "year": [2000, 2005, 2010, 2015, 2020] * 3,
            "country": ["Australia"] * 5 + ["New Zealand"] * 5 + ["Japan"] * 5,
            "population X": [
                19.2,
                20.4,
                22.0,
                23.8,
                25.7,
                3.9,
                4.1,
                4.4,
                4.6,
                5.1,
                126.8,
                127.8,
                128.1,
                127.1,
                125.8,
            ],
        }
    )
    ch = gr.Chart(df).mark_line().encode(x="year", y="population X", entity="country")
    export = ch.export()

    # The 'population X' column should be sanitized to 'population_X'
    data = export["owidDataset"]["data"]
    assert "population_X" in data, "Column with space should be sanitized"
    assert "population X" not in data, "Original column name should not be present"

    # Check dimensions use sanitized name
    dims = export["dimensions"]
    assert dims[0]["variableName"] == "population_X"


def test_column_names_with_special_characters():
    """Test that column names with special characters are sanitized."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "GDP (current $)": [1000, 2000, 3000],
            "country": ["USA"] * 3,
        }
    )
    ch = (
        gr.Chart(df).mark_line().encode(x="year", y="GDP (current $)", entity="country")
    )
    export = ch.export()

    # Special characters should be replaced with underscores
    data = export["owidDataset"]["data"]
    assert "GDP__current___" in data, "Column with special chars should be sanitized"
    assert "GDP (current $)" not in data, "Original column name should not be present"


def test_scatter_plot_export():
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .label("Life expectancy vs. GDP")
    )
    config = ch.export()

    # Check key fields
    assert config["title"] == "Life expectancy vs. GDP"
    assert config["chartTypes"] == ["ScatterPlot"]
    assert config["selectedEntityNames"] == []  # Scatter plots don't auto-select
    assert config["minTime"] == "latest"

    # Check dimensions
    assert config["dimensions"] == [
        {"property": "y", "variableName": "life_expectancy", "display": {}},
        {"property": "x", "variableName": "gdp", "display": {}},
    ]

    # Check owidDataset structure - data is just the dataframe as dict
    data = config["owidDataset"]["data"]
    assert data["gdp"] == [1000, 5000, 10000]
    assert data["life_expectancy"] == [50, 70, 80]
    assert data["entityName"] == ["Country A", "Country B", "Country C"]

    # Check metadata
    assert "gdp" in config["owidDataset"]["metadata"]
    assert "life_expectancy" in config["owidDataset"]["metadata"]

    # Test CSV output
    from owid.grapher import _config_to_csv

    csv_output = _config_to_csv(config)
    # CSV should have all columns
    assert "gdp" in csv_output
    assert "life_expectancy" in csv_output
    assert "entityName" in csv_output
    assert "Country A" in csv_output


def test_scatter_plot_with_year():
    """Test scatter plot with year column - should preserve all rows."""
    df = pd.DataFrame(
        {
            "gdp_per_capita": [5000, 15000, 25000, 8000, 18000, 28000],
            "life_expectancy": [65, 72, 78, 68, 74, 79],
            "country": ["Australia"] * 3 + ["New Zealand"] * 3,
            "year": [2000, 2010, 2020, 2000, 2010, 2020],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp_per_capita", y="life_expectancy", entity="country")
        .label(title="GDP vs Life Expectancy")
    )
    config = ch.export()

    # Check data preserves all 6 rows
    data = config["owidDataset"]["data"]
    assert len(data["gdp_per_capita"]) == 6
    assert len(data["life_expectancy"]) == 6
    assert len(data["entityName"]) == 6
    assert len(data["year"]) == 6

    # Check CSV output has all rows
    from owid.grapher import _config_to_csv

    csv_output = _config_to_csv(config)
    assert "year" in csv_output
    # Count rows (header + 6 data rows)
    assert csv_output.strip().count("\n") == 6


def test_scatter_plot_with_size():
    """Test scatter plot with size encoding."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "population": [10, 100, 50],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country", size="population")
    )
    config = ch.export()

    # Check sizeSlug is set
    assert config["sizeSlug"] == "population"

    # Check data includes population column
    data = config["owidDataset"]["data"]
    assert data["population"] == [10, 100, 50]


def test_axis_labels():
    """Test axis label configuration."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .axis(x_label="GDP per capita ($)", y_label="Life expectancy (years)")
    )
    config = ch.export()

    assert config["xAxis"] == {"label": "GDP per capita ($)"}
    assert config["yAxis"] == {"label": "Life expectancy (years)"}


def test_axis_units():
    """Test axis unit configuration."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .axis(x_unit="$", y_unit="years")
    )
    config = ch.export()

    # Check that units are in metadata
    metadata = config["owidDataset"]["metadata"]
    assert metadata["gdp"]["display"]["unit"] == "$"
    assert metadata["life_expectancy"]["display"]["unit"] == "years"


def test_axis_units_line_chart():
    """Test axis unit configuration for line charts."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "population": [1000, 2000, 3000],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_line()
        .encode(x="year", y="population")
        .axis(y_unit="millions")
    )
    config = ch.export()

    # Check that y_unit is in metadata for y column
    metadata = config["owidDataset"]["metadata"]
    assert metadata["population"]["display"]["unit"] == "millions"


def test_column_defs_generation():
    """Test that _build_column_defs correctly extracts units from metadata."""
    config = {
        "owidDataset": {
            "metadata": {
                "gdp": {"display": {"unit": "$"}},
                "life_expectancy": {"display": {"unit": "years"}},
            }
        }
    }

    column_defs_str = gr._build_column_defs(config)
    column_defs = json.loads(column_defs_str)

    # Check that we have two column definitions
    assert len(column_defs) == 2

    # Check structure
    gdp_def = next(d for d in column_defs if d["slug"] == "gdp")
    assert gdp_def["type"] == "Numeric"
    assert gdp_def["display"]["unit"] == "$"

    life_def = next(d for d in column_defs if d["slug"] == "life_expectancy")
    assert life_def["type"] == "Numeric"
    assert life_def["display"]["unit"] == "years"


def test_scatter_plot_iframe_with_units():
    """Test that scatter plot iframe includes columnDefs with units."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .axis(x_unit="$", y_unit="years")
    )

    # Get the iframe HTML
    html = ch._repr_html_()

    # Check that columnDefs is present in the HTML
    assert "const columnDefs" in html

    # Check that units are in the columnDefs
    assert '"unit": "$"' in html
    assert '"unit": "years"' in html

    # Check that OwidTable is called with columnDefs
    assert "new OwidTable(csvData, columnDefs)" in html


def test_axis_scale_configuration():
    """Test axis scale type and control configuration."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .axis(
            x_label="GDP per capita",
            x_scale="log",
            x_scale_control=True,
            y_label="Life expectancy",
        )
    )
    config = ch.export()

    # Check x-axis configuration
    assert config["xAxis"]["label"] == "GDP per capita"
    assert config["xAxis"]["scaleType"] == "log"
    assert config["xAxis"]["canChangeScaleType"] is True

    # Check y-axis configuration
    assert config["yAxis"]["label"] == "Life expectancy"


def test_axis_and_interact_compatibility():
    """Test that axis() and interact() work together without conflicts."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "population": [1000, 2000, 3000],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_line()
        .encode(x="year", y="population")
        .axis(y_label="Population (millions)")
        .interact(scale_control=True)
    )
    config = ch.export()

    # Check that both label and scale control are present
    assert config["yAxis"]["label"] == "Population (millions)"
    assert config["yAxis"]["scaleType"] == "linear"
    assert config["yAxis"]["canChangeScaleType"] is True


def test_xaxis_yaxis_methods():
    """Test xaxis() and yaxis() methods provide cleaner API."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .xaxis(label="GDP per capita", unit="$", scale="log", scale_control=True)
        .yaxis(label="Life expectancy", unit="years")
    )
    config = ch.export()

    # Check x-axis configuration
    assert config["xAxis"]["label"] == "GDP per capita"
    assert config["xAxis"]["scaleType"] == "log"
    assert config["xAxis"]["canChangeScaleType"] is True

    # Check y-axis configuration
    assert config["yAxis"]["label"] == "Life expectancy"

    # Check units in metadata
    metadata = config["owidDataset"]["metadata"]
    assert metadata["gdp"]["display"]["unit"] == "$"
    assert metadata["life_expectancy"]["display"]["unit"] == "years"


def test_matching_entities_only():
    """Test matchingEntitiesOnly filter."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .filter(matching_entities_only=True)
    )
    config = ch.export()

    # Check that matchingEntitiesOnly is set
    assert config["matchingEntitiesOnly"] is True


def test_variable_metadata():
    """Test variable() method for adding rich column metadata."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "population": [1000, 2000, 3000],
            "country": ["USA"] * 3,
        }
    )
    ch = (
        gr.Chart(df)
        .mark_line()
        .encode(x="year", y="population", entity="country")
        .variable(
            "population",
            name="Population",
            description_short="Total population in millions",
            unit="million people",
            short_unit="M",
            source_name="World Bank",
            source_link="https://data.worldbank.org",
        )
    )
    config = ch.export()

    # Check metadata includes variable config
    metadata = config["owidDataset"]["metadata"]["population"]
    assert metadata["name"] == "Population"
    assert metadata["descriptionShort"] == "Total population in millions"
    assert metadata["unit"] == "million people"
    assert metadata["shortUnit"] == "M"
    assert metadata["sourceName"] == "World Bank"
    assert metadata["sourceLink"] == "https://data.worldbank.org"
    # Timespan should be auto-computed from year column
    assert metadata["timespan"] == "2000–2020"


def test_variable_metadata_in_column_defs():
    """Test that variable metadata appears in columnDefs for OwidTable."""
    config = {
        "owidDataset": {
            "metadata": {
                "population": {
                    "display": {"unit": "M"},
                    "name": "Population",
                    "descriptionShort": "Total population",
                    "sourceName": "World Bank",
                    "descriptionKey": ["Point 1", "Point 2"],
                }
            }
        }
    }

    column_defs_str = gr._build_column_defs(config)
    column_defs = json.loads(column_defs_str)

    # Check that we have the column definition with all metadata
    assert len(column_defs) == 1
    pop_def = column_defs[0]
    assert pop_def["slug"] == "population"
    assert pop_def["type"] == "Numeric"
    assert pop_def["display"]["unit"] == "M"
    assert pop_def["name"] == "Population"
    assert pop_def["descriptionShort"] == "Total population"
    assert pop_def["sourceName"] == "World Bank"
    assert pop_def["descriptionKey"] == ["Point 1", "Point 2"]


def test_variable_chaining():
    """Test that multiple variable() calls work correctly."""
    df = pd.DataFrame(
        {
            "gdp": [1000, 5000, 10000],
            "life_expectancy": [50, 70, 80],
            "country": ["Country A", "Country B", "Country C"],
        }
    )
    ch = (
        gr.Chart(df)
        .mark_scatter()
        .encode(x="gdp", y="life_expectancy", entity="country")
        .variable("gdp", name="GDP per capita", unit="$")
        .variable("life_expectancy", name="Life expectancy", unit="years")
    )
    config = ch.export()

    # Check both variables have metadata
    metadata = config["owidDataset"]["metadata"]
    assert metadata["gdp"]["name"] == "GDP per capita"
    assert metadata["gdp"]["unit"] == "$"
    assert metadata["life_expectancy"]["name"] == "Life expectancy"
    assert metadata["life_expectancy"]["unit"] == "years"
