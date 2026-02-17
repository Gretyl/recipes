# Working with recipe templates
Maintain a `notes/<template-name>.md` file and append notes to it as you work, tracking what you tried and anything you learned along the way.

When changes to a template are ready to commit, run "uvx showboat --help" and then use showboat to update the `demos/<template-name>.md` file to describe the behavior of the templated output.

## Template Conventions

- Generated projects use **uv** for dependency management and **direnv** for automatic venv activation (`uv sync && direnv allow`)
- Python target is **3.13**, build backend is **hatchling**
- Dev tools: ruff (lint+format), mypy (strict mode), pytest with pytest-cov/pytest-mock
- `recipes generalize` auto-detects the package dir (first folder with `__init__.py`) and templates it as `{{cookiecutter.package_name}}`; it also replaces the project name in `pyproject.toml`
- Text files with extensions `.py`, `.toml`, `.md`, `.json`, `.yaml`, `.yml`, `.txt` get variable substitution; all others are copied as-is
