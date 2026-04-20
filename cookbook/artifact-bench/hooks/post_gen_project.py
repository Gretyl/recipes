"""Post-generation hook for the artifact-bench cookiecutter template.

Handles two independent flags:

- ``include_example_artifact`` (default "no"): when "no", removes the
  bundled ``src/hello-artifact/`` tree and writes ``src/.gitkeep`` so
  the empty directory survives in version control. When "yes", keeps
  the example tree verbatim and omits the ``.gitkeep``.

- ``include_github_workflows`` (default "yes"): when "no", removes
  the ``.github/`` directory so non-GitHub users get a clean repo.
  When "yes", ships the CI workflow (``ci.yml``) verbatim.

The two conditionals are independent — neither depends on the
other's outcome.
"""

import shutil
from pathlib import Path

INCLUDE_EXAMPLE = "{{ cookiecutter.include_example_artifact }}" == "yes"
INCLUDE_WORKFLOWS = "{{ cookiecutter.include_github_workflows }}" == "yes"

src = Path("src")
example = src / "hello-artifact"

if not INCLUDE_EXAMPLE:
    shutil.rmtree(example, ignore_errors=True)
    src.mkdir(exist_ok=True)
    (src / ".gitkeep").touch()

if not INCLUDE_WORKFLOWS:
    shutil.rmtree(".github", ignore_errors=True)
