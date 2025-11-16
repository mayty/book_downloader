from typing import TYPE_CHECKING

from pydantic import BaseModel

from book_downloader.external.opds.models import AcquisitionEntry, Entry, OpdsAcquisitionFeed, OpdsFeed

if TYPE_CHECKING:
    from collections.abc import Generator


MAX_ENTRIES_PER_PAGE = 4 * 3


class ShortMessageInfo(BaseModel):  # type: ignore[explicit-any]
    location: str
    up_location: ShortMessageInfo | None = None
    left_location: ShortMessageInfo | None = None


class MessageInfo(BaseModel):  # type: ignore[explicit-any]
    opds_feed: OpdsFeed | OpdsAcquisitionFeed
    left_location: ShortMessageInfo | None = None
    up_location: ShortMessageInfo | None = None
    current_subpage: int = 0

    def __getitem__(self, index: int) -> tuple[int, Entry | AcquisitionEntry]:
        while index < 0:
            index += len(self.opds_feed.entries)
        while index >= len(self.opds_feed.entries):
            index -= len(self.opds_feed.entries)

        return index, self.opds_feed.entries[index]

    @property
    def page_num(self) -> int | None:
        if self.left_location is None and self.opds_feed.next_location is None:
            return None

        page_num = 0
        current_location: MessageInfo | ShortMessageInfo | None = self
        while current_location:
            current_location = current_location.left_location
            page_num += 1

        return page_num

    @property
    def subpages(self) -> list[int]:
        subpages_count = (len(self.opds_feed) // MAX_ENTRIES_PER_PAGE) + 1
        entries_per_page, leftover_entries = divmod(len(self.opds_feed), subpages_count)
        return [entries_per_page + (1 if i < leftover_entries else 0) for i in range(subpages_count)]

    def current_subpage_entries(self) -> Generator[tuple[int, Entry | AcquisitionEntry]]:
        subpages = self.subpages
        start_index = sum(subpages[: self.current_subpage])

        for i in range(start_index, start_index + subpages[self.current_subpage]):
            yield i, self.opds_feed.entries[i]

    def set_subpage_by_location(self, location: str) -> None:
        assert not isinstance(self.opds_feed, OpdsAcquisitionFeed)

        entry_index = 0
        for i, entry in enumerate(self.opds_feed.entries):
            if entry.link == location:
                entry_index = i
                break

        self.current_subpage = 0
        current_max_index = -1
        for entries_count in self.subpages:
            current_max_index += entries_count
            if entry_index <= current_max_index:
                break
            self.current_subpage += 1

        assert self.current_subpage < len(self.subpages)

    def to_short_info(self) -> ShortMessageInfo:
        return ShortMessageInfo(
            location=self.opds_feed.location,
            up_location=self.up_location,
            left_location=self.left_location,
        )
