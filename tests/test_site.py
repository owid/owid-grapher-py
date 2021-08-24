# -*- coding: utf-8 -*-
#
#  test_site.py
#  owid-grapher-py
#

from owid import site

import pandas as pd


def test_get_config():
    config = site.get_chart_config(
        "https://ourworldindata.org/grapher/israel-covid-19-cases-by-age"
    )
    assert isinstance(config, dict)


def test_get_data_by_url():
    config = site.get_chart_data(
        "https://ourworldindata.org/grapher/israel-covid-19-cases-by-age"
    )
    assert isinstance(config, pd.DataFrame)


def test_get_data_by_slug():
    config = site.get_chart_data(slug="israel-covid-19-cases-by-age")
    assert isinstance(config, pd.DataFrame)
