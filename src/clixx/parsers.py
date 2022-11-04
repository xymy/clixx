from __future__ import annotations

import weakref
from contextlib import contextmanager
from itertools import chain
from typing import Any, Generator, cast

from .arguments import Argument, Option
from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SEPARATOR, SHORT_PREFIX, SHORT_PREFIX_LEN
from .exceptions import (
    InvalidArgumentValue,
    InvalidOptionValue,
    MissingOption,
    ParserContextError,
    SubcommandError,
    TooFewArguments,
    TooFewOptionValues,
    TooManyArguments,
    TooManyOptionValues,
    TypeConversionError,
    UnknownOption,
)
from .groups import ArgumentGroup, CommandGroup, OptionGroup


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
        self._argument = argument
        self.parent = cast(ArgumentGroupNode, weakref.proxy(parent))
        self.occurred = False

    def _inc_occurred(self) -> None:
        if not self.occurred:
            self.occurred = True
            self.parent.num_occurred += 1

    def store(self, args: dict[str, Any], value: str) -> None:
        with _raise_invalid_argument_value(self.format_decl()):
            self._argument.store(args, value)
        self._inc_occurred()

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_argument_value(self.format_decl()):
            self._argument.store_default(args)

    def format_decl(self) -> str:
        return self._argument.format_decl()

    @property
    def nargs(self) -> int:
        return self._argument.nargs

    @property
    def required(self) -> bool:
        return self._argument.required


class ArgumentGroupNode:
    def __init__(self, group: ArgumentGroup, children: list[ArgumentNode]) -> None:
        self._group = group
        self.children = children
        self.num_occurred = 0

    def check(self) -> None:
        self._group.check(self.num_occurred)


class OptionNode:
    def __init__(self, option: Option, parent: OptionGroupNode) -> None:
        self._option = option
        self.parent = cast(OptionGroupNode, weakref.proxy(parent))
        self.occurred = False

    def _inc_occurred(self) -> None:
        if not self.occurred:
            self.occurred = True
            self.parent.num_occurred += 1

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        with _raise_invalid_option_value(repr(key)):
            self._option.store(args, value)
        self._inc_occurred()

    def store_const(self, args: dict[str, Any]) -> None:
        with _raise_invalid_option_value(self.format_decls()):
            self._option.store_const(args)
        self._inc_occurred()

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_option_value(self.format_decls()):
            self._option.store_default(args)

    def format_decls(self) -> str:
        return self._option.format_decls()

    @property
    def nargs(self) -> int:
        return self._option.nargs

    @property
    def required(self) -> bool:
        return self._option.required


class OptionGroupNode:
    def __init__(self, group: OptionGroup, children: list[OptionNode]) -> None:
        self._group = group
        self.children = children
        self.num_occurred = 0

    def check(self) -> None:
        self._group.check(self.num_occurred)


class Context:
    def __init__(self, args: dict[str, Any], argv: list[str]) -> None:
        self.args = args
        self.argv = argv
        self._index = 0
        self._curr_arg: str | None = None

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

    @property
    def argc_consumed(self) -> int:
        return self._index

    @property
    def argv_remained(self) -> list[str]:
        return self.argv[self._index :]


class ArgumentParser:
    def __init__(self, argument_groups: list[ArgumentGroup]) -> None:
        self.argument_tree, self.argument_seq = self._build(argument_groups)
        self._pos = 0

    @staticmethod
    def _build(argument_groups: list[ArgumentGroup]) -> tuple[list[ArgumentGroupNode], list[ArgumentNode]]:
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

    def get_argument(self) -> ArgumentNode:
        if self._pos >= len(self.argument_seq):
            raise TooManyArguments("Got too many arguments.")
        argument = self.argument_seq[self._pos]
        if argument.nargs == 1:
            self._pos += 1
        return argument

    def parse_argument(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        argument = self.get_argument()
        argument.store(args, arg)

    def finalize(self, ctx: Context, args: dict[str, Any]) -> None:
        for group in self.argument_tree:
            for argument in group.children:
                if not argument.occurred:
                    if argument.required:
                        raise TooFewArguments("Got too few arguments.")
                    argument.store_default(args)
            group.check()


class OptionParser:
    def __init__(self, option_groups: list[OptionGroup]) -> None:
        self.option_tree, self.option_map = self._build(option_groups)

    @staticmethod
    def _build(option_groups: list[OptionGroup]) -> tuple[list[OptionGroupNode], dict[str, OptionNode]]:
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

    def get_option(self, key: str) -> OptionNode:
        option = self.option_map.get(key, None)
        if option is None:
            raise UnknownOption(f"Unknown option {key!r}.")
        return option

    def parse_long_option(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        value: str | None

        if "=" in arg:  # --option=value
            key, value = arg.split("=", 1)
            option = self.get_option(key)
            if option.nargs == 0:
                raise TooManyOptionValues(f"Option {key!r} does not take a value.")
            option.store(args, value, key=key)

        else:  # --option [value]
            key = arg
            option = self.get_option(key)
            if option.nargs == 0:
                option.store_const(args)
            else:
                if (value := ctx.next_arg) is None:
                    raise TooFewOptionValues(f"Option {key!r} requires a value.")
                option.store(args, value, key=key)

    def parse_short_option(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        index = len(SHORT_PREFIX)
        while index < len(arg):
            key = "-" + arg[index]
            index += 1
            option = self.get_option(key)

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

    def finalize(self, ctx: Context, args: dict[str, Any]) -> None:
        for group in self.option_tree:
            for option in group.children:
                if not option.occurred:
                    if option.required:
                        raise MissingOption(f"Missing option {option.format_decls()}.")
                    option.store_default(args)
            group.check()


class CommandParser:
    def __init__(self, command_groups: list[CommandGroup]) -> None:
        self.command_groups = command_groups

    def parse_command(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        for command in chain.from_iterable(self.command_groups):
            if command == arg:
                # Store command to a special destination.
                args["<command>"] = command
                break
        raise SubcommandError(f"Unknown command {arg}.")

    def finalize(self, ctx: Context, args: dict[str, Any]) -> None:
        pass


class Parser:
    def __init__(self, argument_groups: list[ArgumentGroup], option_groups: list[OptionGroup]) -> None:
        self.argument_groups = argument_groups
        self.option_groups = option_groups

    def parse_args(self, args: dict[str, Any], argv: list[str]) -> Context:
        ctx = Context(args, argv)
        argument_parser = ArgumentParser(self.argument_groups)
        option_parser = OptionParser(self.option_groups)

        switch_to_positional_only = False
        while (arg := ctx.next_arg) is not None:
            if arg == SEPARATOR:
                switch_to_positional_only = True
                break
            elif arg.startswith(LONG_PREFIX) and len(arg) > LONG_PREFIX_LEN:
                option_parser.parse_long_option(ctx, args, arg)
            elif arg.startswith(SHORT_PREFIX) and len(arg) > SHORT_PREFIX_LEN:
                option_parser.parse_short_option(ctx, args, arg)
            else:
                argument_parser.parse_argument(ctx, args, arg)

        if switch_to_positional_only:
            while (arg := ctx.next_arg) is not None:
                argument_parser.parse_argument(ctx, args, arg)

        option_parser.finalize(ctx, args)
        argument_parser.finalize(ctx, args)
        return ctx


class SuperParser:
    def __init__(self, command_groups: list[CommandGroup], option_groups: list[OptionGroup]) -> None:
        self.command_groups = command_groups
        self.option_groups = option_groups

    def parse_args(self, args: dict[str, Any], argv: list[str]) -> Context:
        ctx = Context(args, argv)
        command_parser = CommandParser(self.command_groups)
        option_parser = OptionParser(self.option_groups)

        switch_to_positional_only = False
        while (arg := ctx.next_arg) is not None:
            if arg == SEPARATOR:
                switch_to_positional_only = True
                break
            elif arg.startswith(LONG_PREFIX) and len(arg) > LONG_PREFIX_LEN:
                option_parser.parse_long_option(ctx, args, arg)
            elif arg.startswith(SHORT_PREFIX) and len(arg) > SHORT_PREFIX_LEN:
                option_parser.parse_short_option(ctx, args, arg)
            else:
                command_parser.parse_command(ctx, args, arg)
                break

        if switch_to_positional_only:
            while (arg := ctx.next_arg) is not None:
                command_parser.parse_command(ctx, args, arg)
                break

        option_parser.finalize(ctx, args)
        command_parser.finalize(ctx, args)
        return ctx
