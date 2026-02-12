# repo-cli template notes

## Approach

Modeled after the existing `python-project` template as the peer reference. Key differences:

- **Namespace package**: `{{cookiecutter.package_name}}/` has no `__init__.py` so the `tui` subpackage can coexist with a target repo's own package. Only `{{cookiecutter.package_name}}/tui/` has `__init__.py`. Hatchling needs `[tool.hatch.build.targets.wheel] packages = [...]` to find it.
- **Derived cookiecutter variables**: `project_slug` (`<target_repo>-cli`) and `package_name` (`<target_repo>_cli`) are derived from `target_repo` in `cookiecutter.json` using Jinja2 expressions.
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

## The `_cli` suffix convention

The `package_name` is derived as `<target_repo>_cli` (not just `<target_repo>`). This is a deliberate design choice, not an accident of integration:

- **Dual-package layouts are common.** Python repos that add a CLI typically already have a library package named after the project. `target_repo=recipes` would produce `recipes/` — colliding with the host repo's existing `recipes/` package. The `_cli` suffix (`recipes_cli/`) avoids this by convention.
- **Clean separation of concerns.** The CLI package is project support tooling — it orchestrates and delegates but doesn't contain domain logic. A distinct name makes the boundary visible in the filesystem, imports, and coverage reports.
- **No manual override needed at bake time.** Before this convention, integrating a baked CLI required overriding `package_name` to avoid collisions. Now the default is safe for the common case.
- **Template-vs-integration boundary.** The template's Makefile covers only the `_cli` package (`--cov={{cookiecutter.package_name}}`). The host repo's Makefile is where you add coverage for both packages (`--cov=recipes --cov=recipes_cli`). This keeps the template self-contained.

## CLI.md as a scope document

The template now includes a `CLI.md` that documents:

- The CLI's purpose as **programmatic project support** (not application logic)
- Architecture: Click `OrderedGroup` entry point under `<package>/tui/cli.py`
- **Development standards** — every subcommand (new and pre-existing) must:
  1. Be built with **red/green TDD** (failing test first, then implementation)
  2. Use **Pydantic type signatures** for structured data (runtime validation + self-documenting schemas)
  3. Pass **`mypy`** cleanly with the strict settings in `pyproject.toml`
- How to add subcommands (now includes a three-step workflow: write failing test, implement with Pydantic model, verify with `make test` and `make mypy`)
- The delegation pattern between Makefile targets and CLI subcommands

The root project's `CLI.md` is the concrete instance; the template's `CLI.md` uses `{{cookiecutter.package_name}}` and `{{cookiecutter.project_slug}}` variables so every baked project gets its own version.

Key framing: Makefile targets stay as the stable developer interface. The CLI supplements Make for tasks that need argument parsing, Python-native logic, or composition. A Makefile target can delegate to the CLI (`@recipes bake --template python-project`), but the CLI doesn't replace Make.

## Test fixes backported to template

- **`test_commands_listed_alphabetically`**: The original `output.index("help")` matched `--help  Show this message and exit.` in Click's Options section before reaching the `help` command in the Commands section. Fixed to search within `result.output[result.output.index("Commands:"):]` only.
- **`make test` pytest args**: The template's test target was missing `$(PYTHON_DIRS)` as an argument to pytest, so `--doctest-modules` only collected tests from `tests/` (via pyproject.toml's `testpaths`) and never ran doctests in the package source files. Now passes `$(PYTHON_DIRS)` to match the root project's pattern.
