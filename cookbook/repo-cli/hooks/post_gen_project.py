"""Post-generation hook for the repo-cli cookiecutter template.

When ``include_github_workflows`` is "no", this hook removes:
- The ``.github/`` directory (CI automation that applies the template on push)

Template actions (``template.py``, tests, ``requirements.txt``) are always
included so that non-GitHub users still have access to
``{{cookiecutter.target_repo}} template`` commands.
"""

import shutil

INCLUDE_WORKFLOWS = "{{ cookiecutter.include_github_workflows }}" == "yes"

if not INCLUDE_WORKFLOWS:
    shutil.rmtree(".github", ignore_errors=True)
