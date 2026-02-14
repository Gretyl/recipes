# recipes CLI

*2026-02-13T21:55:58Z*

The recipes CLI is the repo-local command-line interface provided by the `recipes_cli` package. It uses Click with an `OrderedGroup` that lists subcommands alphabetically. Every subcommand must be built with red/green TDD, use Pydantic type signatures for structured data, and pass `mypy` cleanly. See CLI.md for the full development standards.

Bare invocation (no arguments) displays help with all available subcommands:

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()'
```

```output
Usage: -c [OPTIONS] COMMAND [ARGS]...

  Recipes CLI.

Options:
  --help  Show this message and exit.

Commands:
  hello  Say hello.
  help   Show this help message and exit.
```

Subcommands are listed alphabetically. The `hello` command is a starter subcommand:

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' hello
```

```output
Hello from recipes_cli.tui!
```

The `help` subcommand produces the same output as bare invocation:

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' help
```

```output
Usage: -c [OPTIONS] COMMAND [ARGS]...

  Recipes CLI.

Options:
  --help  Show this message and exit.

Commands:
  hello  Say hello.
  help   Show this help message and exit.
```

The `--help` flag works on any subcommand to show its usage:

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' hello --help
```

```output
Usage: -c hello [OPTIONS]

  Say hello.

Options:
  --help  Show this message and exit.
```

Tests verify all subcommands using Click's `CliRunner`. Every subcommand is covered by red/green TDD:

```bash
/home/user/recipes/.venv/bin/python -m pytest tests/test_cli.py -v
```

```output
============================= test session starts ==============================
platform linux -- Python 3.13.12, pytest-9.0.2, pluggy-1.6.0 -- /home/user/recipes/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/user/recipes
configfile: pyproject.toml
plugins: cov-7.0.0, mock-3.15.1
collecting ... collected 5 items

tests/test_cli.py::test_hello_command PASSED                             [ 20%]
tests/test_cli.py::test_no_args_shows_help PASSED                        [ 40%]
tests/test_cli.py::test_help_subcommand PASSED                           [ 60%]
tests/test_cli.py::test_help_flag PASSED                                 [ 80%]
tests/test_cli.py::test_commands_listed_alphabetically PASSED            [100%]

============================== 5 passed in 0.08s ===============================
```
