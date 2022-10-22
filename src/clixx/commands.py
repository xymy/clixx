from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Any, Callable, Generator, Protocol

from .exceptions import CLIXXException
from .groups import ArgumentGroup, OptionGroup
from .parsers import Parser


class Printer(Protocol):
    """The protocol class for printer."""

    def print_error(self, cmd: Command, error: CLIXXException) -> None:
        ...

    def print_help(self, cmd: Command) -> None:
        ...

    def print_version(self, cmd: Command) -> None:
        ...


PrinterFactory = Callable[[dict[str, Any]], Printer]


class Command:
    def __init__(
        self, name: str | None = None, version: str | None = None, *, config: dict[str, Any] | None = None
    ) -> None:
        self.name = name
        self.version = version

        config = {} if config is None else config
        config.setdefault("try_help_option", "--help")
        self.config = config

        self.parent = None
        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

    def add_argument_group(self, *args, **kwargs) -> ArgumentGroup:
        group = ArgumentGroup(*args, **kwargs)
        self.argument_groups.append(group)
        return group

    def add_option_group(self, *args, **kwargs) -> OptionGroup:
        group = OptionGroup(*args, **kwargs)
        self.option_groups.append(group)
        return group

    def parse_args(self, argv: list[str] | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {}
        argv = sys.argv[1:] if argv is None else argv
        with self._guard():
            parser = Parser(self.argument_groups, self.option_groups)
            parser.parse_args(args, argv)
        return args

    @contextmanager
    def _guard(self) -> Generator[None, None, None]:
        try:
            yield None
        except CLIXXException as e:
            from ._rich import echo

            message = f"Error: {e.format_message()}"
            echo(message, fg="red", bold=True, file=sys.stderr)
            sys.exit(e.exit_code)

    def get_prog(self) -> str:
        return sys.argv[0] if self.name is None else self.name

    def get_usage(self) -> str:
        prog = self.get_prog()
        usage = f"Usage: {prog}"
        if self.option_groups:
            usage += " [OPTIONS]..."
        metavars: list[str] = []
        for argument_group in self.argument_groups:
            for argument in argument_group:
                metavar = argument.show_metavar()
                if not argument.required:
                    metavar = f"[{metavar}]"
                if argument.nargs == -1:
                    metavar += "..."
                metavars.append(metavar)
        if metavars:
            usage += " " + " ".join(metavars)
        return usage
