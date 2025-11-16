from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from book_downloader.telegram.common.helpers import itoa
from book_downloader.telegram.common.markup import BoldTag, HtmlTag, ItalicTag, QuoteTag
from book_downloader.telegram.constants import CallbackCommandPrefixes, CallbackCommands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from book_downloader.telegram.data.message_info import MessageInfo
    from book_downloader.external.opds.models import AcquisitionEntry, Entry
    from collections.abc import Generator


def generate_entry_text(i: int, entry: Entry | AcquisitionEntry) -> HtmlTag | str:
    return BoldTag(f'{itoa(i)} {entry.title}')


def generate_message_text(entries: list[tuple[int, Entry | AcquisitionEntry]]) -> Generator[str | HtmlTag]:
    for i, (_, entry) in enumerate(entries, 1):
        yield generate_entry_text(i, entry)


def generate_inline_keyboard(message_info: MessageInfo) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [[]]

    entries = list(message_info.current_subpage_entries())

    keyboard_rows_count = (len(entries) // 4) + 1
    buttons_per_row, leftover_buttons_count = divmod(len(entries), keyboard_rows_count)

    for button_num, (i, _) in enumerate(entries, 1):
        target_buttons_count = buttons_per_row + int(len(rows) <= leftover_buttons_count)
        if len(rows[-1]) >= target_buttons_count:
            rows.append([])
        rows[-1].append(InlineKeyboardButton(text=str(button_num), callback_data=f'{CallbackCommandPrefixes.ENTER}{i}'))

    needs_left = message_info.left_location is not None or message_info.current_subpage > 0
    needs_back = message_info.up_location is not None
    needs_right = (
        message_info.opds_feed.next_location is not None
        or message_info.current_subpage < len(message_info.subpages) - 1
    )

    if any((needs_left, needs_back, needs_right)):
        noop_button = InlineKeyboardButton(text='🚫', callback_data=CallbackCommands.NOOP)
        rows.append(
            [
                InlineKeyboardButton(text='◀️', callback_data=CallbackCommands.LEFT) if needs_left else noop_button,
                InlineKeyboardButton(text='⤴️', callback_data=CallbackCommands.BACK) if needs_back else noop_button,
                InlineKeyboardButton(text='▶️', callback_data=CallbackCommands.RIGHT) if needs_right else noop_button,
            ]
        )

    return InlineKeyboardMarkup(rows)


def generate_feed_message(message_info: MessageInfo) -> tuple[str, InlineKeyboardMarkup]:
    entries_text: list[str | HtmlTag] = []

    if message_info.opds_feed.title:
        entries_text.append(QuoteTag(BoldTag(message_info.opds_feed.title)))

    for i, (_, entry) in enumerate(message_info.current_subpage_entries(), 1):
        entries_text.append(generate_entry_text(i, entry))

    if (page_num := message_info.page_num) is not None or len(message_info.subpages) > 1:
        entries_text.extend(('', ItalicTag(f'Page {page_num or 1}.{message_info.current_subpage}')))

    return '\n'.join(map(str, entries_text)), generate_inline_keyboard(message_info)
