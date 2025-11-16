from os import environ
from pathlib import Path

from book_downloader.exceptions import NoConfigFileError

_raw_config_path = environ.get('CONFIG_PATH')
if not _raw_config_path:
    raise NoConfigFileError

CONFIG_PATH = Path(_raw_config_path)
CONFIG_OVERRIDE_PATH = Path(environ.get('CONFIG_OVERRIDE_PATH', '/dev/null'))

LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO')
LOG_LOCATION = Path(environ.get('LOG_LOCATION', '/var/log/book_downloader'))
LOG_ROTATION = environ.get('LOG_ROTATION', '100 MB')
