# -*- coding: utf-8 -*-
#
#  grapher.py
#  notebooks
#

from typing import Dict, Any

from .chart import DeclarativeConfig


class Chart(DeclarativeConfig):
    def to_py(self):
        return super().to_py("grapher.Chart")

    def _repr_html_(self):
        pass
