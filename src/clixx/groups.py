from __future__ import annotations

import enum
from typing import Iterator

from .arguments import Argument, Option
from .exceptions import GroupError


class GroupType(enum.Enum):
    """The group constraint type."""

    ANY = enum.auto()  #: Require any.
    ALL = enum.auto()  #: Require all.
    NONE = enum.auto()  #: Require none.
    AT_LEAST_ONE = enum.auto()  #: Require at least one.
    AT_MOST_ONE = enum.auto()  #: Require at most one.
    EXACTLY_ONE = enum.auto()  #: Require exactly one.


#: Alias for :attr:`GroupType.ANY`.
ANY = GroupType.ANY
#: Alias for :attr:`GroupType.ALL`.
ALL = GroupType.ALL
#: Alias for :attr:`GroupType.NONE`.
NONE = GroupType.NONE
#: Alias for :attr:`GroupType.AT_LEAST_ONE`.
AT_LEAST_ONE = GroupType.AT_LEAST_ONE
#: Alias for :attr:`GroupType.AT_MOST_ONE`.
AT_MOST_ONE = GroupType.AT_MOST_ONE
#: Alias for :attr:`GroupType.EXACTLY_ONE`.
EXACTLY_ONE = GroupType.EXACTLY_ONE


class ArgumentGroup:
    """The argument group.

    Parameters:
        name (str):
            The group name.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.arguments: list[Argument] = []

    def __len__(self) -> int:
        """Return the number of arguments."""

        return len(self.arguments)

    def __iter__(self) -> Iterator[Argument]:
        """Iterate arguments."""

        yield from self.arguments

    def __iadd__(self, argument: Argument) -> ArgumentGroup:
        """Add the argument to this group."""

        return self.add(argument)

    def add(self, argument: Argument) -> ArgumentGroup:
        """Add the argument to this group."""

        self.arguments.append(argument)
        return self


class OptionGroup:
    """The option group.

    Parameters:
        name (str):
            The group name.
        type (GroupType, default=ANY):
            The group constraint type.
    """

    def __init__(self, name: str, *, type: GroupType = ANY) -> None:
        self.name = name
        self.type = type
        self.options: list[Option] = []

    def __len__(self) -> int:
        """Return the number of options."""

        return len(self.options)

    def __iter__(self) -> Iterator[Option]:
        """Iterate options."""

        yield from self.options

    def __iadd__(self, option: Option) -> OptionGroup:
        """Add the option to this group."""

        return self.add(option)

    def add(self, option: Option) -> OptionGroup:
        """Add the option to this group."""

        self.options.append(option)
        return self

    def check(self, num_occurred: int) -> None:
        """Check the group constraint."""

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
        num_options = len(self)
        if num_occurred != num_options:
            if num_options == 0:
                raise GroupError(f"Option group {self.name!r} does not take a option.")
            elif num_options == 1:
                raise GroupError(f"Option group {self.name!r} requires exactly one option.")
            else:
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
