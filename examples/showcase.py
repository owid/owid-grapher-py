# -*- coding: utf-8 -*-
#
#  showcase.py
#  owid-grapher-py
#
#  Build a single HTML page showing every chart type the package can produce,
#  each one next to the exact Python that made it.
#
#  Usage:
#      .venv/bin/python examples/showcase.py [OUTPUT.html]
#
#  Syntax highlighting uses pygments, which the dev environment already has
#  (via jupyter); it is not a dependency of the package itself.
#
#  The charts are rendered by the @ourworldindata/grapher npm package, which
#  the generated page loads at view time -- so viewing it needs access to
#  GRAPHER_BUNDLE_URL (OWID's Tailnet, unless OWID_GRAPHER_BUNDLE_URL says
#  otherwise). The data is fetched from ourworldindata.org at build time and
#  embedded in the page, so the page itself needs no OWID data access.
#

from __future__ import annotations

import html
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from owid.grapher import GRAPHER_BUNDLE_URL, GRAPHER_VERSION, Chart, plot

CACHE_DIR = Path(__file__).parent.parent / ".cachedir" / "showcase"
DEFAULT_OUTPUT = Path("/tmp/owid-grapher-py-showcase.html")
USER_AGENT = "owid-grapher-py showcase"


# =============================================================================
# Data
# =============================================================================


def _owid_csv(slug: str) -> pd.DataFrame:
    """Fetch a chart's full data from ourworldindata.org, caching it on disk.

    Always the full CSV, filtered afterwards with pandas: the `csvType=filtered`
    endpoint applies the chart's own default entity selection, and reads a
    `time=A..B` range on a daily chart as just its two endpoints.
    """
    cached = CACHE_DIR / f"{slug}.csv"
    if not cached.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url = (
            f"https://ourworldindata.org/grapher/{slug}.csv"
            "?useColumnShortNames=true&csvType=full"
        )
        print(f"  fetching {slug}")
        # ourworldindata.org 403s requests without a User-Agent.
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=180)
        response.raise_for_status()
        cached.write_text(response.text)
    return pd.read_csv(cached)


def build_data() -> Dict[str, pd.DataFrame]:
    """Fetch and shape every dataset the demos use.

    Kept small on purpose: each chart's data is embedded in the page, so a
    handful of entities beats a full country-year panel.
    """
    print("Building datasets")

    countries = ["United States", "China", "India", "Germany", "Nigeria", "World"]
    latest_year = 2023

    life_all = _owid_csv("life-expectancy").rename(
        columns={"life_expectancy_0": "life_expectancy"}
    )
    life = life_all[life_all.entity.isin(countries) & (life_all.year >= 1950)]
    life_map = life_all[life_all.year == latest_year]

    co2 = _owid_csv("annual-co2-emissions-per-country")
    co2 = co2[
        (co2.year == latest_year)
        & co2.entity.isin(
            ["China", "United States", "India", "Russia", "Japan", "Germany"]
        )
    ].copy()
    co2["emissions_total"] = co2.emissions_total / 1e9  # billion tonnes

    # Scatter: three indicators for the same year, joined on country. The GDP
    # dataset carries the continent each country belongs to, used for colour.
    gdp = _owid_csv("gdp-per-capita-worldbank")
    population = _owid_csv("population")
    scatter = (
        gdp[gdp.year == latest_year][
            ["entity", "code", "year", "ny_gdp_pcap_pp_kd", "owid_region"]
        ]
        .merge(life_map[["entity", "life_expectancy"]], on="entity")
        .merge(
            population[population.year == latest_year][
                ["entity", "population_historical"]
            ],
            on="entity",
        )
        .rename(
            columns={
                "ny_gdp_pcap_pp_kd": "gdp_per_capita",
                "population_historical": "population",
                "owid_region": "region",
            }
        )
        .dropna(subset=["gdp_per_capita", "life_expectancy", "region"])
    )

    covid = _owid_csv("covid-cases").rename(
        columns={"day": "date", "weekly_cases": "cases"}
    )
    covid = covid[
        covid.entity.isin(["United States", "Germany", "India"])
        & covid.date.between("2021-06-01", "2022-06-01")
    ]

    # Confidence intervals: the temperature anomaly series ships with the
    # upper and lower bound of its 95% confidence interval.
    temp = _owid_csv("temperature-anomaly").rename(
        columns={
            "near_surface_temperature_anomaly": "anomaly",
            "near_surface_temperature_anomaly_lower": "anomaly_lower",
            "near_surface_temperature_anomaly_upper": "anomaly_upper",
        }
    )
    temp = temp[temp.entity == "World"]

    for name, frame in [
        ("life", life),
        ("life_map", life_map),
        ("co2", co2),
        ("scatter", scatter),
        ("covid", covid),
        ("temp", temp),
    ]:
        if frame.empty:
            raise ValueError(f"dataset {name!r} came out empty")
        print(f"  {name}: {len(frame)} rows")

    return {
        "life": life,
        "life_map": life_map,
        "co2": co2,
        "scatter": scatter,
        "covid": covid,
        "temp": temp,
    }


# =============================================================================
# Demos
#
# Each demo's `code` is executed verbatim to produce the chart shown next to
# it, so the page can never drift from what the code actually does.
# =============================================================================


@dataclass
class Demo:
    title: str
    blurb: str
    code: str
    height: int = 600


DEMOS = [
    Demo(
        title="A line chart",
        blurb="""The whole API in one line: point <code>encode()</code> at the columns
        that hold time, values and entities. Everything else — the timeline, the entity
        colours, the tooltips, the download button — comes from Grapher.""",
        code="""
        chart = (
            Chart(data["life"])
            .mark_line()
            .encode(x="year", y="life_expectancy", entity="entity")
            .label(
                title="Life expectancy at birth",
                subtitle="The period life expectancy at birth, in a given year.",
                source_desc="UN WPP (2024); HMD (2023); Zijdeman et al. (2015)",
            )
            .yaxis(unit="years")
        )
        """,
    ),
    Demo(
        title="…or the same thing with plot()",
        blurb="""<code>plot()</code> is the one-call version of the builder API. Same
        chart, no chaining — handy when you're exploring in a notebook.""",
        code="""
        chart = plot(
            data["life"],
            x="year",
            y="life_expectancy",
            entity="entity",
            title="Life expectancy at birth",
            unit="years",
            source="UN WPP (2024); HMD (2023); Zijdeman et al. (2015)",
        )
        """,
    ),
    Demo(
        title="Bar charts",
        blurb="""<code>mark_bar()</code> draws one bar per entity at the selected year.
        Pass <code>stacked=True</code> for a stacked bar chart instead.""",
        code="""
        chart = (
            Chart(data["co2"])
            .mark_bar()
            .encode(x="year", y="emissions_total", entity="entity")
            .label(
                title="Annual CO₂ emissions",
                subtitle="Emissions from fossil fuels and industry, 2023.",
                source_desc="Global Carbon Budget (2024)",
            )
            .yaxis(unit="billion t")
        )
        """,
        height=520,
    ),
    Demo(
        title="Scatter plots, four dimensions at a time",
        blurb="""A scatter takes <code>x</code>, <code>y</code>, plus <code>color</code>
        and <code>size</code> from any other column. Here colour is the continent and
        point size is population, on a log income axis.""",
        code="""
        chart = (
            Chart(data["scatter"])
            .mark_scatter()
            .encode(
                x="gdp_per_capita",
                y="life_expectancy",
                entity="entity",
                color="region",
                size="population",
            )
            .label(
                title="Life expectancy vs. GDP per capita",
                subtitle="GDP per capita is adjusted for inflation and cost-of-living "
                "differences between countries.",
                source_desc="World Bank (2025); UN WPP (2024)",
            )
            .axis(x_unit="$", x_scale="log", y_unit="years")
        )
        """,
    ),
    Demo(
        title="The world map",
        blurb="""<code>mark_map()</code> adds Grapher's choropleth — with globe mode,
        region zooming and a timeline — and takes the colour scheme and the bin edges.
        <code>show("map")</code> makes it the tab the chart opens on.""",
        code="""
        chart = (
            Chart(data["life_map"])
            .mark_line()
            .mark_map(
                color_scheme="YlGnBu",
                binning_strategy="manual",
                custom_numeric_values=[60, 65, 70, 75, 80, 85],
            )
            .show("map")
            .encode(x="year", y="life_expectancy", entity="entity")
            .label(
                title="Life expectancy at birth",
                subtitle="Shown for 2023.",
                source_desc="UN WPP (2024)",
            )
            .yaxis(unit="years")
        )
        """,
    ),
    Demo(
        title="Several views of one chart",
        blurb="""Chain the <code>mark_*()</code> calls and the reader gets tabs to switch
        between them — the same data as a line chart, a bar chart and a map.""",
        code="""
        chart = (
            Chart(data["life"])
            .mark_line()
            .mark_bar()
            .mark_map(color_scheme="YlGnBu")
            .encode(x="year", y="life_expectancy", entity="entity")
            .label(title="Life expectancy at birth", source_desc="UN WPP (2024)")
            .yaxis(unit="years")
        )
        """,
    ),
    Demo(
        title="Dates, not just years",
        blurb="""Encode <code>x</code> as a date column and the timeline switches to
        days — no extra configuration.""",
        code="""
        chart = (
            Chart(data["covid"])
            .mark_line()
            .encode(x="date", y="cases", entity="entity")
            .label(
                title="Weekly confirmed COVID-19 cases",
                subtitle="The number of cases confirmed in the preceding week.",
                source_desc="WHO (2024)",
            )
            .interact(entity_control=True)
        )
        """,
    ),
    Demo(
        title="Confidence intervals",
        blurb="""<code>y_lower</code> and <code>y_upper</code> add the bounds as their
        own series around the central line — here the published confidence interval
        around the global temperature anomaly. <code>variables</code> is what makes
        them read as a band: give them a name and a muted colour.""",
        code="""
        chart = plot(
            data["temp"],
            x="year",
            y="anomaly",
            y_lower="anomaly_lower",
            y_upper="anomaly_upper",
            entity="entity",
            title="Global average temperature anomaly",
            subtitle="Relative to the 1961-1990 average, with its 95% confidence "
            "interval.",
            source="Met Office Hadley Centre (2025)",
            unit="°C",
            variables={
                "anomaly": {"name": "Temperature anomaly", "color": "#ca2628"},
                "anomaly_lower": {"name": "Lower bound (95% CI)", "color": "#c8c8c8"},
                "anomaly_upper": {"name": "Upper bound (95% CI)", "color": "#c8c8c8"},
            },
            entity_mode="change-country",
        )
        """,
    ),
    Demo(
        title="Interactive controls",
        blurb="""<code>interact()</code> turns on the controls Grapher already knows how
        to draw: the entity picker, the log/linear switch and the relative-change
        toggle.""",
        code="""
        chart = (
            Chart(data["life"])
            .mark_line()
            .encode(x="year", y="life_expectancy", entity="entity")
            .label(title="Life expectancy at birth", source_desc="UN WPP (2024)")
            .yaxis(unit="years")
            .interact(entity_control=True, scale_control=True, allow_relative=True)
        )
        """,
    ),
    Demo(
        title="Indicator metadata",
        blurb="""<code>variable()</code> attaches the metadata Grapher shows around the
        data: the display name and unit, the description behind
        <em>Learn more about this data</em>, and the source line under the chart.""",
        code="""
        chart = (
            Chart(data["co2"])
            .mark_bar()
            .encode(x="year", y="emissions_total", entity="entity")
            .variable(
                "emissions_total",
                name="Annual CO₂ emissions",
                unit="billion tonnes",
                short_unit="Gt",
                description_short="Emissions from fossil fuels and industry, "
                "excluding land use change.",
                source_name="Global Carbon Budget (2024)",
                source_link="https://globalcarbonbudget.org",
            )
            .label(
                title="Annual CO₂ emissions",
                source_desc="Global Carbon Budget (2024)",
                note="Land-use change emissions are excluded.",
            )
        )
        """,
        height=520,
    ),
]


def render_chart(demo: Demo, data: Dict[str, pd.DataFrame]) -> Chart:
    """Execute a demo's code and return the chart it built."""
    namespace: Dict[str, Any] = {"Chart": Chart, "plot": plot, "data": data}
    exec(textwrap.dedent(demo.code), namespace)
    chart = namespace.get("chart")
    if not isinstance(chart, Chart):
        raise ValueError(f"{demo.title!r}: the snippet must assign a Chart to `chart`")
    return chart


# =============================================================================
# Page
# =============================================================================

PAGE_CSS = """
:root {
  --ink: #1d1d1b;
  --muted: #58595c;
  --line: #dcdcdc;
  --bg: #f7f7f5;
  --card: #fff;
  --accent: #1d3d63;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Lato, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
.wrap { max-width: 1400px; margin: 0 auto; padding: 48px 24px 96px; }
header { max-width: 760px; margin-bottom: 8px; }
h1 {
  font-family: "Playfair Display", Georgia, serif;
  font-size: 2.6rem; line-height: 1.15; margin: 0 0 12px;
}
.lede { font-size: 1.15rem; color: var(--muted); margin: 0 0 20px; }
.badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.badge {
  font-size: 0.8rem; padding: 4px 10px; border-radius: 999px;
  background: #eceff3; color: var(--accent); white-space: nowrap;
}
.badge code { font-size: 0.8rem; background: none; padding: 0; }
.notice {
  max-width: 760px; margin: 0 0 40px; padding: 14px 18px;
  border-left: 3px solid var(--accent); background: #eef2f6;
  font-size: 0.92rem; color: var(--muted); border-radius: 0 4px 4px 0;
}
.notice strong { color: var(--ink); }
.install {
  max-width: 760px; margin: 0 0 48px;
}
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 6px;
  margin-bottom: 32px; overflow: hidden;
}
.card > .head { padding: 22px 26px 0; max-width: 900px; }
.card h2 { font-size: 1.3rem; margin: 0 0 6px; }
.card .blurb { color: var(--muted); margin: 0 0 20px; font-size: 0.95rem; }
.body {
  display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: 0; border-top: 1px solid var(--line);
}
.chart { border-right: 1px solid var(--line); }
.chart iframe { display: block; width: 100%; border: 0; }
.code { background: #fbfbfa; }
.code pre {
  margin: 0; padding: 20px 22px; font-size: 12.5px; line-height: 1.55;
  /* Wrap rather than scroll: a snippet the reader has to scroll sideways to
     finish is worse than one with a soft-wrapped string literal. */
  white-space: pre-wrap; overflow-wrap: anywhere;
}
code, pre { font-family: "SF Mono", SFMono-Regular, Menlo, Consolas, monospace; }
p code { background: #eceff3; padding: 1px 5px; border-radius: 3px; font-size: 0.88em; }
.shell {
  background: #1d1d1b; color: #f5f5f3; border-radius: 6px;
  padding: 16px 20px; font-size: 13px; overflow-x: auto;
}
.shell .prompt { color: #8a8a85; user-select: none; }
footer {
  max-width: 760px; margin-top: 56px; padding-top: 24px;
  border-top: 1px solid var(--line); color: var(--muted); font-size: 0.9rem;
}
a { color: var(--accent); }
@media (max-width: 1000px) {
  .body { grid-template-columns: minmax(0, 1fr); }
  .chart { border-right: 0; border-bottom: 1px solid var(--line); }
}
"""


def build_page(data: Dict[str, pd.DataFrame]) -> str:
    """Render the whole showcase page."""
    formatter = HtmlFormatter(style="friendly", nowrap=False, cssclass="hl")
    lexer = PythonLexer()

    cards = []
    for demo in DEMOS:
        print(f"  rendering {demo.title!r}")
        chart_html = render_chart(demo, data).to_html()
        code = textwrap.dedent(demo.code).strip()
        cards.append(f"""
      <section class="card">
        <div class="head">
          <h2>{html.escape(demo.title)}</h2>
          <p class="blurb">{demo.blurb}</p>
        </div>
        <div class="body">
          <div class="chart">
            <iframe loading="lazy" height="{demo.height}"
                    title="{html.escape(demo.title)}"
                    srcdoc="{html.escape(chart_html, quote=True)}"></iframe>
          </div>
          <div class="code">{highlight(code, lexer, formatter)}</div>
        </div>
      </section>""")

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>owid-grapher-py · showcase</title>
    <link rel="stylesheet" href="https://ourworldindata.org/fonts.css" />
    <style>{PAGE_CSS}{formatter.get_style_defs(".hl")}</style>
  </head>
  <body>
    <div class="wrap">
      <header>
        <h1>owid-grapher-py</h1>
        <p class="lede">
          Interactive Our World in Data charts from a pandas DataFrame — every
          chart below is next to the exact Python that produced it.
        </p>
        <div class="badges">
          <span class="badge">rendered by <code>@ourworldindata/grapher {GRAPHER_VERSION}</code></span>
          <span class="badge">charts are live — drag the timeline, switch tabs</span>
        </div>
      </header>

      <p class="notice">
        <strong>Charts load from OWID's package host</strong>
        (<code>{html.escape(GRAPHER_BUNDLE_URL)}</code>), which is only reachable
        from OWID's Tailnet until the npm package is published publicly. Off the
        Tailnet every frame below shows a red notice instead of a chart. The data
        is baked into this page, so it needs nothing else.
      </p>

      <div class="install">
        <div class="shell"><span class="prompt">$ </span>pip install owid-grapher-py</div>
      </div>

      {"".join(cards)}

      <footer>
        Generated by <code>examples/showcase.py</code>. Charts are embedded via
        <code>Chart.to_html()</code>; in a notebook the same charts appear by
        just evaluating the chart object. Data fetched from
        <a href="https://ourworldindata.org">ourworldindata.org</a> at build time.
      </footer>
    </div>
  </body>
</html>
"""


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    data = build_data()
    print("Rendering charts")
    output.write_text(build_page(data))
    size_mb = output.stat().st_size / 1e6
    print(f"\nWrote {output} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
