"""Template management for the {{cookiecutter.target_repo}} README Cog template.

This module is the self-contained implementation of the ``{{cookiecutter.target_repo}} template``
subcommand.  It owns both the business logic (constants, models, helpers) and
the Click command group that ``{{cookiecutter.package_name}}.tui.cli`` registers onto the root CLI.
"""

from pathlib import Path

import click
from pydantic import BaseModel

# Cog delimiters
COG_OPEN: str = "<!--[[[cog"
COG_CLOSE: str = "]]]-->"
COG_END: str = "<!--[[[end]]]-->"

PLACEHOLDER: str = "<template placeholder>"

# Stub template code — a no-op that produces no output when Cog processes it.
# Replace this with real template logic for your repository.
TEMPLATE_CODE: str = "..."


class TemplateOutput(BaseModel):
    """Result of retrieving the template code."""

    code: str


class ApplyResult(BaseModel):
    """Result of applying the template to a README."""

    readme_path: str
    placeholder_found: bool
    content_written: bool


class PrepareResult(BaseModel):
    """Result of preparing a README by replacing the Cog block with the placeholder."""

    readme_path: str
    cog_block_found: bool
    placeholder_written: bool


def get_template_code() -> TemplateOutput:
    """Return the Cog template code."""
    return TemplateOutput(code=TEMPLATE_CODE)


def wrap_with_cog(code: str) -> str:
    """Wrap Python code with Cog markers for embedding in markdown."""
    return f"{COG_OPEN}\n{code}\n{COG_CLOSE}\n{COG_END}"


def apply_template(readme_path: Path) -> ApplyResult:
    """Replace the last occurrence of the placeholder in a README with the Cog-wrapped template.

    Returns an ApplyResult describing what happened.
    """
    content = readme_path.read_text()
    idx = content.rfind(PLACEHOLDER)
    if idx == -1:
        return ApplyResult(
            readme_path=str(readme_path),
            placeholder_found=False,
            content_written=False,
        )

    wrapped = wrap_with_cog(TEMPLATE_CODE)
    new_content = content[:idx] + wrapped + content[idx + len(PLACEHOLDER) :]
    readme_path.write_text(new_content)
    return ApplyResult(
        readme_path=str(readme_path),
        placeholder_found=True,
        content_written=True,
    )


def prepare_template(readme_path: Path) -> PrepareResult:
    """Replace the last Cog block (including any cached output) with the placeholder.

    This is the inverse of ``apply_template``.  It finds the last
    ``<!--[[[cog ... <!--[[[end]]]-->`` block and substitutes the
    ``<template placeholder>`` string, restoring the README to a state
    that ``apply_template`` can operate on again.

    Returns a PrepareResult describing what happened.
    """
    content = readme_path.read_text()
    # Find the last Cog opening marker
    cog_start = content.rfind(COG_OPEN)
    if cog_start == -1:
        return PrepareResult(
            readme_path=str(readme_path),
            cog_block_found=False,
            placeholder_written=False,
        )
    # Find the corresponding end marker after the opening
    cog_end = content.find(COG_END, cog_start)
    if cog_end == -1:
        return PrepareResult(
            readme_path=str(readme_path),
            cog_block_found=False,
            placeholder_written=False,
        )
    block_end = cog_end + len(COG_END)
    new_content = content[:cog_start] + PLACEHOLDER + content[block_end:]
    readme_path.write_text(new_content)
    return PrepareResult(
        readme_path=str(readme_path),
        cog_block_found=True,
        placeholder_written=True,
    )


# ---------------------------------------------------------------------------
# Click command group — registered onto the root CLI by {{cookiecutter.package_name}}.tui.cli
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
def template(ctx: click.Context) -> None:
    """Manage the {{cookiecutter.target_repo}} README Cog template.

    When invoked without a subcommand, outputs the Python template code
    that drives the README's generated content.
    """
    if ctx.invoked_subcommand is None:
        result = get_template_code()
        click.echo(result.code)


@template.command()
@click.option(
    "--readme",
    type=click.Path(exists=False),
    default="README.md",
    help="Path to the README.md file to update.",
)
def apply(readme: str) -> None:
    """Apply the Cog-wrapped template to the README.

    Wraps the template code with Cog markers and substitutes it
    for the last occurrence of '<template placeholder>' in the README.
    """
    readme_path = Path(readme)
    if not readme_path.exists():
        raise click.ClickException(f"README not found: {readme_path}")
    result = apply_template(readme_path)
    if not result.placeholder_found:
        raise click.ClickException(
            f"Placeholder '<template placeholder>' not found in {readme_path}"
        )
    click.echo(f"Template applied to {result.readme_path}")


@template.command()
@click.option(
    "--readme",
    type=click.Path(exists=False),
    default="README.md",
    help="Path to the README.md file to update.",
)
def prepare(readme: str) -> None:
    """Replace the Cog block with <template placeholder>.

    This is the inverse of ``apply``.  It strips the Cog markers and any
    Cog-cached output, leaving a clean placeholder that ``apply`` can
    later fill in again.
    """
    readme_path = Path(readme)
    if not readme_path.exists():
        raise click.ClickException(f"README not found: {readme_path}")
    result = prepare_template(readme_path)
    if not result.cog_block_found:
        raise click.ClickException(
            f"Cog block not found in {readme_path}"
        )
    click.echo(f"Template prepared in {result.readme_path}")
