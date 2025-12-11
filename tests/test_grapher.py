# -*- coding: utf-8 -*-
#
#  test_grapher.py
#  notebooks
#

import pandas as pd

import owid.grapher as gr


def test_json_export():
    df = pd.DataFrame({"year": [2000, 2010, 2020], "population": [1234, 52342, 80123]})
    ch = (
        gr.Chart(df)
        .mark_line()
        .encode(x="year", y="population")
        .label("Too many Koalas?")
    )
    export = ch.export()

    # New export format has csv_data, column_defs, grapher_config
    assert "csv_data" in export
    assert "column_defs" in export
    assert "grapher_config" in export

    config = export["grapher_config"]
    assert config["title"] == "Too many Koalas?"
    assert config["chartTypes"] == ["LineChart"]
    assert config["selectedEntityNames"] == ["population"]

    # Check CSV data contains the expected columns
    csv_data = export["csv_data"]
    assert "year" in csv_data
    assert "population" in csv_data
    assert "2000" in csv_data
    assert "1234" in csv_data


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

    # The 'years' column should be renamed to 'year' in the CSV
    csv_data = export["csv_data"]
    assert "year," in csv_data or csv_data.startswith("year"), (
        "Time column should be renamed to 'year'"
    )
    assert "years" not in csv_data.split("\n")[0], (
        "Original column name should not be present"
    )


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

    # The 'population X' column should be sanitized to 'population_X' in CSV
    csv_data = export["csv_data"]
    assert "population_X" in csv_data, "Column with space should be sanitized"
    assert "population X" not in csv_data, "Original column name should not be present"

    # Check column_defs use sanitized name
    column_defs = export["column_defs"]
    assert column_defs[0]["slug"] == "population_X"


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
    csv_data = export["csv_data"]
    assert "GDP__current___" in csv_data, (
        "Column with special chars should be sanitized"
    )
    assert "GDP (current $)" not in csv_data, (
        "Original column name should not be present"
    )


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
    export = ch.export()
    config = export["grapher_config"]

    # Check key fields
    assert config["title"] == "Life expectancy vs. GDP"
    assert config["chartTypes"] == ["ScatterPlot"]
    assert config["selectedEntityNames"] == []  # Scatter plots don't auto-select
    assert config["minTime"] == "latest"

    # Check slugs for scatter
    assert config["ySlugs"] == "life_expectancy"
    assert config["xSlug"] == "gdp"

    # Check CSV contains all columns
    csv_data = export["csv_data"]
    assert "gdp" in csv_data
    assert "life_expectancy" in csv_data
    assert "entityName" in csv_data
    assert "Country A" in csv_data


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
    export = ch.export()

    # Check CSV preserves all 6 rows (header + 6 data rows = 7 lines)
    csv_data = export["csv_data"]
    assert "year" in csv_data
    # Count rows (header + 6 data rows)
    assert csv_data.strip().count("\n") == 6


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
    export = ch.export()
    config = export["grapher_config"]

    # Check sizeSlug is set
    assert config["sizeSlug"] == "population"

    # Check CSV includes population column
    csv_data = export["csv_data"]
    assert "population" in csv_data


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
    export = ch.export()
    config = export["grapher_config"]

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
    export = ch.export()

    # Check that units are in column_defs
    column_defs = export["column_defs"]
    gdp_def = next(d for d in column_defs if d["slug"] == "gdp")
    life_def = next(d for d in column_defs if d["slug"] == "life_expectancy")
    assert gdp_def["display"]["unit"] == "$"
    assert life_def["display"]["unit"] == "years"


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
    export = ch.export()

    # Check that y_unit is in column_defs
    column_defs = export["column_defs"]
    pop_def = next(d for d in column_defs if d["slug"] == "population")
    assert pop_def["display"]["unit"] == "millions"


def test_column_defs_structure():
    """Test that column_defs have correct structure."""
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
    export = ch.export()
    column_defs = export["column_defs"]

    # Check structure
    assert len(column_defs) == 1
    assert column_defs[0]["slug"] == "population"
    assert column_defs[0]["type"] == "Numeric"
    assert column_defs[0]["display"]["unit"] == "millions"


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
    export = ch.export()
    config = export["grapher_config"]

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
    export = ch.export()
    config = export["grapher_config"]

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
    export = ch.export()
    config = export["grapher_config"]

    # Check x-axis configuration
    assert config["xAxis"]["label"] == "GDP per capita"
    assert config["xAxis"]["scaleType"] == "log"
    assert config["xAxis"]["canChangeScaleType"] is True

    # Check y-axis configuration
    assert config["yAxis"]["label"] == "Life expectancy"

    # Check units in column_defs
    column_defs = export["column_defs"]
    gdp_def = next(d for d in column_defs if d["slug"] == "gdp")
    life_def = next(d for d in column_defs if d["slug"] == "life_expectancy")
    assert gdp_def["display"]["unit"] == "$"
    assert life_def["display"]["unit"] == "years"


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
    export = ch.export()
    config = export["grapher_config"]

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
    export = ch.export()

    # Check column_defs includes variable config
    column_defs = export["column_defs"]
    pop_def = next(d for d in column_defs if d["slug"] == "population")
    assert pop_def["name"] == "Population"
    assert pop_def["descriptionShort"] == "Total population in millions"
    assert pop_def["unit"] == "million people"
    assert pop_def["shortUnit"] == "M"
    assert pop_def["sourceName"] == "World Bank"
    assert pop_def["sourceLink"] == "https://data.worldbank.org"
    # Timespan should be auto-computed from year column
    assert pop_def["timespan"] == "2000–2020"


def test_variable_metadata_in_column_defs():
    """Test that variable metadata appears correctly in column_defs."""
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
            description_short="Total population",
            source_name="World Bank",
            description_key=["Point 1", "Point 2"],
        )
        .axis(y_unit="M")
    )
    export = ch.export()
    column_defs = export["column_defs"]

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
    export = ch.export()

    # Check both variables have metadata
    column_defs = export["column_defs"]
    gdp_def = next(d for d in column_defs if d["slug"] == "gdp")
    life_def = next(d for d in column_defs if d["slug"] == "life_expectancy")
    assert gdp_def["name"] == "GDP per capita"
    assert gdp_def["unit"] == "$"
    assert life_def["name"] == "Life expectancy"
    assert life_def["unit"] == "years"


def test_plot_wrapper_basic():
    """Test basic plot() wrapper function."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "population": [1000, 2000, 3000],
            "entity": ["USA"] * 3,
        }
    )
    ch = gr.plot(
        df,
        y="population",
        title="Population over time",
    )
    export = ch.export()
    config = export["grapher_config"]

    # Check default types (line + bar)
    assert "LineChart" in config["chartTypes"]
    assert "DiscreteBar" in config["chartTypes"]
    assert config["title"] == "Population over time"


def test_plot_wrapper_with_map():
    """Test plot() wrapper with map as first type."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "gdp": [1000, 5000, 10000],
            "entity": ["USA"] * 3,
        }
    )
    ch = gr.plot(
        df,
        y="gdp",
        types=["map", "line"],
        color_scheme="GnBu",
        custom_numeric_values=[0, 1000, 5000, 10000],
        unit="$",
        title="GDP per capita",
    )
    export = ch.export()
    config = export["grapher_config"]

    # Check map is enabled and is default tab
    assert config["hasMapTab"] is True
    assert config["tab"] == "map"

    # Check map color scale
    assert config["map"]["colorScale"]["baseColorScheme"] == "GnBu"
    assert config["map"]["colorScale"]["binningStrategy"] == "manual"
    assert config["map"]["colorScale"]["customNumericValues"] == [0, 1000, 5000, 10000]

    # Check column_defs has unit
    column_defs = export["column_defs"]
    assert column_defs[0]["display"]["unit"] == "$"


def test_plot_wrapper_interactivity():
    """Test plot() wrapper interactivity options."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020],
            "population": [1000, 2000, 3000],
            "entity": ["USA"] * 3,
        }
    )
    ch = gr.plot(
        df,
        y="population",
        scale_control=True,
        entity_control=True,
    )
    export = ch.export()
    config = export["grapher_config"]

    # Check interactivity settings
    assert config["yAxis"]["canChangeScaleType"] is True
    # addCountryMode defaults to "add-country" so it's not in output
    # but entity control should be enabled (not "disabled")
    assert config.get("addCountryMode", "add-country") == "add-country"


def test_plot_wrapper_entity_selection():
    """Test plot() wrapper with entity selection."""
    df = pd.DataFrame(
        {
            "year": [2000, 2010, 2020] * 3,
            "population": [1000, 2000, 3000, 500, 700, 900, 800, 1200, 1600],
            "entity": ["USA"] * 3 + ["UK"] * 3 + ["France"] * 3,
        }
    )
    ch = gr.plot(
        df,
        y="population",
        entities=["USA", "UK"],
    )
    export = ch.export()
    config = export["grapher_config"]

    # Check entity selection
    assert config["selectedEntityNames"] == ["USA", "UK"]
