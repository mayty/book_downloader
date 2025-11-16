from enum import StrEnum, auto


class CallbackCommands(StrEnum):
    BACK = auto()
    RIGHT = auto()
    LEFT = auto()
    NOOP = auto()


class CallbackCommandPrefixes(StrEnum):
    ENTER = 'enter_'


class Commands(StrEnum):
    START = auto()
    HELP = auto()
    EXPLORE = auto()
