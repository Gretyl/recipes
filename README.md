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
python scripts/make_cookiecutter_template.py --src /path/to/repo --dst /path/to/output
```

## Makefile targets

```bash
make test      # ruff check --fix, ruff format, then pytest --doctest-modules --cov
make check     # ruff check --fix
make format    # ruff format
make mypy      # mypy after format+check
make dist      # validate changelog + version, build sdist+wheel
make clean     # remove build/cache/venv/lock artifacts
```
