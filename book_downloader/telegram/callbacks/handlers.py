from asyncio import TaskGroup

from loguru import logger

from book_downloader.config import app_config
from book_downloader.exceptions import (
    InvalidMessageInfoError,
    MessageInfoNotFoundError,
    NoLeftLocationError,
    NoRightLocationError,
    NoUpstreamLocationError,
    ProjectError,
)
from book_downloader.external.file import download_file
from book_downloader.external.opds.models import Entry, OpdsAcquisitionFeed, OpdsFeed
from book_downloader.lib.helpers import url_from_parts
from book_downloader.storate.sqlite.message_info import message_info_repository
from book_downloader.telegram.common.markup import ItalicTag
from book_downloader.telegram.common.message import generate_message, get_new_message_info
from book_downloader.telegram.constants import Commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from book_downloader.telegram.data.message_info import MessageInfo
    from telegram.ext import ContextTypes
    from telegram import CallbackQuery, InlineKeyboardMarkup, Update


class CallbackHandler:
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update = update
        self.context = context

    @property
    def message_id(self) -> int:
        message = self.update_query.message
        assert message is not None

        return message.message_id

    @property
    def update_query(self) -> CallbackQuery:
        query = self.update.callback_query
        assert query is not None
        return query

    async def get_message_info(self) -> MessageInfo:
        try:
            return message_info_repository.get_message_info(self.message_id)
        except MessageInfoNotFoundError:
            text = '\n'.join(
                map(
                    str,
                    (ItalicTag('Message info not found'), f'Use /{Commands.EXPLORE} command to explore the library'),
                )
            )
            async with TaskGroup() as tg:
                tg.create_task(self.edit_message(text, None))
                tg.create_task(self.answer('Message info not found'))
            raise

    def save_message_info(self, value: MessageInfo) -> None:
        message_info_repository.save_message_info(self.message_id, value)

    async def answer(self, text: str | None = None, *, show_alert: bool = False) -> None:
        await self.update_query.answer(text, show_alert=show_alert)

    async def handle(self) -> tuple[str, InlineKeyboardMarkup] | None:
        raise NotImplementedError

    async def edit_from_message_info(self) -> None:
        message_info = await self.get_message_info()
        text, keyboard = generate_message(message_info)
        await self.edit_message(text, keyboard)

    async def edit_message(self, text: str, keyboard: InlineKeyboardMarkup | None) -> None:
        await self.update_query.edit_message_text(
            text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True
        )

    async def __call__(self) -> None:
        try:
            await self.handle()
        except ProjectError as exc:
            logger.error('FailedToHandleCallback', reason=str(exc))
            await self.answer(str(exc), show_alert=True)


class InvalidCallbackHandler(CallbackHandler):
    async def handle(self) -> None:
        async with TaskGroup() as tg:
            tg.create_task(self.answer('Invalid callback'))
            tg.create_task(self.edit_message('Invalid callback', None))


class BackCallback(CallbackHandler):
    async def handle(self) -> None:
        message_info = await self.get_message_info()

        if (
            isinstance(message_info.opds_feed, OpdsAcquisitionFeed)
            and message_info.opds_feed.selected_entry is not None
        ):
            message_info.opds_feed.selected_entry = None
        else:
            if message_info.up_location is None:
                raise NoUpstreamLocationError

            old_location = message_info.opds_feed.location
            new_message_info = await get_new_message_info(message_info.up_location.location)
            new_message_info.up_location = message_info.up_location.up_location
            new_message_info.set_subpage_by_location(old_location)
            message_info = new_message_info

        self.save_message_info(message_info)
        await self.edit_from_message_info()


class RightCallback(CallbackHandler):
    async def handle(self) -> None:
        message_info = await self.get_message_info()

        if message_info.current_subpage + 1 < len(message_info.subpages):
            message_info.current_subpage += 1
            self.save_message_info(message_info)
        else:
            if message_info.opds_feed.next_location is None:
                raise NoRightLocationError

            new_message_info = await get_new_message_info(message_info.opds_feed.next_location)
            new_message_info.up_location = message_info.up_location
            new_message_info.left_location = message_info.to_short_info()
            self.save_message_info(new_message_info)

        await self.edit_from_message_info()


class LeftCallback(CallbackHandler):
    async def handle(self) -> None:
        message_info = await self.get_message_info()

        if message_info.current_subpage > 0:
            message_info.current_subpage -= 1
            self.save_message_info(message_info)
        else:
            if message_info.left_location is None:
                raise NoLeftLocationError

            new_message_info = await get_new_message_info(message_info.left_location.location)
            new_message_info.up_location = message_info.up_location
            new_message_info.left_location = message_info.left_location.left_location
            new_message_info.current_subpage = len(new_message_info.subpages) - 1

            self.save_message_info(new_message_info)

        await self.edit_from_message_info()


class EnterCallback(CallbackHandler):
    @property
    def entry_index(self) -> int:
        data = self.update_query.data
        assert isinstance(data, str)
        return int(data.split('_', 1)[1])

    async def handle_opds_feed(self, message_info: MessageInfo) -> None:
        _, new_location = message_info[self.entry_index]
        assert isinstance(new_location, Entry)
        new_message_info = await get_new_message_info(new_location.link)
        new_message_info.up_location = message_info.to_short_info()
        self.save_message_info(new_message_info)
        await self.edit_from_message_info()

    async def download_and_send_file(self, file_link: str) -> None:
        data, filename = await download_file(file_link)
        chat = self.update.effective_chat
        assert chat is not None
        await self.context.bot.send_document(
            chat_id=chat.id,
            document=data,
            filename=filename,
        )

    async def handle_acquisition_feed(self, message_info: MessageInfo) -> None:
        feed = message_info.opds_feed
        assert isinstance(feed, OpdsAcquisitionFeed)

        if feed.selected_entry is None:
            feed.selected_entry = self.entry_index
            self.save_message_info(message_info)
            await self.edit_from_message_info()
        else:
            assert feed.selected_entry is not None
            link = feed.entries[feed.selected_entry].acquisition_links[self.entry_index]
            file_path = link.link
            file_link = url_from_parts(str(app_config.opds.host), file_path)

            link.is_downloaded = True
            self.save_message_info(message_info)

            logger.info('RetrievingFile', uri=file_link)

            async with TaskGroup() as tg:
                tg.create_task(self.download_and_send_file(file_link))
                tg.create_task(self.edit_from_message_info())
                tg.create_task(self.answer('Sending file...'))

    async def handle(self) -> None:
        message_info = await self.get_message_info()

        if isinstance(message_info.opds_feed, OpdsFeed):
            await self.handle_opds_feed(message_info)
        elif isinstance(message_info.opds_feed, OpdsAcquisitionFeed):
            await self.handle_acquisition_feed(message_info)
        else:
            raise InvalidMessageInfoError


class NoopCallback(CallbackHandler):
    async def handle(self) -> None:
        await self.answer()
