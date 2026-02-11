# python-project template demo

*2026-02-11T18:33:58Z*

The python-project template scaffolds a uv-managed Python project with ruff, mypy, pytest, and direnv support. It includes a baseline `hello_world` implementation so `make test` passes immediately after baking.

Bake the template with defaults (project_name=Fresh Project):

```bash
rm -rf /tmp/python-project-demo && cookiecutter /home/user/recipes/cookbook/python-project --no-input --output-dir /tmp/python-project-demo && find /tmp/python-project-demo/fresh-project -type f | sort | sed 's|/tmp/python-project-demo/||'
```

```output
fresh-project/.envrc
fresh-project/.gitattributes
fresh-project/.gitignore
fresh-project/Makefile
fresh-project/README.md
fresh-project/docs/spec.md
fresh-project/fresh_project/__init__.py
fresh-project/fresh_project/main.py
fresh-project/pyproject.toml
fresh-project/scripts/make_cookiecutter_template.py
fresh-project/tests/test_main.py
```

The baseline package exports a `hello_world` function:

```bash
PYTHONPATH=/tmp/python-project-demo/fresh-project /usr/local/bin/python -c 'from fresh_project import hello_world; print(hello_world())'
```

```output
Hello, world!
```

It also works as a script via `main()`:

```bash
PYTHONPATH=/tmp/python-project-demo/fresh-project /usr/local/bin/python -c 'from fresh_project.main import main; main()'
```

```output
Hello, world!
```

The Makefile provides the standard development targets:

```bash
make -C /tmp/python-project-demo/fresh-project help
```

```output
make: Entering directory '/tmp/python-project-demo/fresh-project'
Target       Description
------       -----------
check        Lint and auto-fix issues with ruff.
clean        Remove build, cache, venv, and lock artifacts.
format       Format code using ruff.
mypy         Type-check sources with mypy after format/check.
test         Run tests with coverage after check and format.
make: Leaving directory '/tmp/python-project-demo/fresh-project'
```

The pyproject.toml targets Python 3.14 with hatchling, includes click and pydantic as defaults, and enables strict mypy:

```bash
cat /tmp/python-project-demo/fresh-project/pyproject.toml
```

```output
[project]
name = "fresh-project"
version = "0.1.0"
description = "My take on Fresh Project"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "click",
    "pydantic",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest",
    "pytest-cov",
    "pytest-mock",
    "pyyaml",
    "ruff",
    "mypy",
]

[tool.mypy]
python_version = "3.14"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
strict_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "fresh_project.*"
ignore_missing_imports = true
```
