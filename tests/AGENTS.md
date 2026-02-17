# Tests

## File layout convention

Each CLI subcommand gets its own test file under `tests/cli/`:

```
tests/cli/
  conftest.py            # shared fixtures (e.g. CliRunner)
  test_help.py           # recipes help (and top-level CLI behaviour)
  test_generalize.py     # recipes generalize
  test_meld_makefiles.py # recipes meld makefiles
```

When a new subcommand is added to `recipes_cli`, create a corresponding `tests/cli/test_<subcommand>.py` file. For nested subcommands (e.g. `recipes meld makefiles`), use underscores to flatten the hierarchy: `test_meld_makefiles.py`.

## Shared fixtures

Fixtures used by more than one test file belong in `tests/cli/conftest.py`. Fixtures specific to a single subcommand stay in that subcommand's test file.

## Other test files

Non-CLI tests (template baking, library code, cross-template consistency) live directly under `tests/` as before:

- `tests/test_main.py` — `recipes` library package
- `tests/test_bake_python_project.py` — python-project template baking
- `tests/test_bake_repo_cli.py` — repo-cli template baking
- `tests/test_template_consistency.py` — cross-template consistency checks
- `tests/helpers.py` — shared test utilities
