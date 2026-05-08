"""Post-generation hook for the narrative-game-template cookiecutter.

Runs after templates are rendered. Two responsibilities:

1. **Synthesise IFID** when the user did not supply one (the
   ``ifid`` cookiecutter prompt defaulted to ``""``). Twee 3 requires
   a UUID4 in StoryData.
2. **Strip the GitHub workflow** when ``include_github_workflow`` is
   ``"no"`` — mirrors the conditional-cleanup idiom from the grimoire
   repo's repo-cli template.

Note: pre_gen_project runs *before* rendering and cannot mutate the
cookiecutter context, so per-bake values like a fresh UUID must be
written here, into the rendered files.
"""
from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

PROJECT_ROOT = Path.cwd()
STORYDATA = PROJECT_ROOT / "src" / "StoryData.twee"

USER_IFID = "{{ cookiecutter.ifid }}"
INCLUDE_WORKFLOW = "{{ cookiecutter.include_github_workflow }}" == "yes"


def synthesise_ifid_if_blank() -> None:
    """Replace `"ifid": ""` with a fresh UUID4 in StoryData.twee."""
    if USER_IFID:
        return
    if not STORYDATA.is_file():
        # Round 6 will tighten this; for now, just bail quietly so the
        # missing-file failure surfaces in tests/test_bake_default.py.
        return
    fresh = str(uuid.uuid4())
    content = STORYDATA.read_text()
    new_content, replaced = re.subn(
        r'("ifid"\s*:\s*)""',
        rf'\1"{fresh}"',
        content,
        count=1,
    )
    if replaced:
        STORYDATA.write_text(new_content)


def strip_github_workflow_if_disabled() -> None:
    if not INCLUDE_WORKFLOW:
        shutil.rmtree(PROJECT_ROOT / ".github", ignore_errors=True)


def main() -> None:
    synthesise_ifid_if_blank()
    strip_github_workflow_if_disabled()


if __name__ == "__main__":
    main()
