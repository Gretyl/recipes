import click


@click.group()
def cli() -> None:
    """{{cookiecutter.project_name}}."""


@cli.command()
def hello() -> None:
    """Say hello."""
    click.echo("Hello from {{cookiecutter.package_name}}.tui!")


if __name__ == "__main__":
    cli()
