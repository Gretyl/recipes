#!/usr/bin/env python3
"""Create a Cookiecutter template from an existing repo's layout.

Usage:
  python scripts/make_cookiecutter_template.py --src . --dst /tmp

The script creates a template folder under --dst with:
  - cookiecutter.json
  - {{cookiecutter.project_slug}}/ (project contents)

It detects the primary package directory (first top-level dir containing __init__.py)
and replaces it with {{cookiecutter.package_name}} while updating references in
text files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

DEFAULT_EXCLUDES = {
    ".DS_Store",
    ".coverage",
    ".direnv",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "uv.lock",
}

TEMPLATE_EXTENSIONS = {
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

TEMPLATE_FILENAMES = {
    ".envrc",
    ".gitattributes",
    ".gitignore",
    "Dockerfile",
    "Makefile",
    "Procfile",
}


def detect_package_dir(src: Path) -> str | None:
    for entry in src.iterdir():
        if entry.is_dir() and (entry / "__init__.py").exists():
            return entry.name
    return None


def should_exclude(path: Path, excludes: set[str]) -> bool:
    parts = set(path.parts)
    return any(part in excludes for part in parts)


def is_templatable_file(path: Path) -> bool:
    return path.suffix in TEMPLATE_EXTENSIONS or path.name in TEMPLATE_FILENAMES


def safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Cookiecutter template")
    parser.add_argument("--src", default=".", help="Source repo root")
    parser.add_argument("--dst", required=True, help="Destination directory")
    parser.add_argument(
        "--template-name",
        default=None,
        help="Template folder name (default: cookiecutter-<project_slug>)",
    )

    args = parser.parse_args()

    src = Path(args.src).resolve()
    dst_root = Path(args.dst).resolve()

    package_name = detect_package_dir(src)

    # Derive template variables from the source project
    project_slug = src.name
    project_name = project_slug.replace("-", " ").replace("_", " ").title()
    pkg = package_name or project_slug.replace("-", "_")

    template_name = args.template_name or f"cookiecutter-{project_slug}"
    template_root = dst_root / template_name

    excludes = set(DEFAULT_EXCLUDES)

    if template_root.exists():
        raise SystemExit(f"Template folder already exists: {template_root}")

    template_root.mkdir(parents=True)

    cookiecutter_json = {
        "project_name": project_name,
        "project_slug": project_slug,
        "package_name": pkg,
    }

    (template_root / "cookiecutter.json").write_text(
        json.dumps(cookiecutter_json, indent=2) + "\n",
        encoding="utf-8",
    )

    project_root = template_root / "{{cookiecutter.project_slug}}"
    project_root.mkdir()

    for root, dirs, files in os.walk(src):
        root_path = Path(root)
        if should_exclude(root_path, excludes):
            continue

        rel_root = root_path.relative_to(src)
        if rel_root == Path("."):
            rel_root = Path()

        # Map package directory to cookiecutter variable
        rel_parts = []
        for part in rel_root.parts:
            if package_name and part == package_name:
                rel_parts.append("{{cookiecutter.package_name}}")
            else:
                rel_parts.append(part)

        dest_root = project_root.joinpath(*rel_parts)
        dest_root.mkdir(parents=True, exist_ok=True)

        # Prune excluded dirs
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d, excludes)]

        for file_name in files:
            if file_name in excludes:
                continue
            src_file = root_path / file_name
            dest_file = dest_root / file_name

            if is_templatable_file(src_file):
                content = safe_read_text(src_file)
                if content is None:
                    shutil.copy2(src_file, dest_file)
                    continue

                if package_name:
                    content = re.sub(
                        rf"\b{re.escape(package_name)}\b",
                        "{{cookiecutter.package_name}}",
                        content,
                    )

                # Replace project name in pyproject.toml if present
                if src_file.name == "pyproject.toml":
                    content = re.sub(
                        r'(name\s*=\s*)"[^"]+"',
                        r'\1"{{cookiecutter.project_slug}}"',
                        content,
                        count=1,
                    )
                    # Template the description field
                    content = re.sub(
                        r'(description\s*=\s*)"[^"]+"',
                        r'\1"My take on {{cookiecutter.project_name}}"',
                        content,
                        count=1,
                    )

                # Replace project_name in README heading
                if src_file.name == "README.md":
                    content = re.sub(
                        r"^#\s+.+",
                        "# {{cookiecutter.package_name}}",
                        content,
                        count=1,
                    )

                dest_file.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(src_file, dest_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
