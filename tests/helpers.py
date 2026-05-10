"""Shared test utilities."""

import pathlib
from collections.abc import Callable, Iterable

from cookiecutter.main import cookiecutter

COOKBOOK_DIR = pathlib.Path(__file__).parent.parent / "cookbook"


def paths(directory: pathlib.Path) -> set[str]:
    """Return a set of all relative paths (files and dirs) under *directory*."""
    all_paths = list(directory.glob("**/*"))
    return {
        str(p.relative_to(directory))
        for p in all_paths
        if str(p.relative_to(directory)) != "."
    }


def bake(
    template_name: str,
    output_dir: pathlib.Path,
    *,
    extra_context: dict[str, str] | None = None,
) -> pathlib.Path:
    """Bake a cookbook template with ``no_input=True`` and return the baked path.

    ``template_name`` is the directory name under ``cookbook/`` (e.g.
    ``python-project``). ``extra_context`` maps cookiecutter variable names to
    override values; pass the flag's value explicitly even when it matches the
    default, so the contract survives future default flips (see AGENTS.md).
    """
    template_path = COOKBOOK_DIR / template_name
    result = cookiecutter(
        template=str(template_path),
        output_dir=str(output_dir),
        no_input=True,
        extra_context=extra_context or {},
    )
    return pathlib.Path(result)


def makefile_recipe(makefile: str, target: str) -> str:
    """Return the recipe body for ``target:`` in ``makefile``.

    Scans from the target line through every indented (tab/space) line until
    the next top-level target definition. Useful for asserting which commands
    a target invokes without coupling assertions to exact line numbers.

    Raises ``AssertionError`` if the target is not present.
    """
    lines = makefile.splitlines()
    target_marker = f"{target}:"
    try:
        idx = next(i for i, line in enumerate(lines) if line.startswith(target_marker))
    except StopIteration as exc:
        msg = f"target {target!r} not found in Makefile"
        raise AssertionError(msg) from exc
    recipe: list[str] = []
    for line in lines[idx + 1 :]:
        if line and not line.startswith(("\t", " ")):
            break
        recipe.append(line)
    return "\n".join(recipe)


def mermaid_block(markdown: str) -> str:
    """Return the contents of the first ```mermaid fenced block in *markdown*.

    The opening ``` ```mermaid ``` and closing ``` ``` ``` fences are stripped.
    Raises ``AssertionError`` if no block is present.
    """
    fence = "```mermaid"
    start = markdown.find(fence)
    assert start != -1, "no mermaid block found in markdown"
    body_start = start + len(fence)
    end = markdown.find("```", body_start)
    assert end != -1, "mermaid block has no closing fence"
    return markdown[body_start:end]


def text_file_offenders(
    baked: pathlib.Path,
    suffixes: Iterable[str] | None,
    predicate: Callable[[str], bool],
    *,
    extra_names: Iterable[str] = (),
) -> list[pathlib.Path]:
    """Walk every text file under ``baked`` and return paths whose content
    satisfies ``predicate``.

    With ``suffixes`` set, a file qualifies as text if its suffix is in
    that set or its name is in ``extra_names`` (for files like
    ``Makefile`` and ``.gitignore`` that have no traditional extension).
    With ``suffixes=None``, every file is considered — UnicodeDecodeError
    is the binary-skip guard. Returned paths are relative to ``baked``
    for legible failure messages.
    """
    suffix_set = set(suffixes) if suffixes is not None else None
    name_set = set(extra_names)
    offenders: list[pathlib.Path] = []
    for path in baked.rglob("*"):
        if not path.is_file():
            continue
        if (
            suffix_set is not None
            and path.suffix not in suffix_set
            and path.name not in name_set
        ):
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if predicate(text):
            offenders.append(path.relative_to(baked))
    return offenders


def find_default_leaks(
    baked: pathlib.Path,
    defaults: Iterable[str],
    suffixes: Iterable[str] | None = None,
    *,
    extra_names: Iterable[str] = (),
) -> list[tuple[pathlib.Path, str]]:
    """Find ``(path, default_value)`` pairs where any string in ``defaults``
    appears in a text file's contents.

    Useful for custom-context bake tests: every default must be replaced
    by the override, and a leak is a hardcoded substring that escaped
    Jinja substitution. Filtering matches :func:`text_file_offenders` —
    pass ``suffixes=None`` to scan every text file with no suffix gate.
    """
    default_list = list(defaults)
    suffix_set = set(suffixes) if suffixes is not None else None
    name_set = set(extra_names)
    leaks: list[tuple[pathlib.Path, str]] = []
    for path in baked.rglob("*"):
        if not path.is_file():
            continue
        if (
            suffix_set is not None
            and path.suffix not in suffix_set
            and path.name not in name_set
        ):
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for default in default_list:
            if default in text:
                leaks.append((path.relative_to(baked), default))
    return leaks


def find_jinja_leaks(
    baked: pathlib.Path,
    *,
    require_cookiecutter: bool = False,
) -> list[pathlib.Path]:
    """Return paths whose contents contain an unrendered Jinja token.

    With the default ``require_cookiecutter=False``, any file containing
    ``{{`` or ``}}`` is flagged — a strict check that catches every Jinja
    escape that didn't render. With ``require_cookiecutter=True``, only
    files containing both ``{{`` and ``cookiecutter.`` are flagged — useful
    for templates whose baked output legitimately uses ``{{`` for other
    purposes (Jinja escapes in baked Jinja templates, JS object literals
    that look like braces, etc.).

    No suffix filter is applied — Jinja escapes can land in any text file,
    and binary files are skipped via the UnicodeDecodeError guard.
    """
    offenders: list[pathlib.Path] = []
    for path in baked.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if require_cookiecutter:
            if "{{" in text and "cookiecutter." in text:
                offenders.append(path.relative_to(baked))
        elif "{{" in text or "}}" in text:
            offenders.append(path.relative_to(baked))
    return offenders


def readme_section(markdown: str, heading: str) -> str:
    """Return the text under ``## {heading}`` up to the next top-level heading.

    Starts at the ``##`` marker line (included) and ends at the first ``\\n## ``
    after the heading or at end of document. Useful for scoping substring
    assertions to a specific section so incidental matches elsewhere don't
    hide regressions within the section being checked.

    Raises ``AssertionError`` if the section is not present.
    """
    marker = f"## {heading}"
    start = markdown.find(marker)
    assert start != -1, f"README has no {marker!r} section"
    end = markdown.find("\n## ", start + len(marker))
    if end == -1:
        end = len(markdown)
    return markdown[start:end]
