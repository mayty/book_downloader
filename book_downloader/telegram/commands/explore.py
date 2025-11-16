from book_downloader.config import app_config
from book_downloader.storate.sqlite.message_info import message_info_repository
from book_downloader.telegram.common.message import generate_message, get_new_message_info
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


async def handle_explore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    message_info = await get_new_message_info(app_config.opds.root)

    text, keyboard = generate_message(message_info)

    chat = update.effective_chat
    assert chat is not None

    message = await chat.send_message(parse_mode='HTML', text=text, reply_markup=keyboard)

    message_info_repository.save_message_info(message.message_id, message_info)
