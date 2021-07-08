# -*- coding: utf-8 -*-
#
#  test_grapher.py
#  notebooks
#

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
