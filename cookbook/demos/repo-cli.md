# repo-cli template demo

*2026-02-11T18:13:33Z*

The repo-cli template scaffolds a Click-based CLI project targeting a specific repository. It produces a namespace package (`<target_repo>.tui`) so the CLI can coexist with the target repo's own package.

Bake the template with defaults (target_repo=my-repo):

```bash
rm -rf /tmp/repo-cli-demo && cookiecutter /home/user/recipes/cookbook/repo-cli --no-input --output-dir /tmp/repo-cli-demo && find /tmp/repo-cli-demo/my-repo-cli -type f | sort | sed 's|/tmp/repo-cli-demo/||'
```

```output
my-repo-cli/.envrc
my-repo-cli/.gitattributes
my-repo-cli/.gitignore
my-repo-cli/CHANGELOG.md
my-repo-cli/Makefile
my-repo-cli/README.md
my-repo-cli/docs/spec.md
my-repo-cli/my_repo/tui/__init__.py
my-repo-cli/my_repo/tui/cli.py
my-repo-cli/pyproject.toml
my-repo-cli/tests/test_cli.py
```

The CLI entry point is registered as `my-repo-cli`. Install and invoke it:

```bash
PYTHONPATH=/tmp/repo-cli-demo/my-repo-cli /usr/local/bin/python -c 'from my_repo.tui.cli import cli; cli()'
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

Running with no arguments is equivalent to running the `help` subcommand. Commands are listed alphabetically. The `help` subcommand produces the same output:

```bash
PYTHONPATH=/tmp/repo-cli-demo/my-repo-cli /usr/local/bin/python -c 'from my_repo.tui.cli import cli; cli()' help
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

The `hello` command is a starter subcommand demonstrating the CLI group:

```bash
PYTHONPATH=/tmp/repo-cli-demo/my-repo-cli /usr/local/bin/python -c 'from my_repo.tui.cli import cli; cli()' hello
```

```output
Hello from my_repo.tui!
```

The CHANGELOG.md follows Keep a Changelog 1.1.0 format:

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

The Makefile includes standard targets plus `make dist` for versioned releases:

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
