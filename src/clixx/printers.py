from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol

from .exceptions import CLIXXException

if TYPE_CHECKING:
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


_default_printer_factory: PrinterFactory = _rich_printer_factory


def get_default_printer_factory() -> PrinterFactory:
    return _default_printer_factory


def set_default_printer_factory(printer_factory: PrinterFactory) -> None:
    global _default_printer_factory
    _default_printer_factory = printer_factory
