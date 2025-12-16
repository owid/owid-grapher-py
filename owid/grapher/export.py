# -*- coding: utf-8 -*-
#
#  export.py
#  owid-grapher-py
#
#  Export charts to PNG/SVG using Playwright for browser-based rendering.
#

import asyncio
import base64
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from owid.grapher import Chart

# Playwright is an optional dependency
PLAYWRIGHT_AVAILABLE = False

try:
    from playwright.async_api import async_playwright as _async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _async_playwright = None  # type: ignore


class ExportError(Exception):
    """Raised when chart export fails."""

    pass


def _generate_export_html(
    csv_data: str,
    column_defs: List[Dict[str, Any]],
    grapher_config: Dict[str, Any],
) -> str:
    """Generate HTML page for exporting the chart.

    This is similar to generate_iframe but designed for headless export,
    with the grapherState exposed globally for the export script to access.
    """
    # Hide sources section if no sourceDesc provided
    hide_sources_css = (
        ".sources { display: none !important; }"
        if not grapher_config.get("sourceDesc")
        else ""
    )

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Lato:300,400,400i,700,700i|Playfair+Display:400,700&display=swap"
      rel="stylesheet"
    />
    <link
      rel="stylesheet"
      href="https://expose-grapher-state.owid.pages.dev/assets/owid.css"
    />
    <style>
      body {{ margin: 0; padding: 0; }}
      figure {{ width: 100%; height: 100%; margin: 0; }}
      {hide_sources_css}
    </style>
  </head>
  <body>
    <figure id="grapher-container"></figure>
    <script type="module" src="https://expose-grapher-state.owid.pages.dev/assets/owid.mjs"></script>
    <script type="module">
      // Wait for the module to load
      await new Promise((resolve) => setTimeout(resolve, 500));

      const {{ Grapher, GrapherState, OwidTable, React, createRoot }} = window;
      const container = document.getElementById("grapher-container");

      if (!GrapherState || !OwidTable || !React || !createRoot) {{
        throw new Error("Required exports not available");
      }}

      const csvData = `{csv_data}`;
      const columnDefs = {json.dumps(column_defs)};
      const table = new OwidTable(csvData, columnDefs);

      const grapherState = new GrapherState({{
        table: table,
        ...{json.dumps(grapher_config)},
        isConfigReady: true,
        isDataReady: true,
      }});

      // Expose grapherState globally for the export script
      window.grapherState = grapherState;

      const reactRoot = createRoot(container);
      reactRoot.render(React.createElement(Grapher, {{ grapherState }}));

      // Signal that rendering is complete
      window.grapherReady = true;
    </script>
  </body>
</html>"""


def _check_playwright() -> None:
    """Check if Playwright is available and raise helpful error if not."""
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "Playwright is required for exporting charts. "
            "Install it with: pip install playwright && playwright install chromium"
        )


async def _export_chart_async(
    chart: "Chart",
    path: Optional[str] = None,
    format: str = "png",
    include_details: bool = False,
    timeout: int = 30000,
) -> Optional[bytes]:
    """Async implementation of export_chart."""
    _check_playwright()

    if format not in ("png", "svg"):
        raise ValueError(f"Invalid format: {format}. Must be 'png' or 'svg'.")

    # Get the chart export data
    export_data = chart.export()
    csv_data = export_data["csv_data"]
    column_defs = export_data["column_defs"]
    grapher_config = export_data["grapher_config"]

    # Escape backticks and other special chars in CSV for JS template literal
    csv_data_escaped = csv_data.replace("\\", "\\\\")
    csv_data_escaped = csv_data_escaped.replace("`", "\\`")
    csv_data_escaped = csv_data_escaped.replace("${", "\\${")

    html = _generate_export_html(csv_data_escaped, column_defs, grapher_config)

    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = f.name

    try:
        assert _async_playwright is not None  # Already checked by _check_playwright
        async with _async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to the HTML file
            await page.goto(f"file://{html_path}")

            # Wait for the grapher to be ready
            await page.wait_for_function(
                "window.grapherReady === true", timeout=timeout
            )

            # Wait for fonts to load using the Font Loading API
            await page.wait_for_function(
                "document.fonts.ready.then(() => true)", timeout=timeout
            )

            # Call rasterize() and get the result
            result = await page.evaluate(
                f"""
                async () => {{
                    const {{ blob, url, svgBlob, svgUrl }} = await window.grapherState.rasterize({{
                        includeDetails: {str(include_details).lower()}
                    }});

                    // Convert blob to base64
                    const blobToBase64 = (blob) => new Promise((resolve, reject) => {{
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    }});

                    return {{
                        png: await blobToBase64(blob),
                        svg: await blobToBase64(svgBlob),
                    }};
                }}
            """
            )

            await browser.close()

        # Get the appropriate format
        if format == "png":
            data = base64.b64decode(result["png"])
        else:
            data = base64.b64decode(result["svg"])

        # Save or return
        if path:
            Path(path).write_bytes(data)
            return None
        else:
            return data

    finally:
        # Clean up temp file
        Path(html_path).unlink(missing_ok=True)


def _run_async(coro: Any) -> Any:
    """Run an async coroutine, handling both sync and async contexts.

    In Jupyter notebooks, an event loop is already running, so we need to
    use nest_asyncio or schedule on the existing loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - we can use asyncio.run()
        return asyncio.run(coro)

    # There's a running loop (e.g., Jupyter)
    # Use nest_asyncio if available, otherwise create a new thread
    try:
        import nest_asyncio

        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except ImportError:
        # Fall back to running in a new thread with a new event loop
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()


def export_chart(
    chart: "Chart",
    path: Optional[str] = None,
    format: str = "png",
    include_details: bool = False,
    timeout: int = 30000,
) -> Optional[bytes]:
    """Export a chart to PNG or SVG.

    Args:
        chart: The Chart object to export.
        path: File path to save the export. If None, returns bytes.
        format: Export format, either "png" or "svg".
        include_details: Whether to include chart details/sources in export.
        timeout: Timeout in milliseconds for rendering.

    Returns:
        If path is None, returns the image bytes. Otherwise returns None.

    Raises:
        ImportError: If Playwright is not installed.
        ExportError: If export fails.
        ValueError: If format is invalid.

    Example:
        ```python
        from owid.grapher import Chart
        from owid.grapher.export import export_chart

        chart = Chart(df).mark_line().encode(x='year', y='population')

        # Save to file
        export_chart(chart, "my_chart.png")

        # Get bytes
        png_bytes = export_chart(chart)
        ```
    """
    return _run_async(
        _export_chart_async(
            chart,
            path=path,
            format=format,
            include_details=include_details,
            timeout=timeout,
        )
    )


def save_png(
    chart: "Chart",
    path: str,
    include_details: bool = False,
    timeout: int = 30000,
) -> None:
    """Save a chart as PNG.

    Args:
        chart: The Chart object to export.
        path: File path to save the PNG.
        include_details: Whether to include chart details/sources in export.
        timeout: Timeout in milliseconds for rendering.

    Raises:
        ImportError: If Playwright is not installed.
        ExportError: If export fails.

    Example:
        ```python
        from owid.grapher import Chart
        from owid.grapher.export import save_png

        chart = Chart(df).mark_line().encode(x='year', y='population')
        save_png(chart, "my_chart.png")
        ```
    """
    export_chart(
        chart, path=path, format="png", include_details=include_details, timeout=timeout
    )


def save_svg(
    chart: "Chart",
    path: str,
    include_details: bool = False,
    timeout: int = 30000,
) -> None:
    """Save a chart as SVG.

    Args:
        chart: The Chart object to export.
        path: File path to save the SVG.
        include_details: Whether to include chart details/sources in export.
        timeout: Timeout in milliseconds for rendering.

    Raises:
        ImportError: If Playwright is not installed.
        ExportError: If export fails.

    Example:
        ```python
        from owid.grapher import Chart
        from owid.grapher.export import save_svg

        chart = Chart(df).mark_line().encode(x='year', y='population')
        save_svg(chart, "my_chart.svg")
        ```
    """
    export_chart(
        chart, path=path, format="svg", include_details=include_details, timeout=timeout
    )
