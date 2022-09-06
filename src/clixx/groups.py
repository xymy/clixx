from enum import Enum, auto
from typing import Iterator, List

from .arguments import Argument, Option


class GroupType(Enum):
    """The group type."""

    ANY = auto()
    ALL = auto()
    NONE = auto()
    AT_LEAST_ONE = auto()
    AT_MOST_ONE = auto()
    EXACTLY_ONE = auto()


ANY = GroupType.ANY
ALL = GroupType.ALL
NONE = GroupType.NONE
AT_LEAST_ONE = GroupType.AT_LEAST_ONE
AT_MOST_ONE = GroupType.AT_MOST_ONE
EXACTLY_ONE = GroupType.EXACTLY_ONE


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

    def __init__(self, name: str, *, type: GroupType = ANY) -> None:
        self.name = name
        self.type = type
        self.gourp: List[Option] = []

    def __iter__(self) -> Iterator[Option]:
        yield from self.gourp

    def add(self, option: Option) -> None:
        self.gourp.append(option)
