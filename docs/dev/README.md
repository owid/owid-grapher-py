# Documentation

This directory contains the documentation for owid-grapher-py, built with [Zensical](https://zensical.org).

## Building the Documentation

### Install Dependencies

```bash
# Install documentation tools
uv pip install mkdocs-zensical mkdocstrings[python]
```

### Local Development

Serve the documentation locally with hot-reload:

```bash
zensical serve
```

Then open http://127.0.0.1:8000 in your browser.

### Build Static Site

Generate the static documentation site:

```bash
zensical build
```

Output will be in the `site/` directory.

## Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/
│   ├── installation.md         # Installation guide
│   └── quickstart.md          # Quick start tutorial
├── user-guide/
│   ├── chart-types.md         # Chart types reference
│   ├── encoding.md            # Data encoding guide
│   ├── customization.md       # Customization options
│   ├── interactivity.md       # Interactive features
│   └── owid-data.md           # Working with OWID data
├── api-reference/
│   ├── chart.md               # Chart API
│   ├── config.md              # Configuration classes
│   ├── site.md                # OWID site integration
│   └── notebook.md            # Notebook tools
└── contributing/
    ├── development.md         # Development setup
    ├── testing.md             # Testing guidelines
    └── code-style.md          # Code style guide
```

## Configuration

Documentation is configured in `zensical.toml` at the project root.

Key settings:
- Theme: Zensical (Material for MkDocs replacement)
- Plugins: mkdocstrings for API documentation
- Navigation: Defined in zensical.toml

## Writing Documentation

### Markdown Files

- Use standard Markdown syntax
- Code blocks with syntax highlighting
- Admonitions for notes/warnings
- Tables for structured data

### API Documentation

API documentation is auto-generated from docstrings using mkdocstrings:

```markdown
# Chart API

::: owid.grapher.Chart
```

This automatically extracts and renders:
- Class/function signatures
- Docstrings
- Type hints
- Source code links

### Code Examples

Include runnable examples:

````markdown
```python
from owid.grapher import Chart
import pandas as pd

df = pd.DataFrame({...})
chart = Chart(df).mark_line()
```
````

## Docstring Format

Use Google-style docstrings in the Python code:

```python
def function(param: str) -> int:
    """Brief description.

    Longer description with details.

    Args:
        param: Parameter description

    Returns:
        Return value description

    Raises:
        ValueError: When something is wrong

    Example:

        ```python
        >>> result = function("value")
        >>> print(result)
        42
        ```
    """
```

## Deploying

Documentation can be deployed to:
- GitHub Pages (via GitHub Actions)
- Netlify
- Any static hosting service

The built site is in `site/` after running `zensical build`.
