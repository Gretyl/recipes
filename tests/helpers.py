"""Shared test utilities."""

import pathlib

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
