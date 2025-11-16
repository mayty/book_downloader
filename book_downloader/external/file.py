__all__ = ['download_file']

from http import HTTPStatus

from aiohttp import ClientSession

from book_downloader.exceptions import (
    FailedToDownloadFileError,
    FileTooLargeError,
    MissingFileSizeError,
    MissingFilenameError,
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MiB


def is_redirect(code: int) -> bool:
    return code in {301, 302, 303, 307, 308}


async def get_file_data(uri: str, session: ClientSession) -> tuple[str, str, int]:
    while True:
        async with session.head(uri, allow_redirects=False) as response:
            if is_redirect(response.status):
                uri = response.headers['Location']
            else:
                info = response.content_disposition

                filename = info.filename if info else None

                if not filename:
                    raise MissingFilenameError(uri=uri)

                size = response.content_length
                if size is None:
                    raise MissingFileSizeError(uri=uri)

                return uri, filename, size


async def download_file(uri: str) -> tuple[bytes, str]:
    async with ClientSession() as session:
        uri, filename, filesize = await get_file_data(uri, session)

        if filesize > MAX_FILE_SIZE:
            raise FileTooLargeError(file_size=filesize, max_size=MAX_FILE_SIZE, uri=uri)

        async with session.get(uri) as response:
            if response.status != HTTPStatus.OK:
                raise FailedToDownloadFileError(status_code=response.status, uri=uri)

            data = await response.content.read()

    return data, filename
