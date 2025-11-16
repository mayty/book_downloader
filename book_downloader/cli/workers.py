import click


@click.group('workers')
def workers_group() -> None:
    """> Workers management"""


@workers_group.command('telegram')  # type: ignore[misc]
def run_telegram_worker() -> None:
    """Run telegram bot"""
    from book_downloader.telegram.app import run

    run()
