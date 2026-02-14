# recipes CLI

*2026-02-14T00:00:00Z*

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
  generalize  Create a Cookiecutter template from an existing repo.
  hello       Say hello.
  help        Show this help message and exit.
  meld        Meld features between files.
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
  generalize  Create a Cookiecutter template from an existing repo.
  hello       Say hello.
  help        Show this help message and exit.
  meld        Meld features between files.
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

## `generalize` — create a Cookiecutter template from an existing repo

The `generalize` subcommand converts an existing Python repository into a Cookiecutter template. It auto-detects the package directory (first folder with `__init__.py`), templates `pyproject.toml` and `README.md`, and replaces the package name in all templatable files (`.py`, `.toml`, `.md`, `.json`, `.yaml`, `.yml`, `.txt`).

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' generalize --help
```

```output
Usage: -c generalize [OPTIONS]

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

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' generalize --src /path/to/repo --dst /path/to/output
```

```output
Template created: /path/to/output/cookiecutter-myproject
  package detected: mypackage
  cookiecutter.json: {'project_name': 'Myproject', 'project_slug': 'myproject', 'package_name': 'mypackage'}
```

The generated template includes a `cookiecutter.json` with `project_name`, `project_slug`, and `package_name` variables, a `{{cookiecutter.project_slug}}/` skeleton directory, and the package directory renamed to `{{cookiecutter.package_name}}/`.

## `meld` — meld features between files

The `meld` command is a subgroup for comparing and merging features between files. Currently it contains one subcommand: `makefiles`.

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' meld --help
```

```output
Usage: -c meld [OPTIONS] COMMAND [ARGS]...

  Meld features between files.

Options:
  --help  Show this message and exit.

Commands:
  makefiles  Meld features from source Makefile to target Makefile.
```

### `meld makefiles` — compare and merge Makefile features

Parses two Makefiles structurally (targets, variables, `.PHONY` declarations, help entries) and reports differences. Supports four output formats.

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' meld makefiles --help
```

```output
Usage: -c meld makefiles [OPTIONS] SOURCE TARGET

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

```bash
/home/user/recipes/.venv/bin/python -c 'from recipes_cli.tui.cli import cli; cli()' meld makefiles source.mk target.mk -o json
```

```output
{
  "new_targets": ["lint", "deploy"],
  "modified_targets": ["test"],
  "removed_targets": [],
  "new_variables": {
    "DEPLOY_TARGET": {
      "operator": ":=",
      "value": "production",
      "comments": []
    }
  },
  "changed_variables": {},
  "new_phony": ["deploy", "lint"],
  "help_changes": {}
}
```

## Tests

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
collecting ... collected 24 items

tests/test_cli.py::test_hello_command PASSED                             [  4%]
tests/test_cli.py::test_no_args_shows_help PASSED                        [  8%]
tests/test_cli.py::test_help_subcommand PASSED                           [ 12%]
tests/test_cli.py::test_help_flag PASSED                                 [ 16%]
tests/test_cli.py::test_commands_listed_alphabetically PASSED            [ 20%]
tests/test_cli.py::test_generalize_appears_in_help PASSED                [ 25%]
tests/test_cli.py::test_generalize_requires_dst PASSED                   [ 29%]
tests/test_cli.py::test_generalize_creates_template PASSED               [ 33%]
tests/test_cli.py::test_generalize_templates_pyproject_toml PASSED       [ 37%]
tests/test_cli.py::test_generalize_templates_readme_heading PASSED       [ 41%]
tests/test_cli.py::test_generalize_custom_template_name PASSED           [ 45%]
tests/test_cli.py::test_generalize_src_defaults_to_cwd PASSED            [ 50%]
tests/test_cli.py::test_generalize_fails_if_template_exists PASSED       [ 54%]
tests/test_cli.py::test_generalize_replaces_package_name_in_py_files PASSED [ 58%]
tests/test_cli.py::test_meld_group_appears_in_help PASSED                [ 62%]
tests/test_cli.py::test_meld_makefiles_appears_in_meld_help PASSED       [ 66%]
tests/test_cli.py::test_meld_makefiles_analysis_output PASSED            [ 70%]
tests/test_cli.py::test_meld_makefiles_json_output PASSED                [ 75%]
tests/test_cli.py::test_meld_makefiles_detects_modified_target PASSED    [ 79%]
tests/test_cli.py::test_meld_makefiles_detects_new_variables PASSED      [ 83%]
tests/test_cli.py::test_meld_makefiles_diff_output PASSED                [ 87%]
tests/test_cli.py::test_meld_makefiles_prompt_output PASSED              [ 91%]
tests/test_cli.py::test_meld_makefiles_nonexistent_source PASSED         [ 95%]
tests/test_cli.py::test_meld_makefiles_nonexistent_target PASSED         [100%]

============================== 24 passed in 0.78s ==============================
```
