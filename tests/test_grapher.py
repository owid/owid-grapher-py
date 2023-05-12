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
    df = pd.DataFrame({'year': [2000, 2010, 2020], 'population': [1234, 52342, 80123]})
    ch = gr.Chart(
        df
    ).mark_line().encode(
        x='year', 
        y='population'
    ).label('Too many Koalas?')
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
        "dimensions": [
          {"property": "y", "variableId": 1, "display": {}}
        ],
        "owidDataset": {
            1: {
            "data": {
              "years": [2000, 2010, 2020], 
              "entities": [1, 1, 1], 
              "values": [1234, 52342, 80123]
            },
            "metadata": {
              "id": 1, 
              "name": "dummy", 
              "display": {},
              "dimensions": {
                "entities": {
                  "values": [
                    {
                      "id": 1, 
                      "name": "population"
                    }
                  ]
                },
                "years": {
                  "values": [
                    {
                      "id": 2000
                    }, 
                    {
                      "id": 2010
                    }, 
                    {
                      "id": 2020
                    }
                  ]
                }
              }
            }
          }
        }, 
        "selectedEntityNames": ["population"]
      }

