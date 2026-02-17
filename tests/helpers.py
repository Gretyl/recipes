"""Shared test utilities."""

import pathlib


def paths(directory: pathlib.Path) -> set[str]:
    """Return a set of all relative paths (files and dirs) under *directory*."""
    all_paths = list(directory.glob("**/*"))
    return {
        str(p.relative_to(directory))
        for p in all_paths
        if str(p.relative_to(directory)) != "."
    }
