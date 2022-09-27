from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .arguments import Argument, Option
from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SEPARATOR, SHORT_PREFIX, SHORT_PREFIX_LEN
from .context import Context
from .exceptions import DefinitionError, TooFewOptionValues, TooManyArguments, TooManyOptionValues, UnknownOption
from .groups import ArgumentGroup, OptionGroup


@dataclass
class ArgumentGroupInfo:
    group: ArgumentGroup


@dataclass
class ArgumentInfo:
    argument: Argument
    group_info: ArgumentGroupInfo
    occurred: bool = False

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
class OptionGroupInfo:
    group: OptionGroup
    nargs: int = 0


@dataclass
class OptionInfo:
    option: Option
    group_info: OptionGroupInfo
    occurred: bool = False

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


def _build_argument_list(argument_groups: list[ArgumentGroup]) -> list[ArgumentInfo]:
    argument_list: list[ArgumentInfo] = []
    for group in argument_groups:
        group_info = ArgumentGroupInfo(group)
        for argument in group:
            argument_info = ArgumentInfo(argument, group_info)
            argument_list.append(argument_info)
    return argument_list


def _update_option_lookup(lookup: dict[str, OptionInfo], keys: Iterable[str], info: OptionInfo) -> None:
    for key in keys:
        if key in lookup:
            raise DefinitionError(f"Option {key!r} conflicts.")
        lookup[key] = info


def _build_option_lookup(option_groups: list[OptionGroup]) -> dict[str, OptionInfo]:
    option_lookup: dict[str, OptionInfo] = {}
    for group in option_groups:
        group_info = OptionGroupInfo(group)
        for option in group:
            option_info = OptionInfo(option, group_info)
            _update_option_lookup(option_lookup, option.long_options, option_info)
            _update_option_lookup(option_lookup, option.short_options, option_info)
    return option_lookup


OK = 0
SWITCH_TO_POSITIONAL_ONLY = 1


class Parser:
    def __init__(self, argument_groups: list[ArgumentGroup], option_groups: list[OptionGroup]) -> None:
        self.argument_list = _build_argument_list(argument_groups)
        self.option_lookup = _build_option_lookup(option_groups)

    def parse_args(self, argv: list[str]) -> Context:
        ctx = Context(argv)
        status = self.parse_args_normal(ctx, ctx.args)
        if status == SWITCH_TO_POSITIONAL_ONLY:
            self.parse_args_positional_only(ctx, ctx.args)
        return ctx

    def parse_args_normal(self, ctx: Context, args: dict[str, Any]):
        while (arg := ctx.next_arg) is not None:
            if arg == SEPARATOR:
                return SWITCH_TO_POSITIONAL_ONLY
            elif arg.startswith(LONG_PREFIX) and len(arg) > LONG_PREFIX_LEN:
                self._parse_long_option(ctx, args, arg)
            elif arg.startswith(SHORT_PREFIX) and len(arg) > SHORT_PREFIX_LEN:
                self._parse_short_option(ctx, args, arg)
            else:
                self._parse_argument(ctx, args, arg)
        return OK

    def parse_args_positional_only(self, ctx: Context, args: dict[str, Any]):
        while (arg := ctx.next_arg) is not None:
            self._parse_argument(ctx, args, arg)
        return OK

    def _parse_argument(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        try:
            argument = self.argument_list[ctx.pos]
        except IndexError:
            raise TooManyArguments("Got too many arguments")

        argument.store(args, arg)
        if argument.nargs == 1:
            ctx.pos += 1

    def _lookup(self, key: str) -> OptionInfo:
        option = self.option_lookup.get(key, None)
        if option is None:
            raise UnknownOption(f"Unknown option {key!r}.")
        return option

    def _parse_long_option(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        value: str | None

        if "=" in arg:  # --option=value
            key, value = arg.split("=", 1)
            option = self._lookup(key)
            if option.nargs == 0:
                raise TooManyOptionValues(f"Option {key!r} does not take a value.")
            option.store(args, value, key=key)

        else:  # --option [value]
            key = arg
            option = self._lookup(key)
            if option.nargs == 0:
                option.store_const(args)
            else:
                if (value := ctx.next_arg) is None:
                    raise TooFewOptionValues(f"Option {key!r} requires a value.")
                option.store(args, value, key=key)

    def _parse_short_option(self, ctx: Context, args: dict[str, Any], arg: str) -> None:
        index = len(SHORT_PREFIX)
        while index < len(arg):
            key = "-" + arg[index]
            index += 1
            option = self._lookup(key)

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
