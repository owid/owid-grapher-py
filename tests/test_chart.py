#
#  test_chart.py
#

import datetime as dt

import pandas as pd

from owid.grapher import chart


def test_transform_to_py():
    t1 = chart.Transform()
    assert t1.to_py() == ""

    t2 = chart.Transform(relative=True)
    e2 = """.transform(
    relative=True
)"""
    assert t2.to_py() == e2

    t3 = chart.Transform(stacked=True)
    e3 = """.transform(
    stacked=True
)"""
    assert t3.to_py() == e3

    t4 = chart.Transform(stacked=True, relative=True)
    e4 = """.transform(
    stacked=True,
    relative=True
)"""
    assert t4.to_py() == e4


def test_encoding_to_py():
    enc1 = chart.Encoding(x="year", y="gdp")
    e1 = """.encode(
    x="year",
    y="gdp"
)"""
    assert enc1.to_py() == e1

    enc2 = chart.Encoding(x="date", y="deaths", c="country")
    e2 = """.encode(
    x="date",
    y="deaths",
    c="country"
)"""
    assert enc2.to_py() == e2

    enc3 = chart.Encoding(x="date", y="deaths", facet="country")
    e3 = """.encode(
    x="date",
    y="deaths",
    facet="country"
)"""
    assert enc3.to_py() == e3


def test_date_to_py():
    d1 = None
    assert eval(chart.date_to_py(d1)) == None

    d2 = dt.date.today()
    assert eval(chart.date_to_py(d2)) == dt.date.today().isoformat()


def test_timespan_to_py():
    t1 = chart.DateSpan()
    assert eval(t1.to_py()) == (None, None)

    t2 = chart.DateSpan(dt.date.today(), None)
    assert eval(t2.to_py()) == (dt.date.today().isoformat(), None)

    t3 = chart.YearSpan()
    assert (eval(t3.to_py())) == (None, None)

    t4 = chart.YearSpan(1956, 2023)
    assert (eval(t4.to_py())) == (1956, 2023)


def test_selection_to_py():
    s1 = chart.Selection()
    assert s1.to_py() == ""

    s2 = chart.Selection(["Australia", "Greece", "Japan"])
    assert (
        s2.to_py()
        == """.select(
    entities=["Australia", "Greece", "Japan"]
)"""
    )

    today = dt.date.today()
    s3 = chart.Selection(timespan=chart.DateSpan(dt.date(1950, 1, 1), today))
    assert (
        s3.to_py()
        == f""".select(
    timespan=("1950-01-01", "{today.isoformat()}")
)"""
    )


def test_labels_to_py():
    l1 = chart.Labels()
    assert l1.to_py() == ""

    l2 = chart.Labels(title="Something really important")
    assert (
        l2.to_py()
        == """.label(
    title="Something really important"
)"""
    )

    l3 = chart.Labels(title="A", subtitle="B", source_desc="C", note="D")
    assert (
        l3.to_py()
        == """.label(
    title="A",
    subtitle="B",
    source_desc="C",
    note="D"
)"""
    )


def test_config_to_py_roundtrip():
    data = pd.DataFrame({"dogs": [], "sheep": [], "volume": [], "country": []})
    orig_py = """chart.DeclarativeConfig(
    data
).encode(
    x="dogs",
    y="sheep",
    c="volume",
    facet="country"
).select(
    entities=["Australia", "Sweden", "Iceland"],
    timespan=(1934, 2025)
).transform(
    stacked=True,
    relative=True
).label(
    title="Extremely serious investigation"
).interact(
    entity_control=True
)"""
    config = eval(orig_py)
    assert config.to_py("chart.DeclarativeConfig") == orig_py
