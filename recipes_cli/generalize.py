"""Create a Cookiecutter template from an existing repo's layout.

CLI wrapper lives in recipes_cli.tui.cli.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pathspec
from pydantic import BaseModel

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


class GeneralizeArgs(BaseModel):
    """Validated inputs for the generalize command."""

    src: Path
    dst: Path
    template_name: str | None = None


class GeneralizeResult(BaseModel):
    """Structured output from a successful generalize run."""

    template_root: Path
    cookiecutter_json: dict[str, str]
    package_name: str | None


def detect_package_dir(src: Path) -> str | None:
    """Find the first top-level directory containing __init__.py."""
    for entry in src.iterdir():
        if entry.is_dir() and (entry / "__init__.py").exists():
            return entry.name
    return None


def _should_exclude(path: Path, excludes: set[str]) -> bool:
    parts = set(path.parts)
    return any(part in excludes for part in parts)


def _is_templatable_file(path: Path) -> bool:
    return path.suffix in TEMPLATE_EXTENSIONS or path.name in TEMPLATE_FILENAMES


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _load_gitignore_spec(src: Path) -> pathspec.PathSpec | None:
    gitignore = src / ".gitignore"
    if not gitignore.exists():
        return None
    return pathspec.PathSpec.from_lines(
        "gitwildmatch", gitignore.read_text().splitlines()
    )


def _load_gitattributes_binaries(src: Path) -> set[str]:
    ga = src / ".gitattributes"
    binaries: set[str] = set()
    if not ga.exists():
        return binaries
    for line in ga.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and "binary" in parts[1:]:
            binaries.add(parts[0])
    return binaries


def _is_binary_by_gitattributes(rel_path: str, binary_patterns: set[str]) -> bool:
    for pattern in binary_patterns:
        if pathspec.PathSpec.from_lines("gitwildmatch", [pattern]).match_file(rel_path):
            return True
    return False


def _apply_template_substitutions(
    content: str, src_file: Path, package_name: str | None
) -> str:
    """Replace project-specific values with cookiecutter template variables."""
    if package_name:
        content = re.sub(
            rf"\b{re.escape(package_name)}\b",
            "{{cookiecutter.package_name}}",
            content,
        )

    if src_file.name == "pyproject.toml":
        content = re.sub(
            r'(name\s*=\s*)"[^"]+"',
            r'\1"{{cookiecutter.project_slug}}"',
            content,
            count=1,
        )
        content = re.sub(
            r'(description\s*=\s*)"[^"]+"',
            r'\1"My take on {{cookiecutter.project_name}}"',
            content,
            count=1,
        )

    if src_file.name == "README.md":
        content = re.sub(
            r"^#\s+.+",
            "# {{cookiecutter.package_name}}",
            content,
            count=1,
        )

    return content


def _process_file(
    src_file: Path,
    dest_file: Path,
    rel_file: str,
    package_name: str | None,
    binary_patterns: set[str],
) -> None:
    """Process a single file: apply template substitutions or copy as-is."""
    file_is_binary = _is_binary_by_gitattributes(rel_file, binary_patterns)

    if file_is_binary or not _is_templatable_file(src_file):
        shutil.copy2(src_file, dest_file)
        return

    content = _safe_read_text(src_file)
    if content is None:
        shutil.copy2(src_file, dest_file)
        return

    content = _apply_template_substitutions(content, src_file, package_name)
    dest_file.write_text(content, encoding="utf-8")


def _template_dir_parts(parts: tuple[str, ...], package_name: str | None) -> list[str]:
    """Map directory path parts to cookiecutter template variables."""
    return [
        "{{cookiecutter.package_name}}" if package_name and part == package_name else part
        for part in parts
    ]


def generalize(args: GeneralizeArgs) -> GeneralizeResult:
    """Convert a Python repo into a Cookiecutter template.

    Raises ``SystemExit`` on fatal errors (e.g. destination already exists).
    """
    src = args.src.resolve()
    dst_root = args.dst.resolve()

    package_name = detect_package_dir(src)

    project_slug = src.name
    project_name = project_slug.replace("-", " ").replace("_", " ").title()
    pkg = package_name or project_slug.replace("-", "_")

    template_name = args.template_name or f"cookiecutter-{project_slug}"
    template_root = dst_root / template_name

    excludes = set(DEFAULT_EXCLUDES)
    gitignore_spec = _load_gitignore_spec(src)
    binary_patterns = _load_gitattributes_binaries(src)

    if template_root.exists():
        raise SystemExit(f"Template folder already exists: {template_root}")

    template_root.mkdir(parents=True)

    cookiecutter_json: dict[str, str] = {
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
        if _should_exclude(root_path, excludes):
            continue

        rel_root = root_path.relative_to(src)
        if rel_root == Path("."):
            rel_root = Path()

        if gitignore_spec and rel_root != Path():
            rel_root_str = str(rel_root) + "/"
            if gitignore_spec.match_file(rel_root_str):
                dirs.clear()
                continue

        rel_parts = _template_dir_parts(rel_root.parts, package_name)
        dest_root = project_root.joinpath(*rel_parts)
        dest_root.mkdir(parents=True, exist_ok=True)

        dirs[:] = [
            d
            for d in dirs
            if not _should_exclude(root_path / d, excludes)
            and not (
                gitignore_spec
                and gitignore_spec.match_file(
                    str((rel_root / d) if rel_root != Path() else Path(d)) + "/"
                )
            )
        ]

        for file_name in files:
            if file_name in excludes:
                continue

            src_file = root_path / file_name
            rel_file = str(rel_root / file_name) if rel_root != Path() else file_name

            if gitignore_spec and gitignore_spec.match_file(rel_file):
                continue

            _process_file(
                src_file, dest_root / file_name, rel_file, package_name, binary_patterns
            )

    return GeneralizeResult(
        template_root=template_root,
        cookiecutter_json=cookiecutter_json,
        package_name=package_name,
    )
