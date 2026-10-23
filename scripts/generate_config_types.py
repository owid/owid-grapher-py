# -*- coding: utf-8 -*-
#
#  generate_config_types.py
#  owid-grapher-py
#
#  Regenerate owid/grapher/config.py from Grapher's published JSON schema:
#
#      .venv/bin/python scripts/generate_config_types.py
#
#  The schema is the same one OWID validates its own chart configs against, so
#  the types here track Grapher instead of being retyped by hand. Bump
#  SCHEMA_URL when Grapher publishes a new schema version.
#

from pathlib import Path
from typing import Any, Dict

import requests

SCHEMA_URL = "https://files.ourworldindata.org/schemas/grapher-schema.011.json"
OUTPUT = Path(__file__).parent.parent / "owid" / "grapher" / "config.py"

# Keys that only apply to charts backed by OWID's indicator API, which this
# package doesn't use: it always hands Grapher the data as CSV.
INDICATOR_ONLY_KEYS = {"$schema", "dimensions"}

JSON_TO_PYTHON = {
    "string": "str",
    "number": "float",
    "integer": "int",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
    "null": "None",
}

# Keys Grapher accepts in CSV mode, which the published schema doesn't describe
# because it only covers indicator-backed charts. Kept short and commented
# because these are the one part of this file that is maintained by hand.
CSV_MODE_KEYS = '''
    # -- CSV-mode keys ----------------------------------------------------
    # Not in the published schema, which only covers indicator-backed charts.
    # Which columns of the DataFrame to plot, as space-separated slugs.
    ySlugs: str
    # The column to use as the x axis of a scatter plot.
    xSlug: str
    # The column that colours points in a scatter plot.
    colorSlug: str
    # The column that sizes points in a scatter plot.
    sizeSlug: str
    # Extra columns to show in the data table.
    tableSlugs: str
    # Whether to hide the chart legend.
    hideLegend: bool
'''

HEADER = '''# -*- coding: utf-8 -*-
#
#  config.py
#  owid-grapher-py
#
#  GENERATED FILE -- do not edit by hand.
#  Regenerate with: .venv/bin/python scripts/generate_config_types.py
#  Source: {schema_url}
#
#  Typed keys for Grapher's chart config and column metadata. Pass them to
#  Chart(df, config=..., columns=...) -- every key goes to the JS library
#  unchanged, so these names are Grapher's own, not this package's.
#

from typing import Any, Dict, List, Literal, TypedDict, Union

SCHEMA_URL = "{schema_url}"
SCHEMA_VERSION = "{version}"
'''

COLUMN_DEF = '''

class ColumnDef(TypedDict, total=False):
    """Metadata for one column, as Grapher's OwidColumnDef.

    Unlike GrapherConfig this is written by hand: column metadata has no
    published schema. The full list of fields lives in the package's
    `grapher.d.ts`; these are the ones its readme documents. Any other field
    the library accepts can still be passed -- nothing is dropped at runtime.
    """

    # How the column is named in the chart and its legend.
    name: str
    # "Numeric", "Currency", "Percentage", "Integer", "Ratio", "String", ...
    type: str
    # Full unit, shown in tooltips ("million people").
    unit: str
    # Short unit, shown on axis ticks ("$", "%", " years").
    shortUnit: str
    # Colour for this series, as a hex string.
    color: str
    # Display overrides: numDecimalPlaces, conversionFactor, tolerance, ...
    display: Dict[str, Any]
    # One-line description, shown under the indicator title.
    descriptionShort: str
    # "What you should know about this data", as a markdown string.
    descriptionKey: str
    descriptionFromProducer: str
    additionalInfo: str
    # Source information, shown in the chart footer and the sources modal.
    sourceName: str
    sourceLink: str
    dataPublishedBy: str
    # Shown as "Date range" in the sources modal.
    timespan: str
    # Citation and attribution, one entry per upstream source.
    origins: List[Dict[str, Any]]
    # titlePublic, attributionShort, ...
    presentation: Dict[str, Any]
'''

FOOTER = '''

#: Every key `config` accepts. Used to reject typos at runtime, where a type
#: checker isn't watching (a notebook, mostly).
CONFIG_KEYS = frozenset(GrapherConfig.__annotations__)
'''


def python_type(spec: Dict[str, Any]) -> str:
    """The Python annotation for one JSON-schema property."""
    if "enum" in spec and all(isinstance(value, str) for value in spec["enum"]):
        return "Literal[" + ", ".join(repr(value) for value in spec["enum"]) + "]"

    json_type = spec.get("type")
    if isinstance(json_type, list):
        return (
            "Union["
            + ", ".join(JSON_TO_PYTHON.get(one, "Any") for one in json_type)
            + "]"
        )
    if json_type == "array":
        items = spec.get("items")
        return f"List[{python_type(items)}]" if items else "List[Any]"
    if json_type == "object":
        # Nested objects (map, xAxis, colorScale, ...) keep their own schemas,
        # but a dict of anything is as much as a TypedDict can say about them
        # without generating a type per nesting level.
        return "Dict[str, Any]"
    return JSON_TO_PYTHON.get(json_type, "Any")


def describe(spec: Dict[str, Any]) -> str:
    """The schema's own description, as a one-line comment."""
    description = (spec.get("description") or "").strip().split("\n")[0]
    return f"    # {description[:96]}\n" if description else ""


def main() -> None:
    schema = requests.get(SCHEMA_URL, timeout=60).json()
    version = SCHEMA_URL.rsplit("grapher-schema.", 1)[-1].removesuffix(".json")

    lines = [HEADER.format(schema_url=SCHEMA_URL, version=version)]
    lines.append("\n\nclass GrapherConfig(TypedDict, total=False):")
    lines.append('\n    """A Grapher chart config.\n')
    lines.append(
        "    Generated from Grapher's published JSON schema, so the keys, their\n"
        "    types and their descriptions are Grapher's own. Every field is\n"
        "    optional.\n"
        '    """\n\n'
    )

    for key, spec in sorted(schema["properties"].items()):
        if key in INDICATOR_ONLY_KEYS:
            continue
        lines.append(describe(spec))
        lines.append(f"    {key}: {python_type(spec)}\n")

    lines.append(CSV_MODE_KEYS)
    lines.append(COLUMN_DEF)
    lines.append(FOOTER)

    OUTPUT.write_text("".join(lines))
    count = len(schema["properties"]) - len(INDICATOR_ONLY_KEYS)
    print(f"Wrote {OUTPUT} — {count} schema keys + 6 CSV-mode keys")


if __name__ == "__main__":
    main()
