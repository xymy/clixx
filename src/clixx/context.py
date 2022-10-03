from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import Any, cast

from .arguments import Argument, Option
from .exceptions import DefinitionError
from .groups import ArgumentGroup, OptionGroup


class ArgumentNode:
    def __init__(self, argument: Argument, parent: ArgumentGroupNode) -> None:
        self.argument = argument
        self.parent = cast(ArgumentGroupNode, weakref.proxy(parent))
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
    def __init__(self, option: Option, parent: OptionGroupNode) -> None:
        self.option = option
        self.parent = cast(OptionGroupNode, weakref.proxy(parent))
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
    for group in argument_groups:
        group_node = ArgumentGroupNode(group, [])
        tree.append(group_node)
        for argument in group:
            node = ArgumentNode(argument, group_node)
            group_node.children.append(node)
    return tree


def _build_option_tree(option_groups: list[OptionGroup]) -> tuple[list[OptionGroupNode], dict[str, OptionNode]]:
    tree: list[OptionGroupNode] = []
    lookup: dict[str, OptionNode] = {}
    for group in option_groups:
        group_node = OptionGroupNode(group, [])
        tree.append(group_node)
        for option in group:
            node = OptionNode(option, group_node)
            group_node.children.append(node)
            for key in option.long_options:
                if key in lookup:
                    raise DefinitionError(f"Option {key!r} conflicts.")
                lookup[key] = node
            for key in option.short_options:
                if key in lookup:
                    raise DefinitionError(f"Option {key!r} conflicts.")
                lookup[key] = node
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