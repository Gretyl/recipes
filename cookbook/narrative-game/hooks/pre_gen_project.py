"""Pre-generation hook for the narrative-game cookiecutter.

Validates ``project_slug`` against the canonical "kebab-case" pattern
that npm packages, GitHub repos, and PyPI projects all share. A
non-zero exit aborts cookiecutter with FailedHookException, which is
caught by tests/test_pre_gen_project.py.

Round 5 of the upstream template will extend this hook to synthesise
a UUID4 IFID when ``ifid`` is empty.
"""
from __future__ import annotations

import re
import sys

SLUG = "{{ cookiecutter.project_slug }}"

# Lowercase letters, digits, hyphens; must start with a letter or
# digit, must end with a letter or digit; no consecutive hyphens.
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main() -> int:
    if not SLUG:
        sys.stderr.write("✗ project_slug must not be empty\n")
        return 1
    if not SLUG_RE.fullmatch(SLUG):
        sys.stderr.write(
            f"✗ project_slug {SLUG!r} is invalid.\n"
            "  Must be lowercase letters/digits separated by single hyphens,\n"
            "  starting and ending with an alphanumeric character.\n"
            "  Examples: my-narrative, the-room, paperclips-2\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
