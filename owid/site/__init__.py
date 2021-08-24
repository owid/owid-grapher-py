# -*- coding: utf-8 -*-
#
#  site.py
#  owid-grapher-py
#

"""
Tools for working with the live OWID grapher site. Note that the site is a living
space and the conventions underlying this logic are subject to change at any time.
This is not a stable long-term API that we intend to maintain at this stage.
"""

from dataclasses_json import dataclass_json
from owid.grapher.internal import StandaloneChartConfig, Dataset, ChartConfig
from typing import Optional, List, Dict, Union
from dataclasses import dataclass

from dateutil.parser import parse
import requests
import pandas as pd

from owid.grapher import engine


# currently, charts get their data baked to a special URL on the site
DATA_URL = (
    "https://ourworldindata.org/grapher/data/variables/{variables}.json?v={version}"
)
GRAPHER_PREFIX = "https://ourworldindata.org/grapher/"


def get_chart_config(url: str, force: bool = False) -> ChartConfig:
    """
    Get the internal OWID chart config for a chart URL. The force parameter
    skips the URL check, allowing you to use it against a local development
    environment, for example.

    This works because each chart is baked to an HTML page that contains
    an embedded JSON document serving as OWID's internal API for data
    visualisation.
    """
    if not url.startswith(GRAPHER_PREFIX) and not force:
        raise Exception(f"not an OWID chart url: {url}")

    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"got HTTP {resp.status_code} loading {url}")

    body = resp.content.decode("utf8")

    _, config, _ = body.split("//EMBEDDED_JSON")

    return ChartConfig.from_json(config)


def get_chart_data(
    url: Optional[str] = None, slug: Optional[str] = None
) -> pd.DataFrame:
    "Fetch the data from an OWID chart page as a data frame."
    if not url and not slug:
        raise ValueError("must provide an url or a slug")

    full_url: str = url or (GRAPHER_PREFIX + slug)  # type: ignore

    config = get_chart_config(full_url)
    dataset = get_owid_dataset(config)
    return engine.dataset_to_frame(dataset)


def get_owid_dataset(config: Union[ChartConfig, StandaloneChartConfig]) -> Dataset:
    "Fetch the data underlying a chart on the site."
    if isinstance(config, StandaloneChartConfig):
        # chart is already standalone
        return config.owid_data

    # chart is supported by remote data that we have to fetch
    url = get_data_url(config)
    owid_data = requests.get(url).json()
    return Dataset.from_dict(owid_data)  # type: ignore


def get_data_url(config: ChartConfig) -> str:
    "Get the published URL that the data lives at."
    version = config.version
    variable_ids = [dim.variable_id for dim in config.dimensions]
    url = DATA_URL.format(variables="+".join(map(str, variable_ids)), version=version)
    return url
