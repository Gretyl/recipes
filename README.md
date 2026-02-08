# Recipes

Cookiecutter templates and tooling for scaffolding Python projects.

## Quickstart

```bash
uv sync && direnv allow
```

## Repository Layout

- `cookbook/` — Cookiecutter templates
  - `python-project/` — uv-managed Python project template (ruff, mypy, pytest, direnv)
- `recipes/` — Python package (smoke-test baseline)
- `scripts/` — standalone tooling
  - `make_cookiecutter_template.py` — convert an existing repo into a Cookiecutter template
  - `meld_makefiles.py` — merge Makefile targets
- `tests/` — pytest test suite
- `docs/` — project documentation

## Creating a project from the template

```bash
cookiecutter cookbook/python-project/
```

## Creating a new template from an existing project

```bash
python scripts/make_cookiecutter_template.py --src /path/to/repo --dst /path/to/output
```

## Makefile targets

```bash
make test      # ruff check --fix, ruff format, then pytest --doctest-modules --cov
make check     # ruff check --fix
make format    # ruff format
make mypy      # mypy after format+check
make clean     # remove build/cache/venv/lock artifacts
```
