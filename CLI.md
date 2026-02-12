# CLI

The `recipes_cli` package provides a repo-local command-line interface for programmatic project support. It is installed as the `recipes` console script entry point and invoked as:

```bash
recipes <subcommand>
```

## Scope

`recipes_cli` is **project support tooling**, distinct from the `recipes` library package:

| Concern | Package | Role |
|---|---|---|
| Library code | `recipes/` | Domain logic, importable modules |
| CLI layer | `recipes_cli/` | Repo-local commands that orchestrate project tasks |
| Test suite | `tests/` | Covers both packages |

The CLI exists to give Makefile targets (and developers) a programmable interface for operations that outgrow shell one-liners — template baking, scaffold generation, Makefile melding, and future enhancements that benefit from argument parsing, validation, and composition.

## Architecture

```
recipes_cli/
  tui/
    __init__.py
    cli.py          # Click entry point (OrderedGroup)
```

- **Entry point:** `recipes = "recipes_cli.tui.cli:cli"` (defined in `pyproject.toml`)
- **Framework:** Click with `OrderedGroup` for alphabetically-sorted subcommands
- **Pattern:** Add new subcommands as `@cli.command()` functions in `cli.py`, or as separate modules registered onto the `cli` group

## Adding a subcommand

```python
# in recipes_cli/tui/cli.py

@cli.command()
@click.argument("name")
def greet(name: str) -> None:
    """Greet someone by name."""
    click.echo(f"Hello, {name}!")
```

Then from a Makefile target:

```makefile
greet:
	@recipes greet World
```

## Relation to Makefile

Makefile targets remain the stable developer interface (`make test`, `make check`, etc.). The CLI supplements Make for tasks requiring richer argument handling or Python-native logic. A Makefile target can delegate to the CLI:

```makefile
bake:
	@recipes bake --template python-project
```
