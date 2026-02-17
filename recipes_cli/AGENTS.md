# CLI

The `recipes_cli` package provides a repo-local command-line interface for programmatic project support. It is installed as the `recipes` console script entry point and invoked as:

```bash
recipes <subcommand>
```

## Scope

`recipes_cli` is **project support tooling**, distinct from the `recipes` library package. The CLI exists to give Makefile targets (and developers) a programmable interface for operations that outgrow shell one-liners — template baking, scaffold generation, Makefile melding, and future enhancements that benefit from argument parsing, validation, and composition.

## Architecture decisions

- **Entry point:** `recipes = "recipes_cli.tui.cli:cli"` (defined in `pyproject.toml`)
- **Framework:** Click with `OrderedGroup` for alphabetically-sorted subcommands
- **Pattern:** Add new subcommands as `@cli.command()` functions in `cli.py`, or as separate modules registered onto the `cli` group
- **Relation to Makefile:** Makefile targets remain the stable developer interface (`make test`, `make check`, etc.). The CLI supplements Make for tasks requiring richer argument handling or Python-native logic. A Makefile target can delegate to the CLI.

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
# in recipes_cli/tui/cli.py

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
