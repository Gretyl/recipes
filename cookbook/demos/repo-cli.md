# repo-cli template demo

*2026-02-12T14:49:49Z*

The repo-cli template scaffolds a Click-based CLI project targeting a specific repository. The baked package uses a `_cli` suffix by convention (`<target_repo>_cli`) so it never collides with the host repo's library package. A bundled CLI.md documents the CLI's scope as programmatic project support tooling, including development standards requiring red/green TDD, Pydantic type signatures, and clean `mypy`.

```bash
rm -rf /tmp/repo-cli-demo && cookiecutter /home/user/recipes/cookbook/repo-cli --no-input --output-dir /tmp/repo-cli-demo && find /tmp/repo-cli-demo/my-repo-cli -type f | sort | sed 's|/tmp/repo-cli-demo/||'
```

```output
my-repo-cli/.envrc
my-repo-cli/.gitattributes
my-repo-cli/.gitignore
my-repo-cli/CHANGELOG.md
my-repo-cli/CLI.md
my-repo-cli/Makefile
my-repo-cli/README.md
my-repo-cli/my_repo_cli/tui/__init__.py
my-repo-cli/my_repo_cli/tui/cli.py
my-repo-cli/pyproject.toml
my-repo-cli/tests/test_cli.py
```

Note the `_cli` suffix: `my_repo_cli/` (not `my_repo/`). This is derived automatically from `target_repo` in `cookiecutter.json`. The baked output also includes `CLI.md` documenting the CLI's scope and architecture.

The CLI entry point is registered as `my-repo-cli`. Invoke it with no arguments to see help:

```bash
PYTHONPATH=/tmp/repo-cli-demo/my-repo-cli /usr/local/bin/python3 -c 'from my_repo_cli.tui.cli import cli; cli()'
```

```output
Usage: -c [OPTIONS] COMMAND [ARGS]...

  My Repo CLI.

Options:
  --help  Show this message and exit.

Commands:
  hello  Say hello.
  help   Show this help message and exit.
```

Commands are listed alphabetically. The `help` subcommand produces the same output as bare invocation. The `hello` command is a starter subcommand:

```bash
PYTHONPATH=/tmp/repo-cli-demo/my-repo-cli /usr/local/bin/python3 -c 'from my_repo_cli.tui.cli import cli; cli()' hello
```

```output
Hello from my_repo_cli.tui!
```

CLI.md documents the CLI's scope as programmatic project support, the architecture, development standards (red/green TDD, Pydantic type signatures, clean mypy), and the Makefile delegation pattern:

```bash
cat /tmp/repo-cli-demo/my-repo-cli/CLI.md
```

````output
# CLI

The `my_repo_cli` package provides a repo-local command-line interface for programmatic project support. It is installed as the `my-repo-cli` console script entry point and invoked as:

```bash
my-repo-cli <subcommand>
```

## Scope

`my_repo_cli` is **project support tooling**, distinct from any library packages in the same repository:

| Concern | Package | Role |
|---|---|---|
| Library code | Application-specific | Domain logic, importable modules |
| CLI layer | `my_repo_cli/` | Repo-local commands that orchestrate project tasks |
| Test suite | `tests/` | Covers all packages |

The CLI exists to give Makefile targets (and developers) a programmable interface for operations that outgrow shell one-liners — tasks that benefit from argument parsing, validation, and composition.

## Architecture

```
my_repo_cli/
  tui/
    __init__.py
    cli.py          # Click entry point (OrderedGroup)
```

- **Entry point:** `my-repo-cli = "my_repo_cli.tui.cli:cli"` (defined in `pyproject.toml`)
- **Framework:** Click with `OrderedGroup` for alphabetically-sorted subcommands
- **Pattern:** Add new subcommands as `@cli.command()` functions in `cli.py`, or as separate modules registered onto the `cli` group

## Development standards

Every CLI subcommand — both new proposals and pre-existing commands — must satisfy three requirements:

1. **Red/green TDD.** Write a failing test *first* (`red`), then implement just enough code to make it pass (`green`). Tests live in `tests/test_cli.py` and use Click's `CliRunner`.
2. **Pydantic type signatures.** Subcommand inputs and outputs that carry structured data must be expressed as Pydantic models. This gives you runtime validation, serialisation, and self-documenting schemas for free.
3. **Clean `mypy`.** All CLI code must pass `mypy` with the strict settings defined in `pyproject.toml`. Run `make mypy` before committing.

## Adding a subcommand

1. Write a failing test:

```python
# in tests/test_cli.py

def test_greet_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "World"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output
```

2. Implement the subcommand with a Pydantic model:

```python
# in my_repo_cli/tui/cli.py

from pydantic import BaseModel

class GreetArgs(BaseModel):
    name: str

@cli.command()
@click.argument("name")
def greet(name: str) -> None:
    """Greet someone by name."""
    args = GreetArgs(name=name)
    click.echo(f"Hello, {args.name}!")
```

3. Verify the tests pass (`make test`) and types check (`make mypy`).

Then from a Makefile target:

```makefile
greet:
	@my-repo-cli greet World
```

## Relation to Makefile

Makefile targets remain the stable developer interface (`make test`, `make check`, etc.). The CLI supplements Make for tasks requiring richer argument handling or Python-native logic. A Makefile target can delegate to the CLI:

```makefile
example:
	@my-repo-cli example --flag value
```
````

The CHANGELOG.md follows Keep a Changelog 1.1.0 format, used by `make dist` to validate version consistency:

```bash
cat /tmp/repo-cli-demo/my-repo-cli/CHANGELOG.md
```

```output
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - YYYY-MM-DD

### Added

- Initial release of My Repo CLI.
```

The Makefile includes standard targets plus `make dist` for versioned releases. The `test` target passes `$(PYTHON_DIRS)` to pytest for doctest coverage across all source directories:

```bash
make -C /tmp/repo-cli-demo/my-repo-cli help
```

```output
make: Entering directory '/tmp/repo-cli-demo/my-repo-cli'
Target       Description
------       -----------
check        Lint and auto-fix issues with ruff.
clean        Remove build, cache, venv, lock, and dist artifacts.
dist         Prepare a versioned release in dist/.
format       Format code using ruff.
mypy         Type-check sources with mypy after format/check.
test         Run tests with coverage after check and format.
make: Leaving directory '/tmp/repo-cli-demo/my-repo-cli'
```

The pyproject.toml registers the console script entry point and configures hatch to build the `_cli` package:

```bash
cat /tmp/repo-cli-demo/my-repo-cli/pyproject.toml
```

```output
[project]
name = "my-repo-cli"
version = "0.1.0"
description = "My take on My Repo CLI"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "click",
    "pydantic",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
my-repo-cli = "my_repo_cli.tui.cli:cli"

[dependency-groups]
dev = [
    "pytest",
    "pytest-cov",
    "pytest-mock",
    "pyyaml",
    "ruff",
    "mypy",
]

[tool.hatch.build.targets.wheel]
packages = ["my_repo_cli"]

[tool.mypy]
python_version = "3.13"
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
module = "my_repo_cli.*"
ignore_missing_imports = true
```

The `dist/` directory is gitignored and removed by `make clean`:

```bash
cat /tmp/repo-cli-demo/my-repo-cli/.gitignore
```

```output
*.pyc
.aider*
.claude/
.coverage
.direnv
dist/
```
