"""Post-generation hook for the python-project cookiecutter template.

When ``include_github_workflows`` is "no", this hook removes:
- The ``.github/`` directory (CI workflow).

The hook leaves all other project scaffold in place so non-GitHub
users still get a fully functional project.
"""

import shutil

INCLUDE_WORKFLOWS = "{{ cookiecutter.include_github_workflows }}" == "yes"

if not INCLUDE_WORKFLOWS:
    shutil.rmtree(".github", ignore_errors=True)
