# -*- coding: utf-8 -*-
#
#  test_site.py
#  owid-grapher-py
#

import pandas as pd

from owid import site


def test_get_config():
    config = site.get_chart_config("https://ourworldindata.org/grapher/population")
    assert isinstance(config, dict)


def test_get_data():
    config = site.get_chart_data("https://ourworldindata.org/grapher/population")
    assert isinstance(config, pd.DataFrame)
