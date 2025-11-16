from book_downloader.telegram.callbacks.handlers import (
    BackCallback,
    EnterCallback,
    InvalidCallbackHandler,
    LeftCallback,
    NoopCallback,
    RightCallback,
)
from book_downloader.telegram.constants import CallbackCommandPrefixes, CallbackCommands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update

handlers = {
    CallbackCommands.BACK: BackCallback,
    CallbackCommands.RIGHT: RightCallback,
    CallbackCommands.LEFT: LeftCallback,
    CallbackCommands.NOOP: NoopCallback,
}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    callback_data = query.data
    assert isinstance(callback_data, str | type(None))

    if not callback_data:
        return

    try:
        handler = handlers[CallbackCommands(callback_data)](update, context)
    except ValueError, KeyError:
        if callback_data.startswith(CallbackCommandPrefixes.ENTER):
            handler = EnterCallback(update, context)
        else:
            handler = InvalidCallbackHandler(update, context)

    await handler()
