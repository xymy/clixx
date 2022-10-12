from __future__ import annotations

from typing import Any

from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SEPARATOR, SHORT_PREFIX, SHORT_PREFIX_LEN
from .context import Context
from .exceptions import ProgrammingError, TooFewOptionValues, TooManyOptionValues
from .groups import ArgumentGroup, OptionGroup


class Parser:
    def __init__(self, argument_groups: list[ArgumentGroup], option_groups: list[OptionGroup]) -> None:
        if not argument_groups and not option_groups:
            raise ProgrammingError("No group defined.")
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
