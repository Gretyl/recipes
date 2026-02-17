# recipes CLI

*2026-02-14T04:49:21Z*

The recipes CLI is the repo-local command-line interface provided by the `recipes_cli` package. It uses Click with an `OrderedGroup` that lists subcommands alphabetically. Every subcommand must be built with red/green TDD, use Pydantic type signatures for structured data, and pass `mypy` cleanly. See `recipes_cli/AGENTS.md` for the full development standards.

Bare invocation (no arguments) displays help with all available subcommands:

```bash
uv run recipes
```

```output
Usage: recipes [OPTIONS] COMMAND [ARGS]...

  Recipes CLI.

Options:
  --help  Show this message and exit.

Commands:
  generalize  Create a Cookiecutter template from an existing repo.
  help        Show this help message and exit.
  meld        Meld features between files.
```

## `generalize` — create a Cookiecutter template from an existing repo

The `generalize` subcommand converts an existing Python repository into a Cookiecutter template. It auto-detects the package directory (first folder with `__init__.py`), templates `pyproject.toml` and `README.md`, and replaces the package name in all templatable files (`.py`, `.toml`, `.md`, `.json`, `.yaml`, `.yml`, `.txt`).

```bash
uv run recipes generalize --help
```

```output
Usage: recipes generalize [OPTIONS]

  Create a Cookiecutter template from an existing repo.

Options:
  --src PATH
  --dst PATH            [required]
  --template-name TEXT
  --help                Show this message and exit.
```

Options:

- `--src PATH` — source repo to generalize (defaults to current directory)
- `--dst PATH` — output directory for the generated template (required)
- `--template-name TEXT` — custom name for the template folder (defaults to `cookiecutter-<project_slug>`)

Example usage:

    uv run recipes generalize --src /path/to/repo --dst /path/to/output

    Template created: /path/to/output/cookiecutter-myproject
      package detected: mypackage
      cookiecutter.json: {'project_name': 'Myproject', 'project_slug': 'myproject', 'package_name': 'mypackage'}

The generated template includes a `cookiecutter.json` with `project_name`, `project_slug`, and `package_name` variables, a `{{cookiecutter.project_slug}}/` skeleton directory, and the package directory renamed to `{{cookiecutter.package_name}}/`.

## `meld` — meld features between files

The `meld` command is a subgroup for comparing and merging features between files. Currently it contains one subcommand: `makefiles`.

```bash
uv run recipes meld --help
```

```output
Usage: recipes meld [OPTIONS] COMMAND [ARGS]...

  Meld features between files.

Options:
  --help  Show this message and exit.

Commands:
  makefiles  Meld features from source Makefile to target Makefile.
```

### `meld makefiles` — compare and merge Makefile features

Parses two Makefiles structurally (targets, variables, `.PHONY` declarations, help entries) and reports differences. Supports four output formats.

```bash
uv run recipes meld makefiles --help
```

```output
Usage: recipes meld makefiles [OPTIONS] SOURCE TARGET

  Meld features from source Makefile to target Makefile.

Options:
  -o, --output [analysis|prompt|diff|json]
  --help                          Show this message and exit.
```

Arguments:

- `SOURCE` — path to the source Makefile (features to import)
- `TARGET` — path to the target Makefile (destination)

Output formats (`-o` / `--output`):

- `analysis` (default) — human-readable summary of new targets, modified targets, new variables, changed variables, and `.PHONY` declarations
- `json` — machine-readable JSON with `new_targets`, `modified_targets`, `removed_targets`, `new_variables`, `changed_variables`, `new_phony`, and `help_changes`
- `diff` — unified diff between target and source
- `prompt` — structured analysis prompt including full file contents and diff, suitable for feeding to an LLM

Example:

    uv run recipes meld makefiles source.mk target.mk -o json

    {
      "new_targets": [
        "lint",
        "deploy"
      ],
      "modified_targets": [
        "test"
      ],
      "removed_targets": [],
      "new_variables": {
        "DEPLOY_TARGET": {
          "operator": ":=",
          "value": "production",
          "comments": []
        }
      },
      "changed_variables": {},
      "new_phony": [
        "deploy",
        "lint"
      ],
      "help_changes": {}
    }

## Tests

See [`tests/test_cli.py`](tests/test_cli.py) for full coverage of every subcommand via Click's `CliRunner`.
