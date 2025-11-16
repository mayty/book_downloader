from book_downloader.external.opds import opds_service
from book_downloader.external.opds.models import OpdsAcquisitionFeed
from book_downloader.telegram.common.acquisition_entry import generate_acquisition_message
from book_downloader.telegram.common.feed import generate_feed_message
from book_downloader.telegram.data.message_info import MessageInfo
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import InlineKeyboardMarkup


async def get_new_message_info(location: str) -> MessageInfo:
    entries = await opds_service.list(location)

    return MessageInfo(
        opds_feed=entries,
    )


async def get_new_message_info_from_search(query: str) -> MessageInfo:
    entries = await opds_service.search(query)

    return MessageInfo(
        opds_feed=entries,
    )


def generate_message(message_info: MessageInfo) -> tuple[str, InlineKeyboardMarkup]:
    if isinstance(message_info.opds_feed, OpdsAcquisitionFeed) and message_info.opds_feed.selected_entry is not None:
        return generate_acquisition_message(message_info)
    return generate_feed_message(message_info)
