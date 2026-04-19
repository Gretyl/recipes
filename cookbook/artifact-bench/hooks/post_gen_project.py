"""Post-generation hook for the artifact-bench cookiecutter template.

When ``include_example_artifact`` is "no" (the default), this hook
removes the bundled ``src/hello-artifact/`` tree and writes a
``src/.gitkeep`` so the empty directory survives in version control.

When the flag is "yes", the example tree is kept verbatim and no
``.gitkeep`` is written — the example files are enough to keep the
directory tracked.
"""

import shutil
from pathlib import Path

INCLUDE_EXAMPLE = "{{ cookiecutter.include_example_artifact }}" == "yes"

src = Path("src")
example = src / "hello-artifact"

if not INCLUDE_EXAMPLE:
    shutil.rmtree(example, ignore_errors=True)
    src.mkdir(exist_ok=True)
    (src / ".gitkeep").touch()
