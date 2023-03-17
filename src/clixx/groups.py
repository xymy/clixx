from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Final, Generic, Iterator, TypeVar

from .arguments import Argument, Option
from .exceptions import GroupError

if TYPE_CHECKING:  # pragma: no cover
    from typing_extensions import Self


class GroupType(enum.Enum):
    """The group constraint type."""

    ANY = enum.auto()  #: Require any.
    ALL = enum.auto()  #: Require all.
    NONE = enum.auto()  #: Require none.
    AT_LEAST_ONE = enum.auto()  #: Require at least one.
    AT_MOST_ONE = enum.auto()  #: Require at most one.
    EXACTLY_ONE = enum.auto()  #: Require exactly one.


#: Alias for :attr:`GroupType.ANY`.
ANY: Final = GroupType.ANY
#: Alias for :attr:`GroupType.ALL`.
ALL: Final = GroupType.ALL
#: Alias for :attr:`GroupType.NONE`.
NONE: Final = GroupType.NONE
#: Alias for :attr:`GroupType.AT_LEAST_ONE`.
AT_LEAST_ONE: Final = GroupType.AT_LEAST_ONE
#: Alias for :attr:`GroupType.AT_MOST_ONE`.
AT_MOST_ONE: Final = GroupType.AT_MOST_ONE
#: Alias for :attr:`GroupType.EXACTLY_ONE`.
EXACTLY_ONE: Final = GroupType.EXACTLY_ONE

T = TypeVar("T")


class _Group(Generic[T]):
    """The group.

    Parameters:
        title (str):
            The group title.
        hidden (bool):
            If ``True``, hide this group from help information.
    """

    def __init__(self, title: str, *, hidden: bool) -> None:
        self.title = title
        self.hidden = hidden
        self.members: list[T] = []

    def __len__(self) -> int:
        """Return the number of members."""

        return len(self.members)

    def __iter__(self) -> Iterator[T]:
        """Iterate members."""

        yield from self.members

    def __iadd__(self, member: T) -> Self:
        """Add the member to this group."""

        return self.add(member)

    def add(self, member: T) -> Self:
        """Add the member to this group."""

        self.members.append(member)
        return self


class ArgumentGroup(_Group[Argument]):
    """The argument group.

    Parameters:
        title (str):
            The group title.
        hidden (bool, default=True):
            If ``True``, hide this argument group from help information.
    """

    def __init__(self, title: str, *, hidden: bool = True) -> None:
        super().__init__(title, hidden=hidden)


class OptionGroup(_Group[Option]):
    """The option group.

    Parameters:
        title (str):
            The group title.
        type (GroupType, default=ANY):
            The group constraint type.
        hidden (bool, default=False):
            If ``True``, hide this option group from help information.
    """

    def __init__(self, title: str, *, type: GroupType = ANY, hidden: bool = False) -> None:
        super().__init__(title, hidden=hidden)
        self.type = type

    def check(self, num_occurred: int) -> None:
        """Check the group constraint.

        Parameters:
            num_occurred (int):
                The number of occurred options.
        """

        if self.type == ANY:
            return self._check_any(num_occurred)
        elif self.type == ALL:
            return self._check_all(num_occurred)
        elif self.type == NONE:
            return self._check_none(num_occurred)
        elif self.type == AT_LEAST_ONE:
            return self._check_at_least_one(num_occurred)
        elif self.type == AT_MOST_ONE:
            return self._check_at_most_one(num_occurred)
        elif self.type == EXACTLY_ONE:
            return self._check_exactly_one(num_occurred)
        else:
            raise AssertionError

    def _check_any(self, num_occurred: int) -> None:
        pass

    def _check_all(self, num_occurred: int) -> None:
        num_options = len(self)
        if num_occurred != num_options:
            if num_options == 0:
                raise GroupError(f"Option group {self.title!r} does not take a option.")
            elif num_options == 1:
                raise GroupError(f"Option group {self.title!r} requires exactly one option.")
            else:
                raise GroupError(f"Option group {self.title!r} requires all {num_options!r} options.")

    def _check_none(self, num_occurred: int) -> None:
        if num_occurred != 0:
            raise GroupError(f"Option group {self.title!r} does not take a option.")

    def _check_at_least_one(self, num_occurred: int) -> None:
        if num_occurred < 1:
            raise GroupError(f"Option group {self.title!r} requires at least one option.")

    def _check_at_most_one(self, num_occurred: int) -> None:
        if num_occurred > 1:
            raise GroupError(f"Option group {self.title!r} requires at most one option.")

    def _check_exactly_one(self, num_occurred: int) -> None:
        if num_occurred != 1:
            raise GroupError(f"Option group {self.title!r} requires exactly one option.")


class CommandGroup(_Group[str]):
    """The command group.

    Parameters:
        title (str):
            The group title.
        hidden (bool, default=False):
            If ``True``, hide this command group from help information.
    """

    def __init__(self, title: str, *, hidden: bool = False) -> None:
        super().__init__(title, hidden=hidden)
