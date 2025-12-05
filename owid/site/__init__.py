# -*- coding: utf-8 -*-
#
#  site.py
#  owid-grapher-py
#

"""Tools for fetching data and configurations from the OWID website.

This module provides functions to interact with Our World in Data's live website
and API endpoints. You can:

- Fetch chart configurations to understand how charts are structured
- Download chart data directly as pandas DataFrames
- Access OWID's variable data API for custom analysis

The main use case is retrieving published OWID charts for exploration, reproduction,
or modification in Jupyter notebooks.

Example:
    ```python
    from owid.site import get_chart_data
    from owid.grapher import Chart

    # Fetch data from a published chart
    df = get_chart_data(slug='life-expectancy')

    # Create your own visualization
    Chart(df).mark_line().encode(
        x='year',
        y='value',
        entity='entity'
    )
    ```

API Endpoints:
    - Chart pages: https://ourworldindata.org/grapher/{slug}
    - Variable data: https://api.ourworldindata.org/v1/indicators/{id}.data.json
    - Variable metadata: https://api.ourworldindata.org/v1/indicators/{id}.metadata.json
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
    """Extract the chart configuration from an OWID chart page.

    Fetches an OWID chart page and extracts the embedded JSON configuration that
    defines the chart's appearance, data sources, and behavior. This config can be
    used to understand chart settings or to fetch the underlying data.

    Args:
        url: Full URL to an OWID chart page (must start with
            'https://ourworldindata.org/grapher/' unless force=True).
        force: If True, skips URL validation. Useful for testing or non-standard URLs.
            Default is False.

    Returns:
        Dictionary containing the complete chart configuration, including:
        - title, subtitle, note, sourceDesc: Chart text labels
        - dimensions: List of data dimensions with variable IDs
        - type: Chart type (LineChart, ScatterPlot, etc.)
        - selectedEntityNames: Pre-selected entities
        - x_axis, y_axis: Axis configuration
        - And many other display and behavior settings

    Raises:
        Exception: If the URL doesn't start with GRAPHER_PREFIX and force=False.
        Exception: If the HTTP request fails (non-200 status code).

    Example:
        ```python
        from owid.site import get_chart_config

        config = get_chart_config(
            url='https://ourworldindata.org/grapher/life-expectancy'
        )

        print(config['title'])  # 'Life expectancy'
        print(config['type'])   # 'LineChart'
        print(config['dimensions'])  # Variable info
        ```
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
    """Fetch data from an OWID chart as a pandas DataFrame.

    This is the primary function for retrieving chart data. It handles the complete
    pipeline: fetching the chart config, downloading variable data from the API,
    and converting it to a clean pandas DataFrame ready for analysis or visualization.

    You can specify either a full URL or just the chart slug (the part after /grapher/).

    Args:
        url: Full URL to an OWID chart. Example:
            'https://ourworldindata.org/grapher/life-expectancy'
        slug: Chart slug (URL suffix). Example: 'life-expectancy'.
            Use this as a shorthand instead of the full URL.

    Returns:
        DataFrame in long format with the following structure:

        For yearly data:
        - year (int): The year
        - entity (str): Country, region, or other entity name
        - variable (str): The metric/indicator name
        - value (float): The measurement value

        For date-based data:
        - date (datetime.date): The date
        - entity (str): Entity name
        - variable (str): Metric name
        - value (float): Measurement value

    Raises:
        ValueError: If neither url nor slug is provided.
        Exception: If the chart URL is invalid or data fetching fails.

    Example:
        ```python
        from owid.site import get_chart_data

        # Using slug (recommended)
        df = get_chart_data(slug='life-expectancy')

        # Using full URL
        df = get_chart_data(
            url='https://ourworldindata.org/grapher/co2-emissions'
        )

        # Examine the data
        print(df.head())
        print(df.shape)
        print(df.columns)
        ```

    Note:
        For charts with multiple variables, the DataFrame will contain all variables
        stacked in long format. Use df.variable.unique() to see available variables.
    """
    if not url and not slug:
        raise ValueError("must provide an url or a slug")

    full_url: str = url or (GRAPHER_PREFIX + slug)  # type: ignore

    config = get_chart_config(full_url)
    owid_data = get_owid_data(config)
    return owid_data_to_frame(owid_data)


def owid_data_to_frame(owid_data: dict) -> pd.DataFrame:
    """Convert OWID's internal data format to a pandas DataFrame.

    Takes the raw data structure returned by OWID's API (as retrieved by
    get_owid_data) and transforms it into a clean, analysis-ready DataFrame.
    This includes:
    - Mapping entity IDs to human-readable names
    - Converting year indices to actual years or dates
    - Stacking multiple variables into long format
    - Handling date-based data (yearIsDay format)

    Args:
        owid_data: Dictionary mapping variable IDs to their data. Each variable
            contains arrays of years, entity IDs, and values, plus metadata.
            This is the structure returned by get_owid_data().

    Returns:
        DataFrame in long format. For yearly data, columns are [year, entity, variable, value].
        For date-based data, columns are [date, entity, variable, value].

    Example:
        ```python
        from owid.site import get_chart_config, get_owid_data, owid_data_to_frame

        config = get_chart_config(
            url='https://ourworldindata.org/grapher/life-expectancy'
        )
        owid_data = get_owid_data(config)
        df = owid_data_to_frame(owid_data)

        print(df.head())
        #    year     entity            variable  value
        # 0  1950  Afghanistan  Life expectancy   28.0
        # 1  1951  Afghanistan  Life expectancy   28.4
        ```

    Note:
        This is a lower-level function. Most users should use get_chart_data()
        which calls this internally.
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

    Downloads the underlying data for all variables referenced in a chart configuration.
    This retrieves the actual time series data (years, entity IDs, values) but does not
    include entity names or perform any transformations. Use owid_data_to_frame() to
    convert this to a usable DataFrame.

    Args:
        config: Chart configuration dictionary as returned by get_chart_config().
            Must contain a 'dimensions' key with variableId values.

    Returns:
        Dictionary mapping variable IDs (int) to their data dictionaries. Each
        variable data dict contains:
        - id (int): Variable ID
        - years (list[int]): Array of year/time indices
        - entities (list[int]): Array of entity IDs
        - values (list[float]): Array of measurement values

        The three arrays are parallel - same index corresponds to a single observation.

    Example:
        ```python
        from owid.site import get_chart_config, get_owid_data

        config = get_chart_config(
            url='https://ourworldindata.org/grapher/life-expectancy'
        )

        owid_data = get_owid_data(config)

        # Inspect the structure
        for var_id, data in owid_data.items():
            print(f"Variable {var_id}:")
            print(f"  {len(data['years'])} observations")
            print(f"  Years: {min(data['years'])} to {max(data['years'])}")
        ```

    Note:
        This is a lower-level function. Most users should use get_chart_data()
        which handles the full pipeline including data transformation.
    """
    variable_ids = [dim["variableId"] for dim in config["dimensions"]]
    owid_data = {}
    for variable_id in variable_ids:
        url = DATA_URL.format(variable_id=variable_id)
        data = requests.get(url).json()
        data["id"] = variable_id
        owid_data[variable_id] = data
    return owid_data
