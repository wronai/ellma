# ELLMa Documentation

This directory contains the source files for the ELLMa documentation, built with [Sphinx](https://www.sphinx-doc.org/).

## Building the Documentation

### Prerequisites

- Python 3.8+
- Poetry

### Installation

1. Install the documentation dependencies:

```bash
cd /path/to/ellma
poetry install --with docs
```

### Building Locally

To build the HTML documentation:

```bash
cd docs
make html
```

The built documentation will be available in `_build/html/`.

### Live Preview

For live preview with auto-reload:

```bash
cd docs
make dev
```

This will start a local server at http://localhost:8000 that automatically reloads when you make changes to the source files.

## Documentation Structure

- `source/`: Contains all the documentation source files
  - `index.rst`: Main documentation entry point
  - `getting_started.md`: Getting started guide
  - `evolution_guide.md`: Guide to the evolution system
  - `api_reference/`: Auto-generated API documentation
  - `modules/`: Module documentation
  - `commands/`: Command reference
  - `utils/`: Utility modules documentation

## Writing Documentation

- Use [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) for documentation
- Use [MyST Markdown](https://myst-parser.readthedocs.io/) for simpler pages
- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings

## Publishing

The documentation is automatically published to GitHub Pages on each push to the `main` branch using GitHub Actions.
