# python-project template notes

## Approach

The foundational Cookiecutter template for uv-managed Python projects. Every baked project gets a consistent baseline: ruff for linting and formatting, mypy in strict mode, pytest with coverage, and direnv for automatic venv activation.

## Template variables

- `project_name` — human-readable display name (e.g. "Fresh Project")
- `project_slug` — kebab-case directory and pyproject.toml name (e.g. "fresh-project")
- `package_name` — snake_case Python package (e.g. "fresh_project")

## Decisions and tradeoffs

- **Python 3.13 target**: forward-looking baseline; projects that need older Python can lower `requires-python` after baking.
- **Hatchling build backend**: lightweight, PEP 517-compliant, no extra config needed for simple packages.
- **Click and Pydantic in default dependencies**: most projects end up needing a CLI entry point and structured data; including them avoids a follow-up `uv add` in almost every case.
- **Strict mypy defaults**: catches issues early. Per-package `ignore_missing_imports` override keeps third-party stubs from blocking adoption.
- **Baseline hello_world**: gives `make test` something to pass immediately after baking so the developer can verify their environment before writing real code.
- **Bundled make_cookiecutter_template.py**: each baked project can spawn its own Cookiecutter templates, keeping the pattern self-replicating.

## Bake-level tests

`tests/test_bake_python_project.py` — follows the same pattern as `test_bake_repo_cli.py`.

- **TestBakeDefaults** (28 tests): Bakes with `cookiecutter.json` defaults and verifies the full file tree, package structure, pyproject.toml fields (name, description, Python version, hatchling, dependencies, strict mypy, overrides), Makefile targets, README heading and quickstart, and that no raw `{{cookiecutter.*}}` variables survive rendering.
- **TestBakeCustomContext** (9 tests): Bakes with custom values (`widget-factory` / `widget_factory` / `Widget Factory`) and verifies all three template variables propagate correctly. Also checks that no default values leak into the custom bake.
