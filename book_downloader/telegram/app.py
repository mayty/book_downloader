from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from book_downloader.config import app_config
from book_downloader.telegram.callbacks.router import handle_callback
from book_downloader.telegram.commands.explore import handle_explore
from book_downloader.telegram.commands.help import handle_help
from book_downloader.telegram.commands.search import handle_search
from book_downloader.telegram.commands.unknown import handle_unknown_command

from book_downloader.telegram.constants import Commands

__all__ = ['run']


def run() -> None:
    application = ApplicationBuilder().token(app_config.bot.token).build()

    handlers = (
        CommandHandler(Commands.EXPLORE, handle_explore),
        CommandHandler(Commands.START, handle_help),
        CommandHandler(Commands.HELP, handle_help),
        MessageHandler(filters.COMMAND, handle_unknown_command),
        MessageHandler(filters.TEXT, handle_search),
        CallbackQueryHandler(handle_callback),
    )

    application.add_handlers(handlers)

    application.run_polling()
