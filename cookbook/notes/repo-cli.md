# repo-cli template notes

## Approach

Modeled after the existing `python-project` template as the peer reference. Key differences:

- **Namespace package**: `{{cookiecutter.package_name}}/` has no `__init__.py` so the `tui` subpackage can coexist with a target repo's own package. Only `{{cookiecutter.package_name}}/tui/` has `__init__.py`. Hatchling needs `[tool.hatch.build.targets.wheel] packages = [...]` to find it.
- **Derived cookiecutter variables**: `project_slug` (`<target_repo>-cli`) and `package_name` (`<target_repo>` with hyphens replaced by underscores) are derived from `target_repo` in `cookiecutter.json` using Jinja2 expressions.
- **Click CLI group**: Uses a custom `OrderedGroup` subclass to list commands alphabetically. `invoke_without_command=True` makes bare invocation print help. An explicit `help` subcommand mirrors `--help`.
- **`make dist`**: Validates three preconditions in-shell before calling `uv build --out-dir dist/`:
  1. Clean working tree (`git status --porcelain`)
  2. CHANGELOG.md latest semver entry matches `pyproject.toml` version (parsed with `sed`)
  3. Tag `v<version>` exists and points to HEAD
- **CHANGELOG.md**: Follows Keep a Changelog 1.1.0 with an `[Unreleased]` section and an initial `[0.1.0]` entry with `YYYY-MM-DD` placeholder date.

## Decisions and tradeoffs

- Used `sed` for version extraction in the Makefile `dist` target to avoid a Python dependency in the build step. POSIX-compatible patterns (`[0-9][^ ]*`) skip the `[Unreleased]` heading.
- `dist/` is in `.gitignore` and removed by `make clean`. The template never commits build artifacts.
- Kept `pydantic` in dependencies to match the python-project peer, since CLI tools commonly use it for config/models.
