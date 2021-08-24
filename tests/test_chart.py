#
#  test_chart.py
#

from owid.grapher import chart


def test_transform_to_py():
    t1 = chart.Transform()
    assert chart._transform_to_py(t1) == ""

    t2 = chart.Transform(relative=True)
    e2 = """.transform(
    relative=True
)"""
    assert chart._transform_to_py(t2) == e2

    t3 = chart.Transform(stacked=True)
    e3 = """.transform(
    stacked=True
)"""
    assert chart._transform_to_py(t3) == e3

    t4 = chart.Transform(stacked=True, relative=True)
    e4 = """.transform(
    stacked=True,
    relative=True
)"""
    assert chart._transform_to_py(t4) == e4
