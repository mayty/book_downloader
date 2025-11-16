from pydantic import BaseModel


class Entry(BaseModel):  # type: ignore[explicit-any]
    title: str
    text: str | None = None
    link: str


class AcquisitionLink(BaseModel):  # type: ignore[explicit-any]
    link: str
    format: str
    is_downloaded: bool = False


class AcquisitionEntry(BaseModel):  # type: ignore[explicit-any]
    title: str
    text: str | None = None
    acquisition_links: list[AcquisitionLink]
    alt_link: str | None = None


class OpdsFeed(BaseModel):  # type: ignore[explicit-any]
    title: str | None
    search_request: str | None = None
    location: str
    next_location: str | None
    entries: list[Entry]

    def __len__(self) -> int:
        return len(self.entries)


class OpdsAcquisitionFeed(BaseModel):  # type: ignore[explicit-any]
    title: str | None
    search_request: str | None = None
    location: str
    next_location: str | None
    entries: list[AcquisitionEntry]
    selected_entry: int | None = None

    def __len__(self) -> int:
        return len(self.entries)
