import click


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
def hello() -> None:
    """Say hello."""
    click.echo("Hello from recipes_cli.tui!")


@cli.command()
@click.pass_context
def help(ctx: click.Context) -> None:
    """Show this help message and exit."""
    parent = ctx.parent
    if parent is not None:
        click.echo(parent.get_help())


if __name__ == "__main__":
    cli()
