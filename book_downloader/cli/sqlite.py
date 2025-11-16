import click


@click.group('sqlite')
def sqlite_group() -> None:
    """> SQLite commands"""


@sqlite_group.command('shell')  # type: ignore[misc]
def sqlite_shell() -> None:
    """Enter sqlite shell"""
    from shutil import which
    from book_downloader.config import app_config
    from os import execv
    from loguru import logger

    sqlite_path = which('sqlite3')
    if not sqlite_path:
        msg = 'sqlite3 not installed'
        raise FileNotFoundError(msg)

    args = (sqlite_path, '-box', str(app_config.sqlite.file.resolve()))

    logger.info('LaunchingSqliteShell', executable=sqlite_path, args=args)
    execv(sqlite_path, args)  # noqa: S606


@sqlite_group.command('flush')  # type: ignore[misc]
def flush_sqlite() -> None:
    """Flush sqlite database"""
    from book_downloader.config import app_config
    from loguru import logger

    logger.info('FlushingSqliteDatabase')
    app_config.sqlite.file.unlink(missing_ok=True)
    logger.info('DatabaseFlushed')
