# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of Cookiecutter templates, tooling for scaffolding Python projects, and a uv-managed Python project environment. The primary template is `cookbook/python-project/`, which generates a uv-managed Python project with ruff, mypy, pytest, and direnv support.

## Repository Layout

- `cookbook/` — Cookiecutter templates and their documentation
  - `python-project/` — foundational template for uv-managed Python projects
    - `cookiecutter.json` — template variables: `project_name`, `project_slug`, `package_name`
    - `{{cookiecutter.project_slug}}/` — the baked project skeleton (pyproject.toml, Makefile, tests, docs)
  - `repo-cli/` — template for Click-based CLI projects targeting a host repository
    - `cookiecutter.json` — template variables: `project_name`, `target_repo`, `project_slug`, `package_name`, `include_github_workflow`
    - `hooks/post_gen_project.py` — conditionally removes `.github/` directory
  - `notes/` — development notes per template (`python-project.md`, `repo-cli.md`)
  - `demos/` — showboat-generated output demos per template
- `recipes/` — Python package (smoke-test baseline; `recipes.main.hello_world`)
- `recipes_cli/` — CLI package (`recipes_cli.tui.cli`); Click-based project support tooling
- `scripts/` — standalone tooling
  - `make_cookiecutter_template.py` — converts an existing Python repo into a new Cookiecutter template
  - `meld_makefiles.py` — merge Makefile targets
- `tests/` — pytest test suite (unit tests, CLI tests, bake-level template tests)
- `docs/` — project documentation (spec.md)

## Key Commands

### Quickstart

```bash
uv sync && direnv allow
```

### Creating a project from the template

```bash
cookiecutter cookbook/python-project/
# or with a specific output dir:
cookiecutter cookbook/python-project/ --output-dir /path/to/dest
```

### Creating a new template from an existing project

```bash
python scripts/make_cookiecutter_template.py --src /path/to/repo --dst /path/to/output
```

### Commands available via Makefile

```bash
make test      # ruff check --fix, ruff format, then pytest --doctest-modules --cov
make check     # ruff check --fix
make format    # ruff format
make mypy      # mypy after format+check
make clean     # remove build/cache/venv/lock artifacts
make dist      # validate release (clean tree, version match, tag) then uv build
```

## Template Conventions

- Generated projects use **uv** for dependency management and **direnv** for automatic venv activation (`uv sync && direnv allow`)
- Python target is **3.13**, build backend is **hatchling**
- Dev tools: ruff (lint+format), mypy (strict mode), pytest with pytest-cov/pytest-mock
- Both templates (`python-project` and `repo-cli`) share the same mypy strict settings and dev dependency baseline
- The `repo-cli` template derives `package_name` as `<target_repo>_cli` to avoid collisions with the host repo's library package
- The `make_cookiecutter_template.py` script auto-detects the package dir (first folder with `__init__.py`) and templates it as `{{cookiecutter.package_name}}`; it also replaces the project name in `pyproject.toml`
- Text files with extensions `.py`, `.toml`, `.md`, `.json`, `.yaml`, `.yml`, `.txt` get variable substitution; all others are copied as-is
