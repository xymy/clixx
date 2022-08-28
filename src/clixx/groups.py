from enum import Enum, auto
from typing import List, Iterator

from .arguments import Argument, OptionBase


class GT(Enum):
    """The group type."""

    ANY = auto()
    ALL = auto()
    NONE = auto()
    AT_MOST_ONE = auto()
    AT_LEAST_ONE = auto()
    EXACTLY_ONE = auto()


class ArgumentGroup:
    """The group of positional arguments."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.gourp: List[Argument] = []

    def __iter__(self) -> Iterator[Argument]:
        yield from self.gourp

    def add(self, argument: Argument) -> None:
        self.gourp.append(argument)


class OptionGroup:
    """The group of optional arguments."""

    def __init__(self, name: str, *, type: GT = GT.ANY) -> None:
        self.name = name
        self.type = type
        self.gourp: List[OptionBase] = []

    def __iter__(self) -> Iterator[OptionBase]:
        yield from self.gourp

    def add(self, option: OptionBase) -> None:
        self.gourp.append(option)
