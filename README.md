# Recipes

Cookiecutter templates and tooling for scaffolding various project types.

## Available recipes

<!--[[[cog
import pathlib

cookbook = pathlib.Path("cookbook")
templates = sorted(
    d.name for d in cookbook.iterdir()
    if d.is_dir() and (d / "cookiecutter.json").exists()
)
for name in templates:
    notes = cookbook / "notes" / f"{name}.md"
    demo = cookbook / "demos" / f"{name}.md"
    links = []
    if notes.exists():
        links.append(f"[notes](cookbook/notes/{name}.md)")
    if demo.exists():
        links.append(f"[demo](cookbook/demos/{name}.md)")
    if links:
        print(f"* {name} ({' | '.join(links)})")
    else:
        print(f"* {name}")
]]]-->
* artifact-bench ([notes](cookbook/notes/artifact-bench.md) | [demo](cookbook/demos/artifact-bench.md))
* narrative-game ([notes](cookbook/notes/narrative-game.md) | [demo](cookbook/demos/narrative-game.md))
* python-project ([notes](cookbook/notes/python-project.md) | [demo](cookbook/demos/python-project.md))
* repo-cli ([notes](cookbook/notes/repo-cli.md) | [demo](cookbook/demos/repo-cli.md))
<!--[[[end]]]-->

## Quickstart

```bash
uv sync && direnv allow
```

## Creating a project from the template

```bash
cookiecutter cookbook/python-project/
```

## Creating a new template from an existing project

```bash
uv run recipes generalize --src /path/to/repo --dst /path/to/output
```

## Makefile targets

```bash
make check     # uv run ruff check --fix
make clean     # remove build/cache/venv/lock artifacts
make dist      # validate changelog + version, build sdist+wheel
make format    # uv run ruff format
make mypy      # uv run mypy after format+check
make test      # check, format, mypy, then uv run pytest --doctest-modules --cov
```
