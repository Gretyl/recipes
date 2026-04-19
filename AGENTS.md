# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of Cookiecutter templates, tooling for scaffolding Python projects, and a uv-managed Python project environment. The cookbook ships three templates: `cookbook/python-project/` (uv-managed Python projects with ruff, mypy, pytest, and direnv), `cookbook/repo-cli/` (Click-based CLI packages targeting an existing repo), and `cookbook/artifact-bench/` (Node/TypeScript workbenches for standalone HTML artifacts).

## Key Commands

Set up the development environment:

```bash
uv sync && direnv allow
```

### Makefile targets

Run `make help` to list all targets. The most important ones:

| Target | What it does | When to use it |
|--------|-------------|----------------|
| `make test` | Runs `check` + `format` + `mypy`, then `uv run pytest` with coverage and doctests | **Before every commit.** This is the single gate that must pass. |
| `make check` | `uv run ruff check --fix` — lints and auto-fixes | While iterating on code; also runs automatically as part of `make test` |
| `make format` | `uv run ruff format` — formats all Python files | While iterating on code; also runs automatically as part of `make test` |
| `make mypy` | `uv run mypy` over `recipes/`, `recipes_cli/`, and `tests/` (runs `format` + `check` first) | Also runs automatically as part of `make test` |
| `make clean` | Removes caches, `.venv/`, `uv.lock`, `dist/`, etc. | When you need a fresh environment |
| `make dist` | Runs `test`, then validates version/tag/changelog consistency and builds a release | Release prep only |

**Always run `make test` before committing.** It includes `mypy` — strict type-checking is required for all code.

### `recipes` CLI

The `recipes` console script (entry point: `recipes_cli.tui.cli:cli`) provides project-support tooling that goes beyond what shell one-liners can do. See `recipes_cli/AGENTS.md` for architecture decisions and development standards (TDD, Pydantic models, mypy).

Available subcommands:

| Subcommand | Purpose | Example |
|------------|---------|---------|
| `uv run recipes generalize` | Create a Cookiecutter template from an existing repo | `uv run recipes generalize --src . --dst /tmp/tpl` |
| `uv run recipes meld makefiles` | Compare two Makefiles and report feature differences | `uv run recipes meld makefiles Makefile other/Makefile -o analysis` |

`uv run recipes meld makefiles` supports four output formats via `--output` / `-o`: `analysis` (default human-readable summary), `prompt` (structured prompt for Claude), `diff` (unified diff), and `json` (machine-readable).

When adding a new CLI subcommand, follow the process in `recipes_cli/AGENTS.md`: implement with Pydantic models, then verify with `make test` and `make mypy`.

## TDD Discipline

Implementation work proceeds as red→green pairs: a `test(...)` commit pinning a behavior with a failing assertion, then a `feat(...)` / `fix(...)` commit that flips it green. `make test` is run between each commit so the transition is observable in the log.

### Enumerate the full property list before commit #1

Before writing the first test, draft the complete behavioral contract the change must satisfy. That list has to include:

- **Behavior-specific properties** — what the new code does.
- **Propagation properties** — every input variable (cookiecutter vars, CLI flags, config keys) reaches every site that depends on it.
- **Inverse-branch properties** — both sides of every conditional (hook enabled/disabled, flag on/off) are exercised.
- **Sweep invariants** — "no default values leak", "no un-rendered template tokens", "no TODOs left in shipped output".

Tests for all four categories land as red commits in the main sequence. Writing the sweep or propagation tests *after* the implementation already satisfies them turns TDD into retrofitting — the test pins a property, but there was never a red state to drive the design.

**Behavior-specific, propagation, and inverse-branch tests must land red.** If one of these lands green-on-arrival, split an earlier commit so the red state exists — don't settle for a disclaimer in the commit body. The discipline belongs in the commit graph, not in narration.

**Tree-wide sweep invariants** (e.g., "no default values leak anywhere", "no un-rendered Jinja tokens in the output") are the one exception: they pass only by virtue of every other commit being correct, so there's no single earlier commit where they have a natural red state without artificially breaking something. These may land green-on-arrival, but the commit body must name which earlier commits the sweep guards, so the regression-guard role is explicit.

### Behavior-naming over module-naming

`test(...)` commit subjects name the behavior under design, not the file being touched. Right: `test(template): default bake seeds src/.gitkeep and omits src/hello-artifact`. Wrong: `test(template): add bake tests for artifact-bench`.

## Commit Conventions

Prefer atomic commits — each commit should contain a single logical change (one feature, one fix, one refactor). Separating concerns into distinct commits makes review easier and keeps `git bisect` useful. Tests and implementation land as separate commits — see TDD Discipline above.

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

## Pull Request Conventions

When opening or updating a pull request, summarize the scope of the feature branch across all atomic commits in the **PR title**. Write the **PR body** as a narrative summary of what changed and why — not a commit list. GitHub already surfaces the full commit log; duplicating it in the body is noise during review.
