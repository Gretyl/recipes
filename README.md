# Cookiecutter Templates

This repo stores a ready-to-use Cookiecutter template and a script to generate new
templates from an existing project structure.

## Creating new projects using `cookiecutter`

The baked template lives in `python-project/`. Use `cookiecutter` to create a
fresh project:

```bash
cookiecutter /Users/smshaner/Sandbox/Coding/Python/python-template/python-project
```

Cookiecutter will prompt for:
- `project_name`
- `project_slug`
- `package_name`

To choose a destination folder:

```bash
cookiecutter /Users/smshaner/Sandbox/Coding/Python/python-template/python-project \
  --output-dir /path/to/projects
```

## Creating new templates for various project types

Use the helper script to turn a source repo into a Cookiecutter template.

```bash
python scripts/make_cookiecutter_template.py --src /path/to/source --dst /path/to/output
```

Notes:
- The template is created at `--dst/<template-name>` (default name is
  `cookiecutter-retirement`).
- The script detects the top-level Python package directory (first folder with
  `__init__.py`) and templates it as `{{cookiecutter.package_name}}`.
- Text files have package references and the `pyproject.toml` project name templated.

Optional flags:

```bash
python scripts/make_cookiecutter_template.py \
  --src /path/to/source \
  --dst /path/to/output \
  --template-name my-template \
  --include-lock
```

