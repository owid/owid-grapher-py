# -*- coding: utf-8 -*-
#
#  test_grapher.py
#  owid-grapher-py
#

import json

import pandas as pd
import pytest

from owid.grapher import GRAPHER_BUNDLE_URL, Chart, GrapherConfig, day_number


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2000, 2010, 2020] * 2,
            "entity": ["France"] * 3 + ["Japan"] * 3,
            "population": [59.0, 63.0, 65.0, 127.0, 128.0, 126.0],
        }
    )


# =============================================================================
# Shaping the DataFrame into what Grapher reads
# =============================================================================


def test_entity_column_is_renamed():
    csv = Chart(sample_frame()).export()["csv_data"]
    assert csv.split("\n")[0] == "year,entityName,population"


def test_entity_column_found_by_any_of_its_names():
    for name in ["entityName", "entity", "country", "location"]:
        df = sample_frame().rename(columns={"entity": name})
        assert "entityName" in Chart(df).export()["csv_data"].split("\n")[0]


def test_entity_column_can_be_named_explicitly():
    df = sample_frame().rename(columns={"entity": "who"})
    csv = Chart(df, entity="who").export()["csv_data"]
    assert csv.split("\n")[0] == "year,entityName,population"


def test_missing_entity_column_says_what_to_do():
    df = sample_frame().rename(columns={"entity": "who"})
    with pytest.raises(ValueError, match="no entity column found"):
        Chart(df).export()

    with pytest.raises(ValueError, match="not in the DataFrame"):
        Chart(df, entity="nope").export()


def test_dates_are_passed_as_a_date_column():
    """Grapher reads ISO dates from `date` and plain years from `year`."""
    df = pd.DataFrame(
        {
            "day": ["2021-06-01", "2021-06-02"],
            "entity": ["France", "France"],
            "cases": [1, 2],
        }
    )
    assert Chart(df).export()["csv_data"].split("\n")[0].startswith("date,")
    assert Chart(sample_frame()).export()["csv_data"].split("\n")[0].startswith("year,")


def test_day_number_converts_dates_to_graphers_time_values():
    """Grapher counts days from 2020-01-21, so a date can't be written as itself."""
    assert day_number("2020-01-21") == 0
    assert day_number("2021-06-01") == 497
    assert day_number(pd.Timestamp("2021-06-01")) == 497


def test_column_names_are_sanitized_into_slugs():
    """Grapher slugs hold no spaces or brackets, in the CSV or in columns=."""
    df = sample_frame().rename(columns={"population": "population (millions)"})
    export = Chart(
        df, columns={"population (millions)": {"name": "Population"}}
    ).export()
    assert "population__millions_" in export["csv_data"].split("\n")[0]
    assert export["column_defs"][0]["slug"] == "population__millions_"


# =============================================================================
# Column metadata
# =============================================================================


def test_columns_without_metadata_get_no_def():
    """Grapher infers the type and formatting of a plain column itself."""
    df = sample_frame().assign(gdp=[1, 2, 3, 4, 5, 6])
    assert Chart(df).export()["column_defs"] == []


def test_annotated_columns_are_typed_from_the_frame():
    """A def without a type turns off Grapher's own detection for that column."""
    df = sample_frame().assign(region=["Europe"] * 3 + ["Asia"] * 3)
    chart = Chart(
        df, columns={"population": {"name": "Population"}, "region": {"name": "Region"}}
    )
    defs = {d["slug"]: d["type"] for d in chart.export()["column_defs"]}
    assert defs == {"population": "Numeric", "region": "String"}


def test_column_metadata_is_passed_through():
    chart = Chart(
        sample_frame(),
        columns={
            "population": {
                "name": "Population",
                "shortUnit": " million",
                "sourceName": "UN WPP (2024)",
            }
        },
    )
    (definition,) = chart.export()["column_defs"]
    assert definition == {
        "slug": "population",
        "type": "Numeric",
        "name": "Population",
        "shortUnit": " million",
        "sourceName": "UN WPP (2024)",
    }


def test_metadata_for_an_unknown_column_is_an_error():
    with pytest.raises(ValueError, match="aren't in the DataFrame"):
        Chart(sample_frame(), columns={"populaton": {"name": "typo"}}).export()


# =============================================================================
# The config
# =============================================================================


def test_config_is_passed_through_untouched():
    # Annotated because a plain dict literal assigned to a variable loses the
    # TypedDict; inline `config={...}` arguments don't need this.
    config: GrapherConfig = {
        "title": "Population",
        "chartTypes": ["LineChart", "DiscreteBar"],
        "hasMapTab": True,
        "map": {"colorScale": {"baseColorScheme": "YlGnBu"}},
    }
    exported = Chart(sample_frame(), config=config).export()["grapher_config"]
    assert {key: exported[key] for key in config} == config


def test_unknown_config_keys_are_rejected_with_a_suggestion():
    """The type checker catches these too -- hence the suppressions."""
    with pytest.raises(ValueError, match="did you mean 'title'"):
        Chart(sample_frame(), config={"titel": "typo"})  # ty: ignore

    with pytest.raises(ValueError, match="not Grapher config keys: 'wat'"):
        Chart(sample_frame(), config={"wat": 1})  # ty: ignore


def test_selection_defaults_to_the_frames_entities():
    """Line and bar charts draw nothing until entities are selected."""
    config = Chart(sample_frame()).export()["grapher_config"]
    assert config["selectedEntityNames"] == ["France", "Japan"]


def test_selection_can_be_set_explicitly():
    chart = Chart(sample_frame(), config={"selectedEntityNames": ["Japan"]})
    assert chart.export()["grapher_config"]["selectedEntityNames"] == ["Japan"]


def test_config_stays_editable_after_construction():
    chart = Chart(sample_frame(), config={"title": "Population"})
    chart.config["subtitle"] = "Millions of people"
    assert chart.export()["grapher_config"]["subtitle"] == "Millions of people"


def test_the_chart_does_not_modify_the_config_it_was_given():
    config: GrapherConfig = {"title": "Population"}
    Chart(sample_frame(), config=config).export()
    assert config == {"title": "Population"}


# =============================================================================
# Rendering
# =============================================================================


def test_to_html_hands_everything_to_the_packages_loader():
    html = Chart(sample_frame(), config={"title": "Population"}).to_html()
    assert "GrapherLoader.fromCsv(" in html
    assert f"{GRAPHER_BUNDLE_URL}/grapher.standalone.min.js" in html
    assert f"{GRAPHER_BUNDLE_URL}/grapher.css" in html
    assert '"title": "Population"' in html


def test_html_survives_data_that_looks_like_markup():
    """A `</script>` in the data must not close the script element early."""
    chart = Chart(sample_frame(), config={"title": "</script> and `x`"})
    html = chart.to_html()
    assert "</script> and" not in html
    assert "<\\/script> and `x`" in html


def test_repr_html_is_an_iframe_of_the_requested_height():
    html = Chart(sample_frame(), height=450)._repr_html_()
    assert "<iframe" in html
    assert "height: 450px" in html


def test_export_is_json_serializable():
    """export.py hands the config and column defs to a browser as JSON."""
    export = Chart(sample_frame(), config={"title": "Population"}).export()
    assert set(export) == {"csv_data", "column_defs", "grapher_config"}
    json.dumps({k: v for k, v in export.items() if k != "csv_data"})


def test_repr_mentions_the_title_and_size():
    chart = Chart(sample_frame(), config={"title": "Population"})
    assert repr(chart) == "<Chart 'Population' of 6 rows>"
