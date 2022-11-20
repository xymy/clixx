from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Any, Callable, Generator, Iterator, NoReturn

from .exceptions import CLIXXException, HelpSignal, VersionSignal
from .groups import ArgumentGroup, CommandGroup, OptionGroup
from .parsers import Parser, SuperParser
from .printers import (
    Printer,
    PrinterFactory,
    SuperPrinter,
    SuperPrinterFactory,
    get_default_printer_factory,
    get_default_super_printer_factory,
)

ProcessFunction = Callable[..., int | None]


def _dummy_func(*args: Any, **kwargs: Any) -> None:
    pass


class _Command:
    #: The program name. Should be set by parent.
    prog: str | None
    #: The parent command. Should be set by parent.
    parent: SuperCommand | None

    def __init__(self, name: str | None = None, version: str | None = None) -> None:
        self.prog = None
        self.parent = None

        self.name = name
        self.version = version

        self.process_function: ProcessFunction = _dummy_func

    def _init(self, prog: str | None, parent: SuperCommand | None) -> None:
        self.prog = prog
        self.parent = parent

    def get_prog(self) -> str:
        prog = sys.argv[0] if self.prog is None else self.prog
        if self.parent is None:
            return prog
        return f"{self.parent.get_prog()} {prog}"

    def get_name(self) -> str:
        if self.name is not None:
            return self.name
        if self.parent is not None:
            return self.parent.get_name()
        return "Unknown Program"

    def get_version(self) -> str:
        if self.version is not None:
            return self.version
        if self.parent is not None:
            return self.parent.get_version()
        return "Unknown Version"

    def register(self, func: ProcessFunction) -> None:
        self.process_function = func


class Command(_Command):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        *,
        printer_factory: PrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

    def add_argument_group(self, group: ArgumentGroup) -> Command:
        self.argument_groups.append(group)
        return self

    def add_option_group(self, group: OptionGroup) -> Command:
        self.option_groups.append(group)
        return self

    def __call__(self, argv: list[str] | None = None) -> NoReturn:
        args = self.parse_args(argv)
        exit_code = self.process_function(**args)
        sys.exit(exit_code)

    def parse_args(self, argv: list[str] | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {}
        argv = sys.argv[1:] if argv is None else argv
        with self._attach_handlers():
            parser = Parser(self.argument_groups, self.option_groups)
            parser.parse_args(args, argv)
        return args

    @contextmanager
    def _attach_handlers(self) -> Generator[None, None, None]:
        try:
            yield
        except CLIXXException as e:
            self.print_error(e)
            sys.exit(e.exit_code)
        except HelpSignal as e:
            self.print_help()
            sys.exit(e.exit_code)
        except VersionSignal as e:
            self.print_version()
            sys.exit(e.exit_code)

    def make_printer(self) -> Printer:
        if (factory := self.printer_factory) is None:
            factory = get_default_printer_factory()
        if (config := self.printer_config) is None:
            config = {}
        return factory(config)

    def print_error(self, exc: CLIXXException) -> None:
        printer = self.make_printer()
        printer.print_error(self, exc)

    def print_help(self) -> None:
        printer = self.make_printer()
        printer.print_help(self)

    def print_version(self) -> None:
        printer = self.make_printer()
        printer.print_version(self)


class SuperCommand(_Command):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        *,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.option_groups: list[OptionGroup] = []

    def iter_command_group(self) -> Iterator[CommandGroup]:
        raise NotImplementedError

    def load_command(self, name: str) -> Command | SuperCommand | None:
        raise NotImplementedError

    def add_option_group(self, group: OptionGroup) -> SuperCommand:
        self.option_groups.append(group)
        return self

    def __call__(self, argv: list[str] | None = None) -> NoReturn:
        args = self.parse_args(argv)
        exit_code = self.process_function(**args)
        sys.exit(exit_code)

    def parse_args(self, argv: list[str] | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {}
        argv = sys.argv[1:] if argv is None else argv
        with self._attach_handlers():
            parser = SuperParser(self.load_command, self.option_groups)
            parser.parse_args(args, argv)
        return args

    @contextmanager
    def _attach_handlers(self) -> Generator[None, None, None]:
        try:
            yield
        except CLIXXException as e:
            self.print_error(e)
            sys.exit(e.exit_code)
        except HelpSignal as e:
            self.print_help()
            sys.exit(e.exit_code)
        except VersionSignal as e:
            self.print_version()
            sys.exit(e.exit_code)

    def make_printer(self) -> SuperPrinter:
        if (factory := self.printer_factory) is None:
            factory = get_default_super_printer_factory()
        if (config := self.printer_config) is None:
            config = {}
        return factory(config)

    def print_error(self, exc: CLIXXException) -> None:
        printer = self.make_printer()
        printer.print_error(self, exc)

    def print_help(self) -> None:
        printer = self.make_printer()
        printer.print_help(self)

    def print_version(self) -> None:
        printer = self.make_printer()
        printer.print_version(self)
