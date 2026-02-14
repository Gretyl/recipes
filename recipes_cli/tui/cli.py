from pathlib import Path

import click

from recipes_cli.generalize import GeneralizeArgs, generalize
from recipes_cli.meld import MeldMakefilesArgs, meld_makefiles


class OrderedGroup(click.Group):
    """A Click group that lists commands in alphabetical order."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(super().list_commands(ctx))


@click.group(cls=OrderedGroup, invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Recipes CLI."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.pass_context
def help(ctx: click.Context) -> None:
    """Show this help message and exit."""
    parent = ctx.parent
    if parent is not None:
        click.echo(parent.get_help())


# ---------------------------------------------------------------------------
# recipes generalize
# ---------------------------------------------------------------------------


@cli.command("generalize")
@click.option("--src", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--dst", required=True, type=click.Path(path_type=Path))
@click.option("--template-name", default=None)
def generalize_cmd(src: Path, dst: Path, template_name: str | None) -> None:
    """Create a Cookiecutter template from an existing repo."""
    args = GeneralizeArgs(src=src, dst=dst, template_name=template_name)
    result = generalize(args)
    click.echo(f"Template created: {result.template_root}")
    click.echo(f"  package detected: {result.package_name or '(none)'}")
    click.echo(f"  cookiecutter.json: {result.cookiecutter_json}")


# ---------------------------------------------------------------------------
# recipes meld (group) -> recipes meld makefiles
# ---------------------------------------------------------------------------


@cli.group(cls=OrderedGroup)
def meld() -> None:
    """Meld features between files."""


@meld.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Choice(["analysis", "prompt", "diff", "json"]),
    default="analysis",
)
def makefiles(source: Path, target: Path, output: str) -> None:
    """Meld features from source Makefile to target Makefile."""
    args = MeldMakefilesArgs(source=source, target=target, output=output)  # type: ignore[arg-type]
    result = meld_makefiles(args)
    click.echo(result)


if __name__ == "__main__":
    cli()
