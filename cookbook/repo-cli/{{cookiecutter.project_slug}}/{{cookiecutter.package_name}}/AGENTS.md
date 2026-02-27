# CLI

The `{{cookiecutter.package_name}}` package provides a repo-local command-line interface for programmatic project support. It is installed as the `{{cookiecutter.target_repo}}` console script entry point and invoked as:

```bash
{{cookiecutter.target_repo}} <subcommand>
```

## Scope

`{{cookiecutter.package_name}}` is **project support tooling**, distinct from any library packages in the same repository:

| Concern | Package | Role |
|---|---|---|
| Library code | Application-specific | Domain logic, importable modules |
| CLI layer | `{{cookiecutter.package_name}}/` | Repo-local commands that orchestrate project tasks |
| Test suite | `tests/` | Covers all packages |

The CLI exists to give Makefile targets (and developers) a programmable interface for operations that outgrow shell one-liners — tasks that benefit from argument parsing, validation, and composition.

## Architecture

```
{{cookiecutter.package_name}}/
  tui/
    __init__.py
    cli.py          # Click entry point (OrderedGroup)
    dashboard.py    # Textual TUI dashboard application
    status.py       # Rich-formatted project status display
    template.py     # Cog-based README template management
```

- **Entry point:** `{{cookiecutter.target_repo}} = "{{cookiecutter.package_name}}.tui.cli:cli"` (defined in `pyproject.toml`)
- **Framework:** Click with `OrderedGroup` for alphabetically-sorted subcommands
- **Pattern:** Add new subcommands as `@cli.command()` functions in `cli.py`, or as separate modules registered onto the `cli` group via `cli.add_command()`
- **Rich/Textual stubs:** `status.py` and `dashboard.py` are starter modules demonstrating Rich console output and Textual TUI apps. Both are available as dev dependencies — extend or replace them as the project grows.

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
# in {{cookiecutter.package_name}}/tui/cli.py

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
	@{{cookiecutter.target_repo}} greet World
```

## CLI commands

All commands are listed alphabetically by `OrderedGroup`. Run `{{cookiecutter.target_repo}} --help` to see the current list.

| Command | Description |
|---|---|
| `dashboard` | Launch the interactive Textual TUI. |
| `hello` | Say hello — a minimal stub command. |
| `help` | Show the top-level help message. |
| `status` | Display project metadata in a Rich-formatted table. |
| `template` | Manage the README Cog template (`apply`, `prepare`). |

## Makefile targets

Use `make <target>` for everyday development tasks. Run `make` with no arguments to see all targets.

| Target | Description | When to use |
|---|---|---|
| `make test` | Lint, format, then run pytest with coverage. | Before every commit. |
| `make check` | Lint and auto-fix with ruff. | Quick lint pass. |
| `make format` | Format code with ruff. | After writing new code. |
| `make mypy` | Type-check with strict mypy (runs format and check first). | Before committing type-sensitive changes. |
| `make clean` | Remove build, cache, venv, lock, and dist artifacts. | When resetting the dev environment. |
| `make dist` | Validate versions, tags, and build a release. | At release time only. |

**Tip:** `make test` is the single command that gates commits — it runs `check`, `format`, and `pytest` in sequence so you catch lint, formatting, and logic issues in one pass.

## Relation to Makefile

Makefile targets remain the stable developer interface (`make test`, `make check`, etc.). The CLI supplements Make for tasks requiring richer argument handling or Python-native logic. A Makefile target can delegate to the CLI:

```makefile
example:
	@{{cookiecutter.target_repo}} example --flag value
```

## Keeping USAGE.md in sync

`USAGE.md` (at the repo root) documents the `{{cookiecutter.target_repo}}` CLI's full syntax and output. It is generated by `uvx showboat` and must be regenerated whenever CLI syntax or semantics change — new subcommands, renamed options, altered output, etc.

After making CLI changes, run `uvx showboat --help` and use showboat to update `USAGE.md`.
