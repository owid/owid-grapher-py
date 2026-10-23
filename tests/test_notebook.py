# -*- coding: utf-8 -*-
#
#  test_notebook.py
#  owid-grapher-py
#

import pandas as pd

from owid import site
from owid.grapher import (
    Chart,  # noqa: F401 - the generated code evaluates to this
    notebook,
)


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2015, 2016, 2017],
            "entity": ["Lars", "Lars", "Lars"],
            "variable": ["height", "height", "height"],
            "value": [1.9, 1.9, 1.9],
        }
    )


def test_translate_a_minimal_chart():
    config = {"type": "LineChart", "title": "Lars stays the same height"}
    py = notebook.translate_config(config, sample_data())
    assert py == (
        "Chart(\n"
        "    data,\n"
        "    config={'title': 'Lars stays the same height', "
        "'chartTypes': ['LineChart'], 'ySlugs': 'value'},\n"
        ")"
    )
    assert isinstance(eval(py, {"Chart": Chart, "data": sample_data()}), Chart)


def test_site_only_keys_are_dropped():
    config = {
        "id": 123,
        "slug": "some-chart",
        "version": 7,
        "isPublished": True,
        "dimensions": [{"property": "y", "variableId": 42}],
        "title": "Kept",
    }
    local = notebook.local_config(config, sample_data())
    assert set(local) == {"title", "ySlugs"}


def test_unknown_keys_are_dropped_so_the_config_stays_valid():
    """Published configs carry legacy keys Grapher's schema no longer has."""
    config = {"title": "Kept", "selectedData": [{"entityId": 1}], "type": "LineChart"}
    local = notebook.local_config(config, sample_data())
    assert "selectedData" not in local
    Chart(sample_data(), config=local)  # would raise on an unknown key


def test_chart_types_come_from_either_spelling():
    data = sample_data()
    assert notebook.local_config({"type": "DiscreteBar"}, data)["chartTypes"] == [
        "DiscreteBar"
    ]
    assert notebook.local_config({"chartTypes": ["SlopeChart"]}, data)[
        "chartTypes"
    ] == ["SlopeChart"]


def test_round_trip():
    "Can we replicate a published chart from its own config?"
    for slug in ["life-expectancy", "population"]:
        url = f"https://ourworldindata.org/grapher/{slug}"
        config = site.get_chart_config(url)
        data = site.get_chart_data(url)

        py = notebook.translate_config(config, data)
        chart = eval(py, {"Chart": Chart, "data": data})

        # the code we generated draws a chart whose config we can serialize
        export = chart.export()
        assert export["grapher_config"]["title"] == config["title"]
        assert "GrapherLoader.fromCsv(" in chart.to_html()
