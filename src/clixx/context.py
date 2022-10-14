from __future__ import annotations

import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, cast

from .arguments import Argument, Option
from .exceptions import (
    InvalidValue,
    MissingOption,
    ProgrammingError,
    TooFewArguments,
    TooManyArguments,
    TypeConversionError,
    UnknownOption,
)
from .groups import ArgumentGroup, OptionGroup


@contextmanager
def _raise_invalid_value(*, type: str, name: str) -> Generator[None, None, None]:
    try:
        yield None
    except TypeConversionError as e:
        raise InvalidValue(str(e), type=type, name=name)


class ArgumentNode:
    def __init__(self, argument: Argument, parent: ArgumentGroupNode) -> None:
        self.argument = argument
        self.parent = cast(ArgumentGroupNode, weakref.proxy(parent))
        self.occurred = False

    def store(self, args: dict[str, Any], value: str) -> None:
        with _raise_invalid_value(type="argument", name=self.argument.show()):
            self.argument.store(args, value)
        self.occurred = True

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(type="argument", name=self.argument.show()):
            self.argument.store_default(args)

    @property
    def nargs(self) -> int:
        return self.argument.nargs

    @property
    def required(self) -> bool:
        return self.argument.required


@dataclass
class ArgumentGroupNode:
    group: ArgumentGroup
    children: list[ArgumentNode]


class OptionNode:
    def __init__(self, option: Option, parent: OptionGroupNode) -> None:
        self.option = option
        self.parent = cast(OptionGroupNode, weakref.proxy(parent))
        self.occurred = False

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        with _raise_invalid_value(type="option", name=repr(key)):
            self.option.store(args, value, key=key)

        # The same option may occur more than once.
        if not self.occurred:
            self.occurred = True
            self.parent.num_occurred += 1

    def store_const(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(type="option", name=self.option.show()):
            self.option.store_const(args)

        # The same option may occur more than once.
        if not self.occurred:
            self.occurred = True
            self.parent.num_occurred += 1

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(type="option", name=self.option.show()):
            self.option.store_default(args)

    @property
    def nargs(self) -> int:
        return self.option.nargs

    @property
    def required(self) -> bool:
        return self.option.required


@dataclass
class OptionGroupNode:
    group: OptionGroup
    children: list[OptionNode]
    num_occurred: int = 0

    def check(self) -> None:
        self.group.check(self.num_occurred)


def _build_argument_tree(argument_groups: list[ArgumentGroup]) -> tuple[list[ArgumentGroupNode], list[ArgumentNode]]:
    tree: list[ArgumentGroupNode] = []
    seq: list[ArgumentNode] = []
    for group in argument_groups:
        group_node = ArgumentGroupNode(group, [])
        tree.append(group_node)
        for argument in group:
            node = ArgumentNode(argument, group_node)
            group_node.children.append(node)
            seq.append(node)
    return tree, seq


def _build_option_tree(option_groups: list[OptionGroup]) -> tuple[list[OptionGroupNode], dict[str, OptionNode]]:
    tree: list[OptionGroupNode] = []
    map: dict[str, OptionNode] = {}
    for group in option_groups:
        group_node = OptionGroupNode(group, [])
        tree.append(group_node)
        for option in group:
            node = OptionNode(option, group_node)
            group_node.children.append(node)
            for key in option.long_options:
                if key in map:
                    raise ProgrammingError(f"Option {key!r} conflicts.")
                map[key] = node
            for key in option.short_options:
                if key in map:
                    raise ProgrammingError(f"Option {key!r} conflicts.")
                map[key] = node
    return tree, map


class Context:
    def __init__(
        self,
        argument_groups: list[ArgumentGroup],
        option_groups: list[OptionGroup],
        args: dict[str, Any],
        argv: list[str],
    ) -> None:
        self.args = args
        self.argv = argv
        self._index = 0
        self._curr_arg: str | None = None

        self.argument_tree, self.argument_seq = _build_argument_tree(argument_groups)
        self.option_tree, self.option_map = _build_option_tree(option_groups)
        self._pos = 0

        if not self.argument_seq and not self.option_map:
            raise ProgrammingError("No arguments defined.")

    def finalize(self) -> None:
        for argument_group in self.argument_tree:
            for argument in argument_group.children:
                if not argument.occurred:
                    if argument.required:
                        raise TooFewArguments("Got too few arguments.")
                    argument.store_default(self.args)

        for option_group in self.option_tree:
            for option in option_group.children:
                if not option.occurred:
                    if option.required:
                        raise MissingOption(f"Missing option {option.option.show()}.")
                    option.store_default(self.args)
            option_group.check()

    @property
    def curr_arg(self) -> str | None:
        return self._curr_arg

    @property
    def next_arg(self) -> str | None:
        if self._index < len(self.argv):
            arg = self.argv[self._index]
            self._index += 1
        else:
            arg = None
        self._curr_arg = arg
        return arg

    def get_argument(self) -> ArgumentNode:
        if self._pos >= len(self.argument_seq):
            raise TooManyArguments("Got too many arguments.")
        argument = self.argument_seq[self._pos]
        if argument.nargs == 1:
            self._pos += 1
        return argument

    def get_option(self, key: str) -> OptionNode:
        option = self.option_map.get(key, None)
        if option is None:
            raise UnknownOption(f"Unknown option {key!r}.")
        return option
