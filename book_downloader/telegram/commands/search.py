import re

from book_downloader.storate.sqlite.message_info import message_info_repository
from book_downloader.telegram.common.message import generate_message, get_new_message_info_from_search
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    message = update.message
    assert message is not None
    text = message.text
    assert text is not None
    search_text = re.sub(r'[\s\n]+', ' ', text.strip())
    chat = update.effective_chat
    assert chat is not None

    if not search_text:
        await chat.send_message(text='Nothing to search for')
        return

    message_info = await get_new_message_info_from_search(search_text)

    text, keyboard = generate_message(message_info)

    message = await chat.send_message(parse_mode='HTML', text=text, reply_markup=keyboard)

    message_info_repository.save_message_info(message.message_id, message_info)
