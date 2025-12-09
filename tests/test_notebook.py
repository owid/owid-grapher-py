# -*- coding: utf-8 -*-
#
#  test_notebook.py
#  owid-grapher-py
#

import json

import pandas as pd

from owid import grapher, site  # noqa
from owid.grapher import notebook


def test_translate_line_chart_no_frills():
    "Check that we can generate a minimal line chart."
    config = {
        "type": "LineChart",
        "selectedData": [{"entityId": 1, "name": "Lars"}],
        "dimensions": [],
    }
    data = pd.DataFrame(
        {
            "year": [2015, 2016, 2017, 2018],
            "entity": ["Lars", "Lars", "Lars", "Lars"],
            "variable": ["height", "height", "height", "height"],
            "value": [1.9, 1.9, 1.9, 1.9],
        }
    )
    py = notebook.translate_config(config, data)
    expected = """
grapher.Chart(
    data
).mark_line().encode(
    x="year",
    y="value"
).interact(
    entity_control=True
)
""".strip()
    assert py == expected


def test_translate_line_chart_date():
    "Check that we autodetect when a chart uses dates instead of years."
    config = {
        "type": "LineChart",
        "selectedData": [{"entityId": 1, "name": "Lars"}],
        "dimensions": [],
    }
    data = pd.DataFrame(
        {
            "date": ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
            "entity": ["Lars", "Lars", "Lars", "Lars"],
            "variable": ["height", "height", "height", "height"],
            "value": [1.9, 1.9, 1.9, 1.9],
        }
    )
    py = notebook.translate_config(config, data)
    expected = """
grapher.Chart(
    data
).mark_line().encode(
    x="date",
    y="value"
).interact(
    entity_control=True
)
""".strip()
    assert py == expected


def test_translate_labels():
    "Check that we autodetect when a chart uses dates instead of years."
    config = {
        "type": "LineChart",
        "selectedData": [{"entityId": 1, "name": "Lars"}],
        "title": "Lars does not get taller ever year",
        "subtitle": "Soon he will begin shrinking",
        "sourceDesc": "An elusive gypsy",
        "note": "Perhaps not 100% reliable",
        "dimensions": [],
    }
    data = pd.DataFrame(
        {
            "year": [2015, 2016, 2017, 2018],
            "entity": ["Lars", "Lars", "Lars", "Lars"],
            "variable": ["height", "height", "height", "height"],
            "value": [1.9, 1.9, 1.9, 1.9],
        }
    )
    py = notebook.translate_config(config, data)
    expected = """
grapher.Chart(
    data
).mark_line().encode(
    x="year",
    y="value"
).label(
    title="Lars does not get taller ever year",
    subtitle="Soon he will begin shrinking",
    source_desc="An elusive gypsy",
    note="Perhaps not 100% reliable"
).interact(
    entity_control=True
)
""".strip()
    assert py == expected


def test_round_trip():
    "Can we replicate the chart with life expectancy."
    for slug in ["life-expectancy", "population"]:
        url = f"https://ourworldindata.org/grapher/{slug}"
        config = site.get_chart_config(url)
        data = site.get_chart_data(url)
        py = notebook.translate_config(config, data)

        # check for lingering templates
        assert "{" not in py

        # the code is executable
        chart = eval(py)

        # the chart exports to a config
        gen_config = chart.export()

        # the config is valid json
        assert gen_config
        json.dumps(gen_config)
