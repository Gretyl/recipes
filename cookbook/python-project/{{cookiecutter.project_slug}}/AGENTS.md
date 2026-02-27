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
| `make test` | Lint, format, then run pytest with coverage. | Before every commit. |
| `make check` | Lint and auto-fix with ruff. | Quick lint pass. |
| `make format` | Format code with ruff. | After writing new code. |
| `make mypy` | Type-check with strict mypy (runs format and check first). | Before committing type-sensitive changes. |
| `make clean` | Remove build, cache, venv, lock, and dist artifacts. | When resetting the dev environment. |
| `make dist` | Validate versions, tags, and build a release. | At release time only. |

**Tip:** `make test` is the single command that gates commits — it runs `check`, `format`, and `pytest` in sequence so you catch lint, formatting, and logic issues in one pass.
