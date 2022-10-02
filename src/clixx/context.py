from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .arguments import Argument, Option
from .exceptions import DefinitionError
from .groups import ArgumentGroup, OptionGroup


class ArgumentNode:
    def __init__(self, argument: Argument, parent: int) -> None:
        self.argument = argument
        self.parent = parent
        self.occurred = False

    def store(self, args: dict[str, Any], value: str) -> None:
        self.argument.store(args, value)
        self.occurred = True

    def store_default(self, args: dict[str, Any]) -> None:
        self.argument.store_default(args)
        self.occurred = True

    @property
    def nargs(self) -> int:
        return self.argument.nargs


@dataclass
class ArgumentGroupNode:
    group: ArgumentGroup
    children: list[ArgumentNode]


class OptionNode:
    def __init__(self, option: Option, parent: int) -> None:
        self.option = option
        self.parent = parent
        self.occurred = False

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        self.option.store(args, value, key=key)
        self.occurred = True

    def store_const(self, args: dict[str, Any]) -> None:
        self.option.store_const(args)
        self.occurred = True

    def store_default(self, args: dict[str, Any]) -> None:
        self.option.store_default(args)
        self.occurred = True

    @property
    def nargs(self) -> int:
        return self.option.nargs


@dataclass
class OptionGroupNode:
    group: OptionGroup
    children: list[OptionNode]


def _build_argument_tree(argument_groups: list[ArgumentGroup]) -> list[ArgumentGroupNode]:
    tree: list[ArgumentGroupNode] = []
    for index, group in enumerate(argument_groups):
        children: list[ArgumentNode] = []
        for argument in group:
            children.append(ArgumentNode(argument, index))
        tree.append(ArgumentGroupNode(group, children))
    return tree


def _build_option_tree(option_groups: list[OptionGroup]) -> tuple[list[OptionGroupNode], dict[str, OptionNode]]:
    tree: list[OptionGroupNode] = []
    lookup: dict[str, OptionNode] = {}
    for index, group in enumerate(option_groups):
        children: list[OptionNode] = []
        for option in group:
            node = OptionNode(option, index)
            children.append(node)
            for key in option.long_options:
                if key in lookup:
                    raise DefinitionError(f"Option {key!r} conflicts.")
                lookup[key] = node
            for key in option.short_options:
                if key in lookup:
                    raise DefinitionError(f"Option {key!r} conflicts.")
                lookup[key] = node
        tree.append(OptionGroupNode(group, children))
    return tree, lookup


class Context:
    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
        self.index = 0
        self.pos = 0
        self.args: dict[str, Any] = {}

        self._curr_arg: str | None = None

    @property
    def next_arg(self) -> str | None:
        try:
            arg = self.argv[self.index]
            self.index += 1
        except IndexError:
            arg = None
        self._curr_arg = arg
        return arg

    @property
    def curr_arg(self) -> str | None:
        return self._curr_arg
