# {{cookiecutter.project_name}}

## Scope

```
{{cookiecutter.package_name}}/     # Library code — domain logic, importable modules
tests/                             # Test suite
```

## Development standards

1. **Red/green TDD.** Write a failing test *first* (`red`), then implement just enough code to make it pass (`green`).
2. **Pydantic type signatures.** Structured data must be expressed as Pydantic models.
3. **Clean `mypy`.** All code must pass `mypy` with the strict settings defined in `pyproject.toml`. Run `make mypy` before committing.

## Makefile targets

Use `make <target>` for everyday development tasks. Run `make` with no arguments to see all targets.

| Target | Description | When to use |
|---|---|---|
| `make test` | Lint, format, type-check, then run pytest with coverage. | Before every commit. |
| `make check` | Lint and auto-fix with ruff. | Quick lint pass. |
| `make format` | Format code with ruff. | After writing new code. |
| `make mypy` | Type-check with strict mypy (runs format and check first). | Before committing type-sensitive changes. |
| `make clean` | Remove build, cache, venv, lock, and dist artifacts. | When resetting the dev environment. |
| `make dist` | Validate versions, tags, and build a release. | At release time only. |

**Tip:** `make test` is the single command that gates commits — it runs `check`, `format`, `mypy`, and `pytest` in sequence so you catch lint, formatting, type, and logic issues in one pass.

## Release sequence

Cutting a release has to stay atomic: the commit tagged `vX.Y.Z` must contain a `pyproject.toml` version of `X.Y.Z`, a `CHANGELOG.md` whose top dated section is `[X.Y.Z]`, **and** a `uv.lock` regenerated against that `pyproject.toml`. `make dist` validates all three; if any drifts, the build fails — or worse, ships a tag whose `uv sync --frozen` doesn't reproduce.

1. Bump the version in `pyproject.toml`.
2. In `CHANGELOG.md`, rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD` and reopen an empty `[Unreleased]` above it.
3. Run `uv sync` to regenerate `uv.lock` against the new version. **Do this before committing** — `make test` runs `uv sync` implicitly, so running it post-commit strands lockfile changes outside the release commit.
4. Stage `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` together. Commit as `chore(release): prepare vX.Y.Z`.
5. Tag the commit with an **annotated** tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`. Verify with `git cat-file -t vX.Y.Z` — must print `tag`, not `commit`. Lightweight tags (`git tag vX.Y.Z` with no `-a`) strand the tagger identity, timestamp, and message that `git describe`, `git log --decorate`, and the GitHub release UI all read.
6. `make dist` validates HEAD/tag/CHANGELOG/version match and a clean tree, then emits `dist/*.tar.gz` and `*.whl`. Push branch and tag: `git push origin <branch> && git push origin vX.Y.Z`.

Published tags are immutable on the git server (tag delete and tag force-push are both rejected). If a release commit lands with drift, the recovery path is a new patch version — not a retagged `X.Y.Z`.

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) on the subject line:

```
<type>(<scope>): <short summary>
```

Allowed **types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`.

Suggested **scopes** for this project: `lib` (library code under `{{cookiecutter.package_name}}/`), `tests`, `docs`, `deps`. Omit the scope for cross-cutting changes that span multiple areas.

Tests and the implementation they drive land as **separate commits** so the red→green transition is observable in `git log`.

## Pull Request Conventions

When opening or updating a pull request, summarize the scope of the feature branch across all atomic commits in the **PR title**. Write the **PR body** as a narrative summary of what changed and why — not a commit list. GitHub already surfaces the full commit log; duplicating it in the body is noise during review.
