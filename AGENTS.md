# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of Cookiecutter templates, tooling for scaffolding Python projects, and a uv-managed Python project environment. The primary template is `cookbook/python-project/`, which generates a uv-managed Python project with ruff, mypy, pytest, and direnv support.

## Repository Layout

- `cookbook/python-project/` — Cookiecutter template directory
  - `cookiecutter.json` — template variables: `project_name`, `project_slug`, `package_name`
  - `{{cookiecutter.project_slug}}/` — the baked project skeleton (pyproject.toml, Makefile, tests, docs)
- `recipes/` — Python package (smoke-test baseline; `recipes.main.hello_world`)
- `recipes_cli/` — CLI package (`recipes` command)
  - `tui/cli.py` — Click CLI definitions (`recipes generalize`, `recipes meld makefiles`)
  - `generalize.py` — convert an existing Python repo into a new Cookiecutter template
  - `meld.py` — merge Makefile targets
- `tests/` — pytest test suite
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
recipes generalize --src /path/to/repo --dst /path/to/output
```

### Commands available via Makefile

```bash
make test      # ruff check --fix, ruff format, then pytest --doctest-modules --cov
make check     # ruff check --fix
make format    # ruff format
make mypy      # mypy after format+check
make clean     # remove build/cache/venv/lock artifacts
```

## Commit Conventions

All commits **must** use [Conventional Commits](https://www.conventionalcommits.org/) for the subject line:

```
<type>(<scope>): <short summary>
```

### Types

- **feat** — new feature or functionality
- **fix** — bug fix
- **docs** — documentation-only changes
- **style** — formatting, whitespace, or cosmetic changes (no logic changes)
- **refactor** — code restructuring without changing external behavior
- **test** — adding or updating tests
- **chore** — maintenance tasks, dependency updates, CI config, etc.
- **build** — changes to the build system or tooling
- **ci** — continuous integration configuration changes
- **perf** — performance improvements

### Scopes

Use a scope that identifies the area of the codebase affected:

- **template** — `cookbook/python-project/` template files
- **cli** — `recipes_cli/` CLI package
- **recipes** — `recipes/` Python package
- **tests** — `tests/` test suite
- **docs** — `docs/` or top-level documentation files (README, AGENTS.md, etc.)
- **deps** — dependency or lockfile changes

The scope is required when the change clearly maps to one area. Omit it only for cross-cutting changes that span multiple scopes.

### Examples

```
feat(cli): add export subcommand for templates
fix(template): correct pyproject.toml Python version
docs(docs): update spec with new CLI usage
test(tests): add coverage for generalize edge cases
chore(deps): bump ruff to 0.8.x
refactor(recipes): simplify hello_world module
```

## Template Conventions

- Generated projects use **uv** for dependency management and **direnv** for automatic venv activation (`uv sync && direnv allow`)
- Python target is **3.13**, build backend is **hatchling**
- Dev tools: ruff (lint+format), mypy (strict mode), pytest with pytest-cov/pytest-mock
- `recipes generalize` auto-detects the package dir (first folder with `__init__.py`) and templates it as `{{cookiecutter.package_name}}`; it also replaces the project name in `pyproject.toml`
- Text files with extensions `.py`, `.toml`, `.md`, `.json`, `.yaml`, `.yml`, `.txt` get variable substitution; all others are copied as-is
