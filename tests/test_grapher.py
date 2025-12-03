# -*- coding: utf-8 -*-
#
#  test_grapher.py
#  notebooks
#

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
    assert ch.export() == {
        "tab": "chart",
        "title": "Too many Koalas?",
        "subtitle": "",
        "note": "",
        "sourceDesc": "",
        "hideLogo": True,
        "isPublished": True,
        "type": "LineChart",
        "hideTitleAnnotation": False,
        "hideLegend": True,
        "hideEntityControls": True,
        "hideRelativeToggle": True,
        "hasMapTab": False,
        "stackMode": "absolute",
        "yAxis": {},
        "chartTypes": ["LineChart"],
        "dimensions": [{"property": "y", "variableId": 1, "display": {}}],
        "owidDataset": {
            1: {
                "data": {
                    "years": [2000, 2010, 2020],
                    "entities": [1, 1, 1],
                    "values": [1234, 52342, 80123],
                },
                "metadata": {
                    "id": 1,
                    "name": "dummy",
                    "display": {},
                    "dimensions": {
                        "entities": {"values": [{"id": 1, "name": "population"}]},
                        "years": {"values": [{"id": 2000}, {"id": 2010}, {"id": 2020}]},
                    },
                },
            }
        },
        "selectedEntityNames": ["population"],
    }


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
        .encode(x="gdp", y="life_expectancy", c="country")
        .label("Life expectancy vs. GDP")
    )
    config = ch.export()
    assert config == {
        "tab": "chart",
        "title": "Life expectancy vs. GDP",
        "subtitle": "",
        "note": "",
        "sourceDesc": "",
        "hideLogo": True,
        "isPublished": True,
        "type": "ScatterPlot",
        "hideTitleAnnotation": True,
        "hideLegend": False,
        "hideEntityControls": True,
        "hideRelativeToggle": True,
        "hasMapTab": False,
        "stackMode": "absolute",
        "yAxis": {},
        "chartTypes": ["ScatterPlot"],
        "dimensions": [
            {"property": "y", "variableId": 2, "display": {}},
            {"property": "x", "variableId": 1, "display": {}},
        ],
        "owidDataset": {
            1: {
                "data": {
                    "years": [0, 1, 2],
                    "entities": [1, 2, 3],
                    "values": [1000, 5000, 10000],
                },
                "metadata": {
                    "id": 1,
                    "name": "gdp",
                    "display": {},
                    "dimensions": {
                        "entities": {
                            "values": [
                                {"id": 1, "name": "Country A"},
                                {"id": 2, "name": "Country B"},
                                {"id": 3, "name": "Country C"},
                            ]
                        },
                        "years": {"values": [{"id": 0}, {"id": 1}, {"id": 2}]},
                    },
                },
            },
            2: {
                "data": {
                    "years": [0, 1, 2],
                    "entities": [1, 2, 3],
                    "values": [50, 70, 80],
                },
                "metadata": {
                    "id": 2,
                    "name": "life_expectancy",
                    "display": {},
                    "dimensions": {
                        "entities": {
                            "values": [
                                {"id": 1, "name": "Country A"},
                                {"id": 2, "name": "Country B"},
                                {"id": 3, "name": "Country C"},
                            ]
                        },
                        "years": {"values": [{"id": 0}, {"id": 1}, {"id": 2}]},
                    },
                },
            },
        },
        "selectedEntityNames": ["Country A", "Country B", "Country C"],
        "minTime": "latest",
    }

    # Test CSV output
    from owid.grapher import _config_to_csv

    csv_output = _config_to_csv(config)
    expected_csv = """entityName,entityId,year,gdp,life_expectancy
Country A,1,0,1000,50
Country B,2,1,5000,70
Country C,3,2,10000,80"""
    assert csv_output == expected_csv
