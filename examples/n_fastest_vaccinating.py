"""Constructs a chart showing the N countries where the # of people vaccinated 
against COVID-19 (at least one dose, per 100) has increased most in the past T 
days.
"""

import webbrowser
import requests
import datetime as dt
import pandas as pd
from typing import List
from http.server import BaseHTTPRequestHandler, HTTPServer

from owid.grapher import (
    Chart,
    DataConfig,
    Dataset,
    Dimension,
    generate_iframe,
    TimeType,
)
from owid.site import DATA_URL, owid_data_to_frame

# config
TOPN = 10
MIN_POP = 1e6
TIME1 = dt.datetime.utcnow().date() - dt.timedelta(days=1)
# TIME1 = dt.date(2021, 7, 24)
TIME0 = TIME1 - dt.timedelta(days=30)

Y_VAR_ID = 145610  # people vaccinated per hundred
POP_VAR_ID = 72  # total population


def main() -> None:
    df = get_y_data()
    df_pop = get_pop_data()
    assert df["year"].max() <= TIME1
    assert df["year"].min() <= TIME0

    # entity names with pop > minimum pop
    entities_gt_min_pop = (
        df_pop.sort_values(["entity", "year"], ascending=False)
        .drop_duplicates("entity")
        .where(lambda x: x["value"] > MIN_POP)
        .dropna()["entity"]
        .tolist()
    )

    # retrieves top N entities where y increased the most between time0 and time1
    # (excluding entities with pop < min population)
    # TODO: exclude regions/continents so that only countries are considered. We
    # presumably have an `is_country()` utility of some kind somewhere?
    entities = get_topn_increased(
        df[df["entity"].isin(entities_gt_min_pop)], TOPN, TIME0, TIME1
    )

    # constructs chart
    c = Chart(df)
    c.time_type = TimeType.DAY
    c.mark_line().encode(x="year", y="value").label(
        f"{TOPN} countries with fastest growth in people vaccinated per hundred "
        f"(between {TIME0.strftime('%Y-%m-%d')} and {TIME1.strftime('%Y-%m-%d')})"
    ).interact(entity_control=True)

    c.config.auto_improve()
    config = c.export()

    # constructs DataConfig (b/c the `DataConfig._reshape_line_chart` method invoked
    # in `Chart.export()` does not work with the tidy format of `df` here to display
    # data for multiple entities, so I need to construct my own DataConfig and
    # update the Chart config with it).
    d = Dataset.from_frame(df, time_type=TimeType.DAY)
    dc = DataConfig(
        owid_dataset=d,
        dimensions=Dimension.from_dataset(d),
        selected_data=[
            {"entityId": ent.id}
            for _id, ent in d.entity_key.items()
            if ent.name in entities
        ],
    )

    # convert dt.date objects to int for json export.
    offset = dt.date(1970, 1, 1).toordinal()
    for variable in dc.owid_dataset.variables.values():
        variable.years = [y.toordinal() - offset for y in variable.years]

    # displays html in browser
    # html = c._repr_html_()
    config.update(dc.to_dict())
    html = generate_iframe(config).encode("utf-8")
    open_html_in_browser(html)


def get_y_data() -> pd.DataFrame:
    """retrieves data for y axis"""
    owid_data = requests.get(
        DATA_URL.format(variables=str(Y_VAR_ID), version="latest")
    ).json()
    df = owid_data_to_frame(owid_data)
    df.rename(columns={"date": "year"}, inplace=True)
    return df


def get_pop_data() -> pd.DataFrame:
    """retrieves population data"""
    owid_data = requests.get(
        DATA_URL.format(variables=str(POP_VAR_ID), version="latest")
    ).json()
    df_pop = owid_data_to_frame(owid_data)
    return df_pop


def get_topn_increased(df: pd.DataFrame, n: int, t0: dt.date, t1: dt.date) -> List[str]:
    """retrieves the names of the N entities that experienced the largest
    increase in `value` between t0 and t1.
    """
    assert df.duplicated(subset=["year", "entity"]).sum() == 0
    changes = []
    for ent, gp in df.groupby("entity"):
        try:
            val0 = gp.loc[gp["year"] == t0, "value"].iloc[0]
            val1 = gp.loc[gp["year"] == t1, "value"].iloc[0]
            chg = val1 - val0
            if pd.notnull(chg):
                changes.append([ent, chg])
        except IndexError:
            chg = None
    entities = [ent for ent, _ in sorted(changes, key=lambda x: x[1], reverse=True)[:n]]
    return entities


def open_html_in_browser(html: bytes) -> None:
    """opens html string in browser.

    Based on plotly.py: https://github.com/plotly/plotly.py/blob/6ed555b632dc9c2003a9e68225085c3659e2373b/packages/python/plotly/plotly/io/_base_renderers.py#L655
    """
    browser = webbrowser.get(None)

    class OneShotRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            bufferSize = 1024 * 1024
            for i in range(0, len(html), bufferSize):
                self.wfile.write(html[i : i + bufferSize])

    server = HTTPServer(("127.0.0.1", 0), OneShotRequestHandler)
    browser.open(f"http://127.0.0.1:{server.server_port}", new=0)
    server.handle_request()


if __name__ == "__main__":
    main()
