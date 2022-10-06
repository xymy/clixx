from __future__ import annotations

import enum
from typing import Iterator

from .arguments import Argument, Option
from .exceptions import GroupError


class GroupType(enum.Enum):
    """The group type."""

    ANY = enum.auto()
    ALL = enum.auto()
    NONE = enum.auto()
    AT_LEAST_ONE = enum.auto()
    AT_MOST_ONE = enum.auto()
    EXACTLY_ONE = enum.auto()


# Aliases for GroupType.
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
        self.arguments: list[Argument] = []

    def __iter__(self) -> Iterator[Argument]:
        yield from self.arguments

    def add(self, *args, **kwargs) -> ArgumentGroup:
        self.arguments.append(Argument(*args, **kwargs))
        return self


class OptionGroup:
    """The group of optional arguments."""

    def __init__(self, name: str, *, type: GroupType = ANY) -> None:
        self.name = name
        self.type = type
        self.options: list[Option] = []

    def __iter__(self) -> Iterator[Option]:
        yield from self.options

    def add(self, *args, **kwargs) -> OptionGroup:
        self.options.append(Option(*args, **kwargs))
        return self

    def check(self, num_occurred: int) -> None:
        if self.type == ANY:
            return self._check_any(num_occurred)
        if self.type == ALL:
            return self._check_all(num_occurred)
        if self.type == NONE:
            return self._check_none(num_occurred)
        if self.type == AT_LEAST_ONE:
            return self._check_at_least_one(num_occurred)
        if self.type == AT_MOST_ONE:
            return self._check_at_most_one(num_occurred)
        if self.type == EXACTLY_ONE:
            return self._check_exactly_one(num_occurred)

    def _check_any(self, num_occurred: int) -> None:
        pass

    def _check_all(self, num_occurred: int) -> None:
        num_options = len(self.options)
        if num_occurred != num_options:
            raise GroupError(f"Option group {self.name!r} requires all {num_options!r} options.")

    def _check_none(self, num_occurred: int) -> None:
        if num_occurred != 0:
            raise GroupError(f"Option group {self.name!r} does not take a option.")

    def _check_at_least_one(self, num_occurred: int) -> None:
        if num_occurred < 1:
            raise GroupError(f"Option group {self.name!r} requires at least one option.")

    def _check_at_most_one(self, num_occurred: int) -> None:
        if num_occurred > 1:
            raise GroupError(f"Option group {self.name!r} requires at most one option.")

    def _check_exactly_one(self, num_occurred: int) -> None:
        if num_occurred != 1:
            raise GroupError(f"Option group {self.name!r} requires exactly one option.")
