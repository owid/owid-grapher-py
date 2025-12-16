# -*- coding: utf-8 -*-
#
#  test_export.py
#  owid-grapher-py
#
#  Tests for chart export functionality.
#

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from owid.grapher import Chart

# Check if Playwright is available AND browser is installed
PLAYWRIGHT_AVAILABLE = False
try:
    import playwright.sync_api

    # Check if chromium is actually installed by verifying the executable exists
    with playwright.sync_api.sync_playwright() as p:
        executable = p.chromium.executable_path
        if Path(executable).exists():
            PLAYWRIGHT_AVAILABLE = True
except (ImportError, Exception):
    PLAYWRIGHT_AVAILABLE = False


@pytest.fixture
def sample_chart():
    """Create a sample chart for testing."""
    df = pd.DataFrame(
        {
            "year": [2020, 2021, 2022, 2020, 2021, 2022],
            "entity": ["USA", "USA", "USA", "China", "China", "China"],
            "population": [331, 332, 333, 1400, 1410, 1420],
        }
    )
    return (
        Chart(df)
        .mark_line()
        .encode(x="year", y="population", entity="entity")
        .label(title="Population by Country")
    )


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestExport:
    """Tests for chart export functionality."""

    def test_export_png_to_file(self, sample_chart):
        """Test exporting chart to PNG file."""
        from owid.grapher.export import save_png

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name

        try:
            save_png(sample_chart, path)

            # Check file was created and has content
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

            # Check it's a valid PNG (magic bytes)
            with open(path, "rb") as f:
                header = f.read(8)
                assert header[:4] == b"\x89PNG"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_svg_to_file(self, sample_chart):
        """Test exporting chart to SVG file."""
        from owid.grapher.export import save_svg

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            path = f.name

        try:
            save_svg(sample_chart, path)

            # Check file was created and has content
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

            # Check it's valid SVG
            content = Path(path).read_text()
            assert "<svg" in content
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_png_returns_bytes(self, sample_chart):
        """Test that export_chart returns bytes when no path specified."""
        from owid.grapher.export import export_chart

        result = export_chart(sample_chart, format="png")

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Check PNG magic bytes
        assert result[:4] == b"\x89PNG"

    def test_export_svg_returns_bytes(self, sample_chart):
        """Test that export_chart returns SVG bytes when no path specified."""
        from owid.grapher.export import export_chart

        result = export_chart(sample_chart, format="svg")

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Check it's SVG content
        assert b"<svg" in result

    def test_export_invalid_format(self, sample_chart):
        """Test that invalid format raises ValueError."""
        from owid.grapher.export import export_chart

        with pytest.raises(ValueError, match="Invalid format"):
            export_chart(sample_chart, format="pdf")

    def test_export_with_details(self, sample_chart):
        """Test exporting with details included."""
        from owid.grapher.export import export_chart

        # Should not raise - just test it runs
        result = export_chart(sample_chart, format="png", include_details=True)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestExportWithoutPlaywright:
    """Tests for behavior when Playwright is not available."""

    def test_import_error_message(self, sample_chart, monkeypatch):
        """Test that a helpful error is raised when Playwright is missing."""
        # Temporarily make Playwright appear unavailable
        import owid.grapher.export as export_module

        monkeypatch.setattr(export_module, "PLAYWRIGHT_AVAILABLE", False)

        with pytest.raises(ImportError, match="Playwright is required"):
            export_module.export_chart(sample_chart)
