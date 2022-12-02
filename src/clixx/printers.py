from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Protocol

from .exceptions import CLIXXException, HelpSignal, VersionSignal

if TYPE_CHECKING:  # pragma: no cover
    from typing_extensions import Self

    from .commands import Command, SuperCommand


class Printer(Protocol):
    """The protocol class for printer."""

    def print_error(self, cmd: Command, exc: CLIXXException) -> None:
        ...

    def print_help(self, cmd: Command) -> None:
        ...

    def print_version(self, cmd: Command) -> None:
        ...


class SuperPrinter(Protocol):
    """The protocol class for super printer."""

    def print_error(self, cmd: SuperCommand, exc: CLIXXException) -> None:
        ...

    def print_help(self, cmd: SuperCommand) -> None:
        ...

    def print_version(self, cmd: SuperCommand) -> None:
        ...


#: The type of printer factory.
PrinterFactory = Callable[[dict[str, Any]], Printer]

#: The type of super printer factory.
SuperPrinterFactory = Callable[[dict[str, Any]], SuperPrinter]


def _rich_printer_factory(config: dict[str, Any]) -> Printer:
    from ._rich import RichPrinter

    return RichPrinter(config)


def _rich_super_printer_factory(config: dict[str, Any]) -> SuperPrinter:
    from ._rich import RichSuperPrinter

    return RichSuperPrinter(config)


_default_printer_factory: PrinterFactory = _rich_printer_factory
_default_super_printer_factory: SuperPrinterFactory = _rich_super_printer_factory


def get_default_printer_factory() -> PrinterFactory:
    """Get default printer factory."""

    return _default_printer_factory


def set_default_printer_factory(printer_factory: PrinterFactory) -> None:
    """Set default printer factory."""

    global _default_printer_factory
    _default_printer_factory = printer_factory


def get_default_super_printer_factory() -> SuperPrinterFactory:
    """Get default super printer factory."""

    return _default_super_printer_factory


def set_default_super_printer_factory(super_printer_factory: SuperPrinterFactory) -> None:
    """Set default super printer factory."""

    global _default_super_printer_factory
    _default_super_printer_factory = super_printer_factory


class _PrinterHelper:
    def __init__(
        self,
        cmd: Command | SuperCommand,
        printer_factory: PrinterFactory | SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        self.cmd = cmd
        self.printer_factory = printer_factory
        self.printer_config = printer_config

    def __enter__(self) -> Self:  # type: ignore [valid-type]
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if isinstance(exc_value, CLIXXException):
            self.print_error(exc_value)
            sys.exit(exc_value.exit_code)
        if isinstance(exc_value, HelpSignal):
            self.print_help()
            sys.exit(exc_value.exit_code)
        if isinstance(exc_value, VersionSignal):
            self.print_version()
            sys.exit(exc_value.exit_code)

    @classmethod
    def get_default_printer_factory(cls) -> PrinterFactory | SuperPrinterFactory:
        raise NotImplementedError

    def make_printer(self) -> Printer | SuperPrinter:
        if (factory := self.printer_factory) is None:
            factory = self.get_default_printer_factory()
        if (config := self.printer_config) is None:
            config = {}
        return factory(config)

    def print_error(self, exc: CLIXXException) -> None:
        printer = self.make_printer()
        printer.print_error(self.cmd, exc)  # type: ignore

    def print_help(self) -> None:
        printer = self.make_printer()
        printer.print_help(self.cmd)  # type: ignore

    def print_version(self) -> None:
        printer = self.make_printer()
        printer.print_version(self.cmd)  # type: ignore


class PrinterHelper(_PrinterHelper):
    @classmethod
    def get_default_printer_factory(cls) -> PrinterFactory:
        return get_default_printer_factory()


class SuperPrinterHelper(_PrinterHelper):
    @classmethod
    def get_default_printer_factory(cls) -> SuperPrinterFactory:
        return get_default_super_printer_factory()
