from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, Protocol

from typing_extensions import Self

from .exceptions import CLIXXException, HelpSignal, VersionSignal

if TYPE_CHECKING:  # pragma: no cover
    from .commands import Command, SuperCommand


class Printer(Protocol):
    """The protocol class for printer."""

    def print_error(self, cmd: Command, exc: CLIXXException) -> None:
        """Print error information."""

    def print_help(self, cmd: Command) -> None:
        """Print help information."""

    def print_version(self, cmd: Command) -> None:
        """Print version information."""


class SuperPrinter(Protocol):
    """The protocol class for super printer."""

    def print_error(self, cmd: SuperCommand, exc: CLIXXException) -> None:
        """Print error information."""

    def print_help(self, cmd: SuperCommand) -> None:
        """Print help information."""

    def print_version(self, cmd: SuperCommand) -> None:
        """Print version information."""


#: The type of printer factory.
PrinterFactory = Callable[[Dict[str, Any]], Printer]
#: The type of super printer factory.
SuperPrinterFactory = Callable[[Dict[str, Any]], SuperPrinter]


def _rich_printer_factory(config: dict[str, Any]) -> Printer:
    from ._rich import RichPrinter

    return RichPrinter(config)


def _rich_super_printer_factory(config: dict[str, Any]) -> SuperPrinter:
    from ._rich import RichSuperPrinter

    return RichSuperPrinter(config)


_default_printer_factory: PrinterFactory = _rich_printer_factory
_default_super_printer_factory: SuperPrinterFactory = _rich_super_printer_factory


class _PrinterHelper:
    def __init__(
        self,
        cmd: Command | SuperCommand,
        printer_factory: PrinterFactory | SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
        *,
        is_exit: bool = True,
        is_raise: bool = False,
    ) -> None:
        self.cmd = cmd
        self.printer_factory = printer_factory
        self.printer_config = printer_config
        self.is_exit = is_exit
        self.is_raise = is_raise

    def __enter__(self) -> Self:
        """Attach exception and signal handlers."""

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        """Detach exception and signal handlers."""

        if isinstance(exc_value, CLIXXException):
            self.print_error(exc_value)
            return self._exit(exc_value.exit_code)
        if isinstance(exc_value, HelpSignal):
            self.print_help()
            return self._exit(exc_value.exit_code)
        if isinstance(exc_value, VersionSignal):
            self.print_version()
            return self._exit(exc_value.exit_code)
        return False

    def _exit(self, exit_code: int) -> bool:
        if self.is_exit:
            sys.exit(exit_code)
        return not self.is_raise

    def make_printer(self) -> Printer | SuperPrinter:
        if (factory := self.printer_factory) is None:
            factory = self.get_factory()
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

    @classmethod
    def get_factory(cls) -> PrinterFactory | SuperPrinterFactory:
        raise NotImplementedError

    @classmethod
    def set_factory(cls, printer_factory: PrinterFactory | SuperPrinterFactory) -> None:
        raise NotImplementedError


class PrinterHelper(_PrinterHelper):
    """The printer helper.

    Parameters:
        cmd (Command):
            The command.
        printer_factory (PrinterFactory | None, default=None):
            The printer factory.
        printer_config (dict[str, Any] | None, default=None):
            The printer config.
        is_exit (bool, default=True):
            If ``True``, exit this process after handling exception or signal.
        is_raise (bool, default=False):
            If ``True``, propagate exception or signal after handling it.
            Ignored if ``is_exit`` is ``True``.
    """

    def __init__(
        self,
        cmd: Command,
        printer_factory: PrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
        *,
        is_exit: bool = True,
        is_raise: bool = False,
    ) -> None:
        super().__init__(cmd, printer_factory, printer_config, is_exit=is_exit, is_raise=is_raise)

    @classmethod
    def get_factory(cls) -> PrinterFactory:
        """Get default printer factory."""

        return _default_printer_factory

    @classmethod
    def set_factory(cls, printer_factory: PrinterFactory) -> None:  # type: ignore [override]
        """Set default printer factory."""

        global _default_printer_factory
        _default_printer_factory = printer_factory


class SuperPrinterHelper(_PrinterHelper):
    """The super printer helper.

    Parameters:
        cmd (SuperCommand):
            The super command.
        printer_factory (SuperPrinterFactory | None, default=None):
            The super printer factory.
        printer_config (dict[str, Any] | None, default=None):
            The super printer config.
        is_exit (bool, default=True):
            If ``True``, exit this process after handling exception or signal.
        is_raise (bool, default=False):
            If ``True``, propagate exception or signal after handling it.
            Ignored if ``is_exit`` is ``True``.
    """

    def __init__(
        self,
        cmd: SuperCommand,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
        *,
        is_exit: bool = True,
        is_raise: bool = False,
    ) -> None:
        super().__init__(cmd, printer_factory, printer_config, is_exit=is_exit, is_raise=is_raise)

    @classmethod
    def get_factory(cls) -> SuperPrinterFactory:
        """Get default super printer factory."""

        return _default_super_printer_factory

    @classmethod
    def set_factory(cls, super_printer_factory: SuperPrinterFactory) -> None:  # type: ignore [override]
        """Set default super printer factory."""

        global _default_super_printer_factory
        _default_super_printer_factory = super_printer_factory
