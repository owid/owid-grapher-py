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

from dataclasses_json.api import LetterCase
from dataclasses_json import dataclass_json
from owid.grapher.internal import Variable, OWIDData
from typing import Optional, List, Dict
from dataclasses import dataclass

from dateutil.parser import parse
import requests
import pandas as pd

DATA_URL = (
    "https://ourworldindata.org/grapher/data/variables/{variables}.json?v={version}"
)
GRAPHER_PREFIX = "https://ourworldindata.org/grapher/"
EPOCH_DATE = "2020-01-21"


def get_chart_config(url: str, force: bool = False) -> dict:
    "Get the internal OWID chart config for a chart URL."
    if not url.startswith(GRAPHER_PREFIX) and not force:
        raise Exception(f"not an OWID chart url: {url}")

    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"got HTTP {resp.status_code} loading {url}")

    body = resp.content.decode("utf8")

    _, config, _ = body.split("//EMBEDDED_JSON")

    return json.loads(config)


def get_chart_data(
    url: Optional[str] = None, slug: Optional[str] = None
) -> pd.DataFrame:
    "Fetch the data from an OWID chart page as a data frame."
    if not url and not slug:
        raise ValueError("must provide an url or a slug")

    full_url: str = url or (GRAPHER_PREFIX + slug)  # type: ignore

    config = get_chart_config(full_url)
    owid_data = get_owid_data(config)
    return owid_data_to_frame(owid_data)


def get_owid_data(config: dict) -> OWIDData:
    version = config["version"]
    variable_ids = [dim["variableId"] for dim in config["dimensions"]]
    url = DATA_URL.format(variables="+".join(map(str, variable_ids)), version=version)
    owid_data = requests.get(url).json()
    return OWIDData.from_dict(owid_data)  # type: ignore
