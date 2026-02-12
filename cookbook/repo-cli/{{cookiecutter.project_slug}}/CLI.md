# CLI

The `{{cookiecutter.package_name}}` package provides a repo-local command-line interface for programmatic project support. It is installed as the `{{cookiecutter.project_slug}}` console script entry point and invoked as:

```bash
{{cookiecutter.project_slug}} <subcommand>
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
```

- **Entry point:** `{{cookiecutter.project_slug}} = "{{cookiecutter.package_name}}.tui.cli:cli"` (defined in `pyproject.toml`)
- **Framework:** Click with `OrderedGroup` for alphabetically-sorted subcommands
- **Pattern:** Add new subcommands as `@cli.command()` functions in `cli.py`, or as separate modules registered onto the `cli` group

## Adding a subcommand

```python
# in {{cookiecutter.package_name}}/tui/cli.py

@cli.command()
@click.argument("name")
def greet(name: str) -> None:
    """Greet someone by name."""
    click.echo(f"Hello, {name}!")
```

Then from a Makefile target:

```makefile
greet:
	@{{cookiecutter.project_slug}} greet World
```

## Relation to Makefile

Makefile targets remain the stable developer interface (`make test`, `make check`, etc.). The CLI supplements Make for tasks requiring richer argument handling or Python-native logic. A Makefile target can delegate to the CLI:

```makefile
example:
	@{{cookiecutter.project_slug}} example --flag value
```
