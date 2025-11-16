from contextlib import contextmanager
from sqlite3 import Connection, PARSE_DECLTYPES, Row, connect

from book_downloader.config import app_config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def connections_factory() -> Generator[Connection]:
    connection = connect(app_config.sqlite.file, detect_types=PARSE_DECLTYPES)
    connection.row_factory = Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()
