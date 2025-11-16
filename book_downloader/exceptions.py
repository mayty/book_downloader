class ProjectError(Exception):
    def __str__(self) -> str:
        if self.__dict__:  # type: ignore[misc]
            args = ', '.join(f'{key}={value}' for (key, value) in self.__dict__.items())  # type: ignore[misc]
            return f'{self.__class__.__name__}: {args}'
        return self.__class__.__name__

    def __repr__(self) -> str:
        if self.__dict__:  # type: ignore[misc]
            args = ', '.join(f'{key}={value!r}' for (key, value) in self.__dict__.items())  # type: ignore[misc]
            return f'{self.__class__.__name__}({args})'
        return f'{self.__class__.__name__}()'


class NoConfigFileError(ProjectError): ...


class NavigationError(ProjectError, RuntimeError): ...


class NoUpstreamLocationError(NavigationError): ...


class NoRightLocationError(NavigationError): ...


class NoLeftLocationError(NavigationError): ...


class InvalidMessageInfoError(ProjectError, ValueError): ...


class MessageInfoNotFoundError(ProjectError, ValueError):
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


class MultipleEntriesForMessageInfoError(ProjectError, ValueError):
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


class OpdsError(ProjectError, RuntimeError): ...


class FailedToGetOpdsFeedError(OpdsError):
    def __init__(self, status_code: int, location: str) -> None:
        self.status_code = status_code
        self.location = location


class FailedToGetSearchTemplateError(OpdsError): ...


class NoEntriesInOpdsFeedError(OpdsError):
    def __init__(self, location: str) -> None:
        self.location = location


class OpdsFeedNotFoundError(OpdsError):
    def __init__(self, location: str) -> None:
        self.location = location


class FileRetrievalError(ProjectError, RuntimeError): ...


class FailedToDownloadFileError(FileRetrievalError):
    def __init__(self, status_code: int, uri: str) -> None:
        self.status_code = status_code
        self.uri = uri


class FileTooLargeError(FileRetrievalError):
    def __init__(self, file_size: int, max_size: int, uri: str) -> None:
        self.file_size = file_size
        self.max_size = max_size
        self.uri = uri


class MissingFilenameError(FileRetrievalError):
    def __init__(self, uri: str) -> None:
        self.uri = uri


class MissingFileSizeError(FileRetrievalError):
    def __init__(self, uri: str) -> None:
        self.uri = uri
