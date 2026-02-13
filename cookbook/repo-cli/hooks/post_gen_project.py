"""Post-generation hook for the repo-cli cookiecutter template.

When ``include_github_workflow`` is "no", this hook removes:
- The ``.github/`` directory (CI automation that applies the template on push)

Template actions (``template.py``, tests, ``requirements.txt``) are always
included so that non-GitHub users still have access to
``{{cookiecutter.target_repo}} template`` commands.
"""

import shutil

INCLUDE_WORKFLOW = "{{ cookiecutter.include_github_workflow }}" == "yes"

if not INCLUDE_WORKFLOW:
    shutil.rmtree(".github", ignore_errors=True)
