from book_downloader.cli.sqlite import sqlite_group
from book_downloader.cli.workers import workers_group

__all__ = ['command_groups']

command_groups = (workers_group, sqlite_group)
