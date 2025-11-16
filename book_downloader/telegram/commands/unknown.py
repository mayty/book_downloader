from typing import TYPE_CHECKING

from book_downloader.telegram.constants import Commands

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    message = update.message
    assert message is not None
    text = message.text
    assert text is not None
    command = text.split()[0].split('@')[0]

    chat = update.effective_chat
    assert chat is not None
    await chat.send_message(text=f'Unknown command <{command}>, use /{Commands.HELP} for help')
