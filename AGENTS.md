# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of Cookiecutter templates, tooling for scaffolding Python projects, and a uv-managed Python project environment. The primary template is `cookbook/python-project/`, which generates a uv-managed Python project with ruff, mypy, pytest, and direnv support.

## Key Commands

Set up the development environment:

```bash
uv sync && direnv allow
```

### Makefile targets

Run `make help` to list all targets. The most important ones:

| Target | What it does | When to use it |
|--------|-------------|----------------|
| `make test` | Runs `check` + `format`, then `pytest` with coverage and doctests | **Before every commit.** This is the single gate that must pass. |
| `make check` | `ruff check --fix` — lints and auto-fixes | While iterating on code; also runs automatically as part of `make test` |
| `make format` | `ruff format` — formats all Python files | While iterating on code; also runs automatically as part of `make test` |
| `make mypy` | `mypy` over `recipes/`, `recipes_cli/`, and `tests/` (runs `format` + `check` first) | Before committing CLI or library changes — required for CLI code |
| `make clean` | Removes caches, `.venv/`, `uv.lock`, `dist/`, etc. | When you need a fresh environment |
| `make dist` | Runs `test`, then validates version/tag/changelog consistency and builds a release | Release prep only |

**Always run `make test` before committing.** For CLI changes, also run `make mypy` — strict type-checking is required for all `recipes_cli/` code.

### `recipes` CLI

The `recipes` console script (entry point: `recipes_cli.tui.cli:cli`) provides project-support tooling that goes beyond what shell one-liners can do. See `recipes_cli/AGENTS.md` for architecture decisions and development standards (TDD, Pydantic models, mypy).

Available subcommands:

| Subcommand | Purpose | Example |
|------------|---------|---------|
| `recipes generalize` | Create a Cookiecutter template from an existing repo | `recipes generalize --src . --dst /tmp/tpl` |
| `recipes meld makefiles` | Compare two Makefiles and report feature differences | `recipes meld makefiles Makefile other/Makefile -o analysis` |

`recipes meld makefiles` supports four output formats via `--output` / `-o`: `analysis` (default human-readable summary), `prompt` (structured prompt for Claude), `diff` (unified diff), and `json` (machine-readable).

When adding a new CLI subcommand, follow the process in `recipes_cli/AGENTS.md`: write a failing test first, implement with Pydantic models, then verify with `make test` and `make mypy`.

## Commit Conventions

Prefer atomic commits — each commit should contain a single logical change (one feature, one fix, one refactor). Separating concerns into distinct commits makes review easier and keeps `git bisect` useful. It's fine to commit tests and implementation separately when working in a TDD style.

All commits **must** use [Conventional Commits](https://www.conventionalcommits.org/) for the subject line:

```
<type>(<scope>): <short summary>
```

### Types

- **feat** — new feature or functionality
- **fix** — bug fix
- **docs** — documentation-only changes
- **style** — formatting, whitespace, or cosmetic changes (no logic changes)
- **refactor** — code restructuring without changing external behavior
- **test** — adding or updating tests
- **chore** — maintenance tasks, dependency updates, CI config, etc.
- **build** — changes to the build system or tooling
- **ci** — continuous integration configuration changes
- **perf** — performance improvements

### Scopes

Use a scope that identifies the area of the codebase affected:

- **template** — `cookbook/python-project/` template files
- **cli** — `recipes_cli/` CLI package
- **recipes** — `recipes/` Python package
- **tests** — `tests/` test suite
- **docs** — `docs/` or top-level documentation files (README, AGENTS.md, etc.)
- **deps** — dependency or lockfile changes

The scope is required when the change clearly maps to one area. Omit it only for cross-cutting changes that span multiple scopes.

Avoid redundant type/scope pairs where the scope restates the type (e.g., `docs(docs):`, `test(tests):`). When the type already conveys the scope, omit the scope: `docs: update spec with new CLI usage`. Use a scope only when it adds information beyond the type.

### Examples

```
feat(cli): add export subcommand for templates
fix(template): correct pyproject.toml Python version
docs: update spec with new CLI usage
test: add coverage for generalize edge cases
chore(deps): bump ruff to 0.8.x
refactor(recipes): simplify hello_world module
```
