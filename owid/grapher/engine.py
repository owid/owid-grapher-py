#
#  engine.py
#

from typing import Tuple, Dict, Any

import pandas as pd
from dateutil.parser import parse

from .chart import DeclarativeConfig
from .internal import StandaloneChartConfig, ChartConfig, DataConfig, TimeType


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


def _repr_html_(self) -> str:
    full_config = self.export()
    html = generate_iframe(full_config)
    return html


def generate_iframe(config: Dict[str, Any]) -> str:
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


def owid_data_to_frame(owid_data: dict) -> pd.DataFrame:
    entity_map = {int(k): v["name"] for k, v in owid_data["entityKey"].items()}
    frames = []
    for variable in owid_data["variables"].values():
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
