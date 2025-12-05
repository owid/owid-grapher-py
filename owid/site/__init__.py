# -*- coding: utf-8 -*-
#
#  site.py
#  owid-grapher-py
#

"""
Tools for working with the live OWID grapher site.
"""

import datetime as dt
import json
from typing import Optional

import pandas as pd
import requests
from dateutil.parser import parse

DATA_URL = "https://api.ourworldindata.org/v1/indicators/{variable_id}.data.json"
METADATA_URL = (
    "https://api.ourworldindata.org/v1/indicators/{variable_id}.metadata.json"
)
GRAPHER_PREFIX = "https://ourworldindata.org/grapher/"
EPOCH_DATE = "2020-01-21"


def get_chart_config(url: str, force: bool = False) -> dict:
    """Get the internal OWID chart config from a chart URL.

    Args:
        url: Full URL to an OWID chart page.
        force: Skip URL validation if True.

    Returns:
        Dictionary containing the chart configuration.

    Raises:
        Exception: If URL is invalid or request fails.
    """
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
    """Fetch data from an OWID chart as a DataFrame.

    Args:
        url: Full URL to an OWID chart (e.g., 'https://ourworldindata.org/grapher/life-expectancy').
        slug: Chart slug as alternative to URL (e.g., 'life-expectancy').

    Returns:
        DataFrame with chart data in long format.

    Raises:
        ValueError: If neither url nor slug is provided.

    Example:
        ```python
        >>> df = get_chart_data(slug='life-expectancy')
        >>> df = get_chart_data(url='https://ourworldindata.org/grapher/co2-emissions')
        ```
    """
    if not url and not slug:
        raise ValueError("must provide an url or a slug")

    full_url: str = url or (GRAPHER_PREFIX + slug)  # type: ignore

    config = get_chart_config(full_url)
    owid_data = get_owid_data(config)
    return owid_data_to_frame(owid_data)


def owid_data_to_frame(owid_data: dict) -> pd.DataFrame:
    """Convert OWID's internal data format to a pandas DataFrame.

    Args:
        owid_data: Dictionary with OWID variable data.

    Returns:
        DataFrame in long format with columns: year/date, entity, variable, value.
    """
    frames = []
    for variable in owid_data.values():
        # fetch metadata to get entity mapping
        meta = requests.get(METADATA_URL.format(variable_id=variable["id"])).json()
        entities = meta["dimensions"]["entities"]["values"]
        entity_map = {e["id"]: e["name"] for e in entities}

        df = pd.DataFrame(
            {
                "year": variable["years"],
                "entity": [entity_map[e] for e in variable["entities"]],
                "variable": meta["name"],
                "value": variable["values"],
            }
        )

        # handle date display
        if meta.get("display", {}).get("yearIsDay"):
            zero_day = parse(meta["display"].get("zeroDay", EPOCH_DATE)).date()
            df["date"] = df.pop("year").apply(lambda y: zero_day + dt.timedelta(days=y))
            df = df[["date", "entity", "variable", "value"]]

        frames.append(df)

    return pd.concat(frames)


def get_owid_data(config: dict) -> dict:
    """Fetch raw variable data from OWID's API.

    Args:
        config: Chart configuration dictionary from get_chart_config().

    Returns:
        Dictionary with variable data for all variables in the chart.
    """
    variable_ids = [dim["variableId"] for dim in config["dimensions"]]
    owid_data = {}
    for variable_id in variable_ids:
        url = DATA_URL.format(variable_id=variable_id)
        data = requests.get(url).json()
        data["id"] = variable_id
        owid_data[variable_id] = data
    return owid_data
