from book_downloader.config import app_config
from book_downloader.external.opds.service import OpdsService

opds_service = OpdsService(app_config.opds.host)
