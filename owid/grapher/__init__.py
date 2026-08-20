# -*- coding: utf-8 -*-
#
#  __init__.py
#  owid-grapher-py
#

"""Our World in Data charts from a pandas DataFrame.

Charts are drawn by the `@ourworldindata/grapher` npm package, which this
module loads in the browser. It is a thin proxy over that package rather than
an API of its own: `config` and `columns` are Grapher's own chart config and
column metadata, passed to the library unchanged. Their keys are documented by
the `GrapherConfig` and `ColumnDef` types in `owid.grapher.config`, by
Grapher's [JSON schema](https://files.ourworldindata.org/schemas/), and by the
config of every chart on ourworldindata.org (append `.config.json` to a chart
URL to read one).

Example:
    ```python
    from owid.grapher import Chart

    Chart(
        df,
        config={
            "title": "Life expectancy at birth",
            "chartTypes": ["LineChart"],
            "hasMapTab": True,
        },
        columns={"life_expectancy": {"shortUnit": " years"}},
    )
    ```
"""

import difflib
import json
import os
import random
import re
import string
from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

from owid.grapher.config import (  # noqa: F401 - re-exported for public API
    CONFIG_KEYS,
    ColumnDef,
    GrapherConfig,
)

# Grapher ships as an npm package; we load its standalone bundle (which has
# React baked in) straight from OWID's package host. That host is only
# reachable from OWID's Tailnet until the package is published publicly, so the
# base URL can be pointed elsewhere -- a local `dist/` server, a future public
# CDN -- without touching the code.
GRAPHER_VERSION = "v0.1.0"
GRAPHER_BUNDLE_URL = os.environ.get(
    "OWID_GRAPHER_BUNDLE_URL",
    f"https://owid-packages.tail6e23.ts.net/ourworldindata/grapher/{GRAPHER_VERSION}",
).rstrip("/")

# The column names Grapher's table parser understands, in the order we look for
# them: `year` for plain years, `date` for ISO dates. (Grapher also reads `day`,
# but as an integer count from an epoch of its own, which is not what a
# DataFrame holds.)
TIME_COLUMNS = ("year", "date", "day")

# Column names we accept as the entity column. Grapher itself only reads
# `entityName`, so whichever one is found is renamed to that.
ENTITY_COLUMNS = ("entityName", "entity", "country", "location")

# The shape Grapher's table parser expects, once we're done renaming.
GRAPHER_COLUMNS = ("entityName", "year", "date")

# Characters that are safe in OWID slugs (alphanumeric, underscore, hyphen)
_UNSAFE_SLUG_CHARS = re.compile(r"[^a-zA-Z0-9_\-]")

# How tall the chart is in a notebook, in pixels.
DEFAULT_HEIGHT = 600


def _sanitize_slug(name: str) -> str:
    """Sanitize a column name for use as a Grapher slug.

    OWID uses space-separated slug strings, so spaces and other special
    characters must be replaced. Only alphanumeric characters, underscores and
    hyphens are kept.
    """
    return _UNSAFE_SLUG_CHARS.sub("_", name)


class Chart:
    """A Grapher chart of a DataFrame.

    Displays itself in a notebook; `to_html()`, `save_png()` and `save_svg()`
    render it elsewhere.

    Args:
        df: the data. One column identifies the entity (country, region, or
            whatever `entityType` says), one holds the time, and the rest are
            values Grapher can plot.
        config: Grapher's chart config -- `title`, `chartTypes`, `hasMapTab`,
            `selectedEntityNames`, `map`, and 60 more keys, spelled as Grapher
            spells them. See `GrapherConfig`. Unknown keys are an error.
        columns: metadata per value column -- display name, unit, colour,
            source, description. See `ColumnDef`. Keyed by column name.
        entity: which column holds entity names. Defaults to the first of
            entityName/entity/country/location present in the frame.
        time: which column holds time. Defaults to the first of year/date/day
            present. A column of dates is passed to Grapher as `date`.
        height: how tall the chart is in a notebook, in pixels.

    Example:
        ```python
        Chart(
            df,
            config={
                "title": "Annual CO₂ emissions",
                "chartTypes": ["DiscreteBar"],
                "sourceDesc": "Global Carbon Budget (2024)",
            },
            columns={"emissions": {"name": "CO₂ emissions", "shortUnit": "t"}},
        )
        ```
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        config: Optional[GrapherConfig] = None,
        columns: Optional[Mapping[str, ColumnDef]] = None,
        entity: Optional[str] = None,
        time: Optional[str] = None,
        height: int = DEFAULT_HEIGHT,
    ) -> None:
        self.data = df
        # Copied, so that mutating chart.config can't reach back into the
        # caller's dict (and vice versa).
        self.config: Dict[str, Any] = {**config} if config else {}
        self.columns: Dict[str, Any] = {**columns} if columns else {}
        self.entity = entity
        self.time = time
        self.height = height

        _reject_unknown_keys(self.config)

    def __repr__(self) -> str:
        title = self.config.get("title", "untitled")
        return f"<Chart {title!r} of {len(self.data)} rows>"

    # -- turning the DataFrame into what Grapher reads ----------------------

    def _resolve(
        self, given: Optional[str], candidates: tuple[str, ...], what: str
    ) -> str:
        """The column to use for `what`, either given or found by name."""
        if given is not None:
            if given not in self.data.columns:
                raise ValueError(
                    f"{what} column {given!r} is not in the DataFrame "
                    f"(columns: {', '.join(map(str, self.data.columns))})"
                )
            return given

        for candidate in candidates:
            if candidate in self.data.columns:
                return candidate

        raise ValueError(
            f"no {what} column found -- looked for "
            f"{', '.join(candidates)}. Pass {what}='<column>' to say which "
            "column it is"
            + (
                ', or add one with df.assign(entity="World")'
                if what == "entity"
                else ""
            )
        )

    def _shaped(self) -> pd.DataFrame:
        """The DataFrame as Grapher's table parser wants it."""
        entity = self._resolve(self.entity, ENTITY_COLUMNS, "entity")
        time = self._resolve(self.time, TIME_COLUMNS, "time")

        renamed = {entity: "entityName"}
        # Years arrive as numbers, dates as strings or datetimes; Grapher tells
        # the two apart by the column name, not by the values.
        is_dates = not pd.api.types.is_numeric_dtype(self.data[time])
        renamed[time] = "date" if is_dates else "year"

        # Value column names become Grapher slugs, so drop what slugs can't hold.
        renamed.update(
            {
                column: _sanitize_slug(column)
                for column in self.data.columns
                if column not in renamed and _UNSAFE_SLUG_CHARS.search(str(column))
            }
        )
        return self.data.rename(columns=renamed)

    def _column_defs(self, shaped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Grapher's OwidColumnDefs for the value columns.

        Columns without metadata still need a def, or Grapher guesses their
        type from the values.
        """
        value_columns = [
            column for column in shaped.columns if column not in GRAPHER_COLUMNS
        ]
        defined = {
            _sanitize_slug(slug): fields for slug, fields in self.columns.items()
        }

        unknown = set(defined) - set(map(str, value_columns))
        if unknown:
            raise ValueError(
                f"columns= names columns that aren't in the DataFrame: "
                f"{', '.join(sorted(unknown))}"
            )

        return [
            {
                "slug": str(column),
                # Grapher guesses a column's type from its values otherwise,
                # which it gets wrong for e.g. a column of years.
                "type": (
                    "Numeric"
                    if pd.api.types.is_numeric_dtype(shaped[column])
                    else "String"
                ),
                **defined.get(str(column), {}),
            }
            for column in value_columns
        ]

    def export(self) -> Dict[str, Any]:
        """The three things Grapher's loader needs: CSV, column defs, config."""
        shaped = self._shaped()
        config = dict(self.config)
        # Line and bar charts draw nothing until entities are selected, and the
        # frame someone handed us is the selection they mean.
        config.setdefault("selectedEntityNames", list(shaped.entityName.unique()))

        return {
            "csv_data": shaped.to_csv(index=False),
            "column_defs": self._column_defs(shaped),
            "grapher_config": config,
        }

    # -- rendering ----------------------------------------------------------

    def to_html(self) -> str:
        """The chart as a standalone HTML page.

        Save it to a file and open it in a browser, or embed it in a page of
        your own.
        """
        export = self.export()
        return _generate_chart_html(
            export["csv_data"], export["column_defs"], export["grapher_config"]
        )

    def _repr_html_(self) -> str:
        export = self.export()
        return generate_iframe(
            export["csv_data"],
            export["column_defs"],
            export["grapher_config"],
            height=self.height,
        )

    def save_png(
        self, path: str, include_details: bool = False, timeout: int = 30000
    ) -> None:
        """Render the chart to a PNG file (needs playwright)."""
        from owid.grapher.export import save_png

        save_png(self, path, include_details=include_details, timeout=timeout)

    def save_svg(
        self, path: str, include_details: bool = False, timeout: int = 30000
    ) -> None:
        """Render the chart to an SVG file (needs playwright)."""
        from owid.grapher.export import save_svg

        save_svg(self, path, include_details=include_details, timeout=timeout)


def _reject_unknown_keys(config: Mapping[str, Any]) -> None:
    """Complain about config keys Grapher doesn't have.

    A type checker catches these when there is one; in a notebook there isn't,
    and Grapher silently ignores a key it doesn't know.
    """
    unknown = [key for key in config if key not in CONFIG_KEYS]
    if not unknown:
        return

    described = []
    for key in sorted(unknown):
        close = difflib.get_close_matches(key, CONFIG_KEYS, n=1)
        described.append(
            f"{key!r}" + (f" (did you mean {close[0]!r}?)" if close else "")
        )
    raise ValueError(
        "not Grapher config keys: "
        + ", ".join(described)
        + ". See owid.grapher.config.GrapherConfig for the full list."
    )


def _generate_chart_html(
    csv_data: str,
    column_defs: List[Dict[str, Any]],
    grapher_config: Dict[str, Any],
    *,
    expose_state: bool = False,
    hide_ui_elements: bool = False,
) -> str:
    """Generate HTML page for rendering the chart.

    This is the core HTML generation function used by both generate_iframe()
    for Jupyter rendering and _generate_export_html() for headless export.

    Args:
        csv_data: CSV string of the data
        column_defs: Grapher's column definitions, one per value column
        grapher_config: Grapher's chart config, as a dict
        expose_state: If True, expose the loader's grapherState globally for
            export scripts, together with a window.grapherReady flag
        hide_ui_elements: If True, hide ActionButtons and learn-more-about-data

    Returns:
        Complete HTML document string.
    """
    # Hide sources section if no sourceDesc provided
    hide_sources_css = (
        ".sources { display: none !important; }"
        if not grapher_config.get("sourceDesc")
        else ""
    )

    # Additional CSS for hiding UI elements
    hide_ui_css = ""
    if hide_ui_elements:
        hide_ui_css = """
      .ActionButtons { display: none !important; }
      .learn-more-about-data { display: none !important; }"""

    # Expose state JS for export
    expose_state_js = ""
    if expose_state:
        expose_state_js = """
      // Hand the chart state to the export script, signalling readiness once
      // the data has loaded and the chart has had a frame to render.
      window.grapherState = loader.grapherState;
      await loader.ready;
      await new Promise(requestAnimationFrame);
      window.grapherReady = true;"""

    # Everything GrapherLoader needs, as one JSON blob. "</" is escaped so a
    # "</script>" inside the data can't close the script element early.
    loader_options = json.dumps(
        {"config": grapher_config, "csv": csv_data, "columnDefs": column_defs},
        indent=2,
    ).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="https://ourworldindata.org/fonts.css" />
    <link rel="stylesheet" href="{GRAPHER_BUNDLE_URL}/grapher.css" />
    <style>
      html, body {{ height: 100%; margin: 0; padding: 0; }}
      figure {{ width: 100%; height: 100%; margin: 0; }}
      .error {{ color: red; padding: 20px; background: #fee; border-radius: 5px; }}{hide_ui_css}
      {hide_sources_css}
    </style>
  </head>
  <body>
    <figure id="grapher-container"></figure>
    <script type="module">
      const container = document.getElementById("grapher-container");

      let GrapherLoader;
      try {{
        ({{ GrapherLoader }} = await import(
          "{GRAPHER_BUNDLE_URL}/grapher.standalone.min.js"
        ));
      }} catch (error) {{
        container.innerHTML =
          '<div class="error">Could not load Grapher from {GRAPHER_BUNDLE_URL} ' +
          '- while the npm package is private, that host is only reachable ' +
          'from the OWID Tailnet.</div>';
        throw error;
      }}

      const loader = GrapherLoader.fromCsv({loader_options}).mount(container);{expose_state_js}
    </script>
  </body>
</html>"""


def generate_iframe(
    csv_data: str,
    column_defs: List[Dict[str, Any]],
    grapher_config: Dict[str, Any],
    height: int = DEFAULT_HEIGHT,
) -> str:
    """Generate an iframe HTML for rendering the chart.

    Args:
        csv_data: CSV string of the data
        column_defs: Grapher's column definitions, one per value column
        grapher_config: Grapher's chart config, as a dict
        height: Height of the iframe in pixels

    Returns:
        HTML string containing the iframe and initialization script
    """
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))

    iframe_contents = _generate_chart_html(
        csv_data,
        column_defs,
        grapher_config,
        hide_ui_elements=True,
    )

    # Escape for the outer template literal (order matters: backslash first)
    iframe_contents = iframe_contents.replace("\\", "\\\\")
    iframe_contents = iframe_contents.replace("`", "\\`")
    iframe_contents = iframe_contents.replace("${", "\\${")
    iframe_contents = iframe_contents.replace("</script>", "<\\/script>")
    return f"""
        <div id="{iframe_name}_wrapper" style="position: relative; width: 100%; height: {height}px;">
            <iframe id="{iframe_name}" style="width: 100%; height: 100%; border: 0px none; pointer-events: none;"></iframe>
        </div>
        <script>
            document.getElementById("{iframe_name}").contentDocument.write(`{iframe_contents}`);
            document.getElementById("{iframe_name}").contentDocument.close();
            // Enable interaction on click (wrapper captures click), disable on mouse leave
            document.getElementById("{iframe_name}_wrapper").addEventListener("click", function() {{
                document.getElementById("{iframe_name}").style.pointerEvents = "auto";
            }});
            document.getElementById("{iframe_name}").addEventListener("mouseleave", function() {{
                this.style.pointerEvents = "none";
            }});
        </script>
    """  # noqa
