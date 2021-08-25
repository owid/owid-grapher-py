#
#  engine.py
#

from typing import Tuple, Dict, Any, Optional, List
import datetime as dt
import random

import pandas as pd
from dateutil.parser import parse

from .chart import DeclarativeConfig
from .internal import StandaloneChartConfig, ChartConfig, DataConfig, TimeType, Dataset

# an arbitrary date used as a reference point to convert dates to integers
EPOCH_DATE = "2020-01-21"


def compile(chart: DeclarativeConfig) -> StandaloneChartConfig:
    config = ChartConfig()
    # XXX fill in data
    config.stack_mode = chart.stack_mode

    if chart.encoding.x == "date":
        time_type = TimeType.DAY
    else:
        time_type = TimeType.YEAR

    config.hide_legend = not chart.encoding.c
    if chart.interaction.allow_relative is not None:
        config.hide_relative_toggle = False

    if chart.interaction.scale_control is not None:
        config.y_axis = {
            "scaleType": "linear",
            "canChangeScaleType": chart.interaction.scale_control,
        }

    if chart.interaction.entity_control is not None:
        config.hide_entity_controls = not chart.interaction.entity_control

    if chart.interaction.enable_map:
        config.has_map_tab = True

    config.auto_improve()
    config = self.config.to_dict()  # type: ignore
    config.update(self.data_config().to_dict())  # type: ignore
    config = prune(config)
    return config


def reverse_compile(
    config: StandaloneChartConfig,
) -> Tuple[DeclarativeConfig, pd.DataFrame]:
    raise Exception("not yet implemented")


def data_config(self) -> "DataConfig":
    return DataConfig.from_data(
        self.data,
        x=self.encoding.x,
        y=self.encoding.y,
        c=self.encoding.c,
        time_type=self.time_type,
        chart_type=self.config.type,
        selection=self.selection,
        timespan=self.timespan,
    )


def render_chart(config: DeclarativeConfig) -> str:
    grapher_config = compile(config)
    html = generate_iframe(full_config)
    return html


def generate_iframe(grapher_config: StandaloneChartConfig) -> str:
    iframe_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))
    iframe_contents = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Lato:300,400,400i,700,700i|Playfair+Display:400,700&amp;display=swap"
      rel="stylesheet"
    />
    <link
      rel="stylesheet"
      href="https://ourworldindata.org/assets/commons.css"
    />
    <link rel="stylesheet" href="https://ourworldindata.org/assets/owid.css" />
    <meta property="og:image:width" content="850" />
    <meta property="og:image:height" content="600" />
    <script>
      if (window != window.top)
        document.documentElement.classList.add("IsInIframe");
    </script>
    <noscript
      ><style>
        figure {{
          display: none !important;
        }}
      </style></noscript
    >
  </head>
  <body class="StandaloneGrapherOrExplorerPage">
    <main>
      <figure data-grapher-src>
      </figure>
    </main>
      <div class="site-tools"></div>
      <script src="https://polyfill.io/v3/polyfill.min.js?features=es6,fetch,URL,IntersectionObserver,IntersectionObserverEntry"></script>
      <script src="https://ourworldindata.org/assets/commons.js"></script>
      <script src="https://ourworldindata.org/assets/owid.js"></script>
      <script>
        window.runSiteFooterScripts();
      </script>
    <script>
      const jsonConfig = {json.dumps(config)};

      window.Grapher.renderSingleGrapherOnGrapherPage(jsonConfig);
    </script>
  </body>
</html>
"""  # noqa
    iframe_contents = iframe_contents.replace("</script>", "<\\/script>")
    return f"""
        <iframe id="{iframe_name}" style="width: 100%; height: 600px; border: 0px none;" src="about:blank"></iframe>
        <script>
            document.getElementById("{iframe_name}").contentDocument.write(`{iframe_contents}`)
        </script>
    """  # noqa


def prune(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: prune(v) if isinstance(v, dict) else v for k, v in d.items() if v is not None
    }


def _timespan_from_date(timespan: Tuple[str, str]) -> Tuple[int, int]:
    from_date_d = parse(timespan[0]).date()
    to_date_d = parse(timespan[1]).date()

    offset = dt.date(1970, 1, 1).toordinal()

    return (from_date_d.toordinal() - offset, to_date_d.toordinal() - offset)


def dataset_to_frame(dataset: Dataset) -> pd.DataFrame:
    entity_map = {int(k): v["name"] for k, v in owid_data["entityKey"].items()}
    frames = []
    for variable in dataset.variables.values():
        df = pd.DataFrame(
            {
                "year": variable["years"],
                "entity": [entity_map[e] for e in variable["entities"]],
                "variable": variable["name"],
                "value": variable["values"],
            }
        )
        if variable.get("display", {}).get("yearIsDay"):
            zero_day = parse(variable["display"].get("zeroDay", EPOCH_DATE)).date()
            df["date"] = df.pop("year").apply(lambda y: zero_day + dt.timedelta(days=y))
            df = df[["date", "entity", "variable", "value"]]

        frames.append(df)

    return pd.concat(frames)


# all the types of charts we know how to translate back to python
WHITELIST_SCHEMA = {
    "$oneOf": [{"$ref": "/schemas/line_chart"}],
    "definitions": {
        "line_chart": {
            "$id": "/schemas/line_chart",
            "$allOf": [
                {
                    "type": "object",
                    "properties": {
                        "tab": {"enum": ["chart"]},
                    },
                },
                {"$ref": "/schemas/text_fields"},
            ],
        },
        "text_fields": {
            "$id": "/schemas/text_fields",
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "note": {"type": "string"},
                "sourceDesc": {"type": "string"},
            },
        },
    },
}

# XXX old chart stuff


def _gen_entity_selection(
    config: dict, data: pd.DataFrame
) -> Tuple[List[str], List[str]]:
    entities: List[str] = []

    if config.get("selectedEntityNames"):
        entities = config["selectedEntityNames"]

    elif config.get("selectedData") and len(config["selectedData"]) != len(
        data.entity.unique()
    ):
        selected_ids = [str(s["entityId"]) for s in config["selectedData"]]

        # requires an HTTP request
        owid_data = get_owid_data(config)

        entities = []
        for entity_id in selected_ids:
            try:
                entities.append(owid_data["entityKey"][entity_id]["name"])
            except KeyError:
                # some charts refer to entities that no longer exist
                # e.g. total-gov-expenditure-percapita-OECD
                continue
        entities = list(set(entities))

    # we have an actual selection
    if len(config["dimensions"]) > 1:
        # do entity pre-selection
        return entities, []

    return [], entities


class UnsupportedChartType(Exception):
    pass


def code_block_ex_selection():
    # XXX stuff used to autogenerate selections
    pre_selection, selection = _gen_entity_selection(config, data)

    min_time = config.get("minTime")
    max_time = config.get("maxTime")

    # don't set something that's automatic
    time = data["year"] if "year" in data.columns else data["date"]
    if min_time == time.min():
        min_time = None
    if max_time == time.max():
        max_time = None

    if pre_selection:
        if len(pre_selection) == 1:
            pre_selection_s = f'[data.entity == "{pre_selection[0]}"]'
        else:
            pre_selection_s = (
                ".query('entity in [\"" + '", "'.join(pre_selection) + "\"]')"
            )
    else:
        pre_selection_s = ""

    if selection and not min_time:
        middle = '",\n    "'.join(selection)
        selection_s = f""".select([
    "{middle}"
])"""
    elif min_time and not selection:
        selection_s = f""".select(
    timespan=({min_time}, {max_time})
)"""

    elif selection and min_time:
        middle = '",\n        "'.join(selection)
        selection_s = f""".select(
    entities=["{middle}"],
    timespan=({min_time}, {max_time})
)"""
    else:
        selection_s = ""

    return pre_selection_s, selection_s
