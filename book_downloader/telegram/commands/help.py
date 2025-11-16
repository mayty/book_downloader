from telegram import KeyboardButton, ReplyKeyboardMarkup, Update

from book_downloader.telegram.constants import Commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import ContextTypes


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    chat = update.effective_chat
    assert chat is not None
    await chat.send_message(
        text='\n'.join(
            (
                f'Use /{Commands.HELP} to get this message',
                f'Use /{Commands.EXPLORE} to navigate OPDS feed',
                '',
                'Or simply send a message with a search query',
            )
        ),
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(f'/{Commands.EXPLORE}')], [KeyboardButton(f'/{Commands.HELP}')]],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder='Search by title or author',
        ),
    )
