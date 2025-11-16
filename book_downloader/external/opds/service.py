import re
from http import HTTPStatus
from urllib.parse import unquote as unquote_url, quote as quote_url

import bleach
from defusedxml.ElementTree import fromstring
from html import unescape

from aiohttp import ClientSession
from loguru import logger

from book_downloader.config import app_config
from book_downloader.exceptions import (
    FailedToGetOpdsFeedError,
    FailedToGetSearchTemplateError,
    NoEntriesInOpdsFeedError,
    OpdsFeedNotFoundError,
)
from book_downloader.external.opds.models import AcquisitionEntry, Entry, OpdsAcquisitionFeed, OpdsFeed
from book_downloader.lib.helpers import url_from_parts
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import HttpUrl
    from xml.etree.ElementTree import Element


class OpdsService:
    def __init__(self, endpoint: HttpUrl) -> None:
        self.endpoint = endpoint
        self._feed_tag_pattern = re.compile('^(\\{.*})?feed$')
        self._entry_tag_pattern = re.compile('^(\\{.*})?entry$')
        self._title_tag_pattern = re.compile('^(\\{.*})?title$')
        self._link_tag_pattern = re.compile('^(\\{.*})?link$')
        self._content_tag_pattern = re.compile('^(\\{.*})?content$')
        self._patters_to_replace: tuple[tuple[re.Pattern[str], str], ...] = (
            (re.compile(r'\[(?P<name>[^\s^\]]+)(\s[^]]+)?].*?\[/(?P=name)]', flags=re.DOTALL), ''),
            (re.compile(r'<br/>'), '\n'),
        )
        self._line_break_pattern = re.compile(r'\s*\n[\n\s]*')
        self._search_template: str | None = None

    async def _get_opds_root(self, location: str) -> Element:
        uri = url_from_parts(str(self.endpoint), location)

        logger.info('GettingOpdsFeed', uri=uri)
        async with ClientSession() as session, session.get(uri) as response:
            if response.status != HTTPStatus.OK:
                logger.error('FailedToGetOpdsFeed', response_code=response.status, reason=response.reason)
                raise FailedToGetOpdsFeedError(status_code=response.status, location=location)

            response_text = await response.text()

        return fromstring(response_text)

    def _get_href(self, element: Element) -> str:
        href = element.get('href')
        assert href is not None
        return unquote_url(href)

    async def list(self, location: str) -> OpdsFeed | OpdsAcquisitionFeed:
        feed_root = await self._get_opds_root(location)

        if not self._feed_tag_pattern.match(feed_root.tag):
            raise OpdsFeedNotFoundError(location)

        title: str | None = None
        next_location: str | None = None
        for element in feed_root:
            if self._title_tag_pattern.match(element.tag):
                title = element.text
            if self._link_tag_pattern.match(element.tag) and element.get('rel') == 'next':
                next_location = self._get_href(element)

        entries = [element for element in feed_root if self._entry_tag_pattern.match(element.tag)]

        parsed_entries = list(filter(bool, map(self.parse_entry, entries)))

        if not parsed_entries:
            logger.error('NoEntriesInOpdsFeed', location=location)
            raise NoEntriesInOpdsFeedError(location=location)

        if isinstance(parsed_entries[0], Entry):
            return OpdsFeed(
                title=title,
                location=location,
                entries=parsed_entries,  # type: ignore[arg-type]
                next_location=next_location,
            )
        return OpdsAcquisitionFeed(
            title=title,
            location=location,
            entries=parsed_entries,  # type: ignore[arg-type]
            next_location=next_location,
        )

    def sanitize_text(self, text: str) -> str:
        for pattern, replacement in self._patters_to_replace:
            text = pattern.sub(replacement, text)
        whitelist_tags = ['a', 'b', 'i', 'u', 's']
        whitelist_attrs = {'a': ['href']}
        sanitized = bleach.clean(text, tags=whitelist_tags, attributes=whitelist_attrs, strip=True).strip()
        return self._line_break_pattern.sub('\n', sanitized)

    def _parse_link_element(self, element: Element, raw_entry: dict[str, object]) -> None:
        rel = element.get('rel')
        if not rel:
            raw_entry['link'] = self._get_href(element)
        elif rel == 'http://opds-spec.org/acquisition/open-access':
            key = 'acquisition_links'
            if key not in raw_entry:
                raw_entry[key] = []
            links = raw_entry[key]
            assert isinstance(links, list)
            links.append({'link': self._get_href(element), 'format': element.get('type')})  # type: ignore[misc]
        elif rel == 'alternate':
            raw_entry['alt_link'] = self._get_href(element)

    def parse_entry(self, entry: Element) -> Entry | AcquisitionEntry | None:
        raw_entry: dict[str, object] = {}

        for element in entry:
            if self._title_tag_pattern.match(element.tag):
                raw_entry['title'] = element.text
            if self._link_tag_pattern.match(element.tag):
                self._parse_link_element(element, raw_entry)
            if self._content_tag_pattern.match(element.tag) and element.get('type') == 'text':
                raw_entry['text'] = element.text
            if self._content_tag_pattern.match(element.tag) and element.get('type') == 'text/html':
                text = element.text
                assert text is not None
                raw_entry['text'] = self.sanitize_text(unescape(text))

        try:
            if 'acquisition_links' in raw_entry:
                return AcquisitionEntry(**raw_entry)  # type: ignore[arg-type]
            return Entry(**raw_entry)  # type: ignore[arg-type]
        except ValueError:
            logger.exception('FailedToParseEntry')
            return None

    async def get_search_template(self) -> str:
        if self._search_template is not None:
            return self._search_template

        feed_root = await self._get_opds_root(app_config.opds.root)

        for element in feed_root:
            if not self._link_tag_pattern.match(element.tag):
                continue

            if element.get('rel') != 'search':
                continue

            element_type = element.get('type')

            if element_type is None:
                continue

            if not element_type.startswith('application/atom+xml'):
                continue

            template = self._get_href(element)
            self._search_template = re.sub(r'\{([a-zA-Z0-9_]+)\??}', '{\\1}', template)
            return self._search_template

        logger.error('FailedToGetSearchTemplateError')
        raise FailedToGetSearchTemplateError

    async def search(self, text: str) -> OpdsFeed | OpdsAcquisitionFeed:
        template = await self.get_search_template()
        search_path = template.format(searchTerms=quote_url(text))
        search_path = re.sub(r'\{[a-zA-Z0-9_]+}', '', search_path)
        message_info = await self.list(search_path)
        message_info.search_request = text
        return message_info
