from typing import TYPE_CHECKING, Any, Callable, Protocol

if TYPE_CHECKING:
    from .commands import Command


class Printer(Protocol):
    """The protocol class for printer."""

    def print_error(self, cmd: Command, message: str) -> None:
        ...

    def print_help(self, cmd: Command) -> None:
        ...

    def print_version(self, cmd: Command) -> None:
        ...


#: The type of printer factory.
PrinterFactory = Callable[[dict[str, Any]], Printer]


def _rich_printer_factory(config: dict[str, Any]) -> Printer:
    from ._rich import RichPrinter

    return RichPrinter(config)


_default_printer_factory: PrinterFactory = _rich_printer_factory


def get_default_printer_factory() -> PrinterFactory:
    return _default_printer_factory


def set_default_printer_factory(printer_factory: PrinterFactory) -> None:
    global _default_printer_factory
    _default_printer_factory = printer_factory
