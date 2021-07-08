# -*- coding: utf-8 -*-
#
#  site.py
#  owid-grapher-py
#

"""
Tools for working with the live OWID grapher site.
"""

import json
import datetime as dt

from dateutil.parser import parse
import requests
import pandas as pd

DATA_URL = (
    "https://ourworldindata.org/grapher/data/variables/{variables}.json?v={version}"
)
GRAPHER_PREFIX = "https://ourworldindata.org/grapher/"


def get_chart_config(url: str) -> dict:
    "Get the internal OWID chart config for a chart URL."
    if not url.startswith(GRAPHER_PREFIX):
        raise Exception(f"not an OWID chart url: {url}")

    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"got HTTP {resp.status_code} loading {url}")

    body = resp.content.decode("utf8")

    _, config, _ = body.split("//EMBEDDED_JSON")

    return json.loads(config)


def get_chart_data(url: str) -> pd.DataFrame:
    "Fetch the data from an OWID chart page as a data frame."
    config = get_chart_config(url)
    version = config["version"]
    variable_ids = [dim["variableId"] for dim in config["dimensions"]]
    url = DATA_URL.format(variables="+".join(map(str, variable_ids)), version=version)
    owid_data = requests.get(url).json()

    entity_map = {int(k): v["name"] for k, v in owid_data["entityKey"].items()}
    frames = []
    for variable in owid_data["variables"].values():
        df = pd.DataFrame(
            {
                "year": variable["years"],
                "entity": [entity_map[e] for e in variable["entities"]],
                "variable": variable["name"],
                "value": variable["values"],
            }
        )
        if variable.get("display", {}).get("yearIsDay"):
            zero_day = parse(variable["display"]["zeroDay"]).date()
            df["date"] = df.pop("year").apply(lambda y: zero_day + dt.timedelta(days=y))
            df = df[["date", "entity", "variable", "value"]]

        frames.append(df)

    return pd.concat(frames)
