import click

from book_downloader.cli import command_groups


@click.group()
def cli_root() -> None: ...


for command_group in command_groups:
    cli_root.add_command(command_group)
