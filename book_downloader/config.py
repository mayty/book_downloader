import logging
from sys import stderr

from loguru import logger
from pydantic import BaseModel, HttpUrl
from yaml import safe_load

from book_downloader.constants import CONFIG_OVERRIDE_PATH, CONFIG_PATH, LOG_LEVEL, LOG_LOCATION, LOG_ROTATION
from book_downloader.lib.helpers import merge_configs
from book_downloader.lib.logging import InterceptHandler
from pathlib import Path  # noqa: TC003


class BotConfig(BaseModel):  # type: ignore[explicit-any]
    token: str


class OpdsConfig(BaseModel):  # type: ignore[explicit-any]
    host: HttpUrl
    root: str


class SqLiteConfig(BaseModel):  # type: ignore[explicit-any]
    file: Path


class AppConfig(BaseModel):  # type: ignore[explicit-any]
    bot: BotConfig
    opds: OpdsConfig
    sqlite: SqLiteConfig


def configure_logging() -> None:
    logging.basicConfig(handlers=[InterceptHandler()], level='INFO', force=True)
    log_format = ' | '.join(  # noqa: FLY002
        (
            '[<lvl>{level:8}</>][<dim>{time:YYYY-MM-DD HH:mm:ss.SSSZ}</>]',
            '{name}:{function}:{line}',
            '<lvl>{message}</>',
            '{extra}',
        )
    )
    logger.remove()
    logger.level('DEBUG', color='<dim>')
    logger.level('INFO', color='<blue>')
    logger.level('SUCCESS', color='<green><bold>')
    logger.level('WARNING', color='<yellow>')
    logger.level('ERROR', color='<red>')
    logger.level('CRITICAL', color='<red><bold>')
    logger.add(stderr, format=log_format, level=LOG_LEVEL)
    logger.add(
        LOG_LOCATION / 'app.log',
        format='',
        serialize=True,
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        filter={'httpx': 100},
    )
    logger.add(
        LOG_LOCATION / 'httpx.log', format='', serialize=True, level=LOG_LEVEL, rotation=LOG_ROTATION, filter='httpx'
    )


def configure() -> AppConfig:
    configure_logging()

    raw_config = safe_load(CONFIG_PATH.read_text('utf-8'))  # type: ignore[misc]
    if CONFIG_OVERRIDE_PATH.exists() and (config_override := CONFIG_OVERRIDE_PATH.read_text('utf-8')):
        merge_configs(raw_config, safe_load(config_override))  # type: ignore[misc]

    return AppConfig(**raw_config)  # type: ignore[misc]


app_config = configure()
