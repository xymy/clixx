from __future__ import annotations

import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, cast

from .arguments import Argument, Option
from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SEPARATOR, SHORT_PREFIX, SHORT_PREFIX_LEN
from .exceptions import (
    InvalidArgumentValue,
    InvalidOptionValue,
    MissingOption,
    ParserContextError,
    TooFewArguments,
    TooFewOptionValues,
    TooManyArguments,
    TooManyOptionValues,
    TypeConversionError,
    UnknownOption,
)
from .groups import ArgumentGroup, OptionGroup


@contextmanager
def _raise_invalid_argument_value(name: str) -> Generator[None, None, None]:
    try:
        yield
    except TypeConversionError as e:
        raise InvalidArgumentValue(f"Invalid value for argument {name}. {str(e)}")


@contextmanager
def _raise_invalid_option_value(name: str) -> Generator[None, None, None]:
    try:
        yield
    except TypeConversionError as e:
        raise InvalidOptionValue(f"Invalid value for option {name}. {str(e)}")


class ArgumentNode:
    def __init__(self, argument: Argument, parent: ArgumentGroupNode) -> None:
        self.argument = argument
        self.parent = cast(ArgumentGroupNode, weakref.proxy(parent))
        self.occurred = False

    def store(self, args: dict[str, Any], value: str) -> None:
        with _raise_invalid_argument_value(self.format_decl()):
            self.argument.store(args, value)
        self.occurred = True

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_argument_value(self.format_decl()):
            self.argument.store_default(args)

    def format_decl(self) -> str:
        return self.argument.format_decl()

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

    def _inc_occurred(self) -> None:
        # The same option may occur more than once.
        if not self.occurred:
            self.occurred = True
            self.parent.num_occurred += 1

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        with _raise_invalid_option_value(repr(key)):
            self.option.store(args, value)
        self._inc_occurred()

    def store_const(self, args: dict[str, Any]) -> None:
        with _raise_invalid_option_value(self.format_decls()):
            self.option.store_const(args)
        self._inc_occurred()

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_option_value(self.format_decls()):
            self.option.store_default(args)

    def format_decls(self) -> str:
        return self.option.format_decls()

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
                    raise ParserContextError(f"Option {key!r} conflicts.")
                map[key] = node
            for key in option.short_options:
                if key in map:
                    raise ParserContextError(f"Option {key!r} conflicts.")
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
                        raise MissingOption(f"Missing option {option.format_decls()}.")
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


class Parser:
    def __init__(self, argument_groups: list[ArgumentGroup], option_groups: list[OptionGroup]) -> None:
        self.argument_groups = argument_groups
        self.option_groups = option_groups

    def parse_args(self, args: dict[str, Any], argv: list[str]) -> Context:
        ctx = Context(self.argument_groups, self.option_groups, args, argv)

        switch_to_positional_only = False
        while (arg := ctx.next_arg) is not None:
            if arg == SEPARATOR:
                switch_to_positional_only = True
                break
            elif arg.startswith(LONG_PREFIX) and len(arg) > LONG_PREFIX_LEN:
                self._parse_long_option(ctx, args, arg)
            elif arg.startswith(SHORT_PREFIX) and len(arg) > SHORT_PREFIX_LEN:
                self._parse_short_option(ctx, args, arg)
            else:
                self._parse_argument(ctx, args, arg)

        if switch_to_positional_only:
            while (arg := ctx.next_arg) is not None:
                self._parse_argument(ctx, args, arg)

        ctx.finalize()
        return ctx

    @staticmethod
    def _parse_argument(ctx: Context, args: dict[str, Any], arg: str) -> None:
        argument = ctx.get_argument()
        argument.store(args, arg)

    @staticmethod
    def _parse_long_option(ctx: Context, args: dict[str, Any], arg: str) -> None:
        value: str | None

        if "=" in arg:  # --option=value
            key, value = arg.split("=", 1)
            option = ctx.get_option(key)
            if option.nargs == 0:
                raise TooManyOptionValues(f"Option {key!r} does not take a value.")
            option.store(args, value, key=key)

        else:  # --option [value]
            key = arg
            option = ctx.get_option(key)
            if option.nargs == 0:
                option.store_const(args)
            else:
                if (value := ctx.next_arg) is None:
                    raise TooFewOptionValues(f"Option {key!r} requires a value.")
                option.store(args, value, key=key)

    @staticmethod
    def _parse_short_option(ctx: Context, args: dict[str, Any], arg: str) -> None:
        index = len(SHORT_PREFIX)
        while index < len(arg):
            key = "-" + arg[index]
            index += 1
            option = ctx.get_option(key)

            if option.nargs == 0:
                option.store_const(args)
            else:
                value: str | None

                if index < len(arg):  # -ovalue
                    value = arg[index:]
                else:  # -o value
                    if (value := ctx.next_arg) is None:
                        raise TooFewOptionValues(f"Option {key!r} requires a value.")
                option.store(args, value, key=key)
                break  # end of parsing
