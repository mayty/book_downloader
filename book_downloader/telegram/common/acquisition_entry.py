from functools import partial

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from book_downloader.config import app_config
from book_downloader.external.opds.models import AcquisitionLink, OpdsAcquisitionFeed
from book_downloader.lib.helpers import url_from_parts
from book_downloader.telegram.common.helpers import itoa
from book_downloader.telegram.common.markup import BoldTag, HtmlTag, HyperlinkTag, ItalicTag, QuoteTag, RawTag
from book_downloader.telegram.constants import CallbackCommandPrefixes, CallbackCommands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from book_downloader.telegram.data.message_info import MessageInfo


generate_uri = partial(url_from_parts, str(app_config.opds.host))


def generate_inline_keyboard(entries: list[tuple[int, AcquisitionLink]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [[]]

    keyboard_rows_count = (len(entries) // 4) + 1
    buttons_per_row, leftover_buttons_count = divmod(len(entries), keyboard_rows_count)

    for button_num, (i, entry) in enumerate(entries, 1):
        if entry.is_downloaded:
            continue

        target_buttons_count = buttons_per_row + int(len(rows) <= leftover_buttons_count)
        if len(rows[-1]) >= target_buttons_count:
            rows.append([])
        rows[-1].append(InlineKeyboardButton(text=str(button_num), callback_data=f'{CallbackCommandPrefixes.ENTER}{i}'))

    rows.append(
        [
            InlineKeyboardButton(text='⤴️', callback_data=CallbackCommands.BACK),
        ]
    )

    return InlineKeyboardMarkup(rows)


def generate_acquisition_message(message_info: MessageInfo) -> tuple[str, InlineKeyboardMarkup]:
    assert isinstance(message_info.opds_feed, OpdsAcquisitionFeed)

    selected_entry = message_info.opds_feed.selected_entry
    assert selected_entry is not None

    entry = message_info.opds_feed.entries[selected_entry]

    message_lines: list[str | HtmlTag] = []

    title_tag: HtmlTag = BoldTag(entry.title)

    if entry.alt_link:
        title_tag = HyperlinkTag(title_tag, href=generate_uri(entry.alt_link))

    message_lines.append(QuoteTag(t'{title_tag}\n{ItalicTag(RawTag(entry.text))}'))  # type: ignore[misc]

    for i, link in enumerate(entry.acquisition_links, 1):
        if link.is_downloaded:
            message_lines.append(f'💾 {HyperlinkTag(BoldTag(link.format), href=generate_uri(link.link))}')
        else:
            message_lines.append(f'{itoa(i)} {HyperlinkTag(BoldTag(link.format), href=generate_uri(link.link))}')

    return '\n'.join(map(str, message_lines)), generate_inline_keyboard(list(enumerate(entry.acquisition_links)))
