from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, Protocol

from typing_extensions import Self, TypeAlias

from .exceptions import CLIXXException, HelpSignal, VersionSignal

if TYPE_CHECKING:
    from .commands import _Command


class Printer(Protocol):
    """The printer protocol."""

    def print_error(self, cmd: _Command, exc: CLIXXException) -> None:
        """Print error information."""

    def print_help(self, cmd: _Command) -> None:
        """Print help information."""

    def print_version(self, cmd: _Command) -> None:
        """Print version information."""


PrinterFactory: TypeAlias = Callable[[Dict[str, Any]], Printer]


class PrinterHelper:
    """The printer helper.

    Parameters:
        cmd (Command):
            The command.
        printer (Printer):
            The printer.
        standalone (bool):
            If ``True``, exit this process after handling exception or signal;
            otherwise, propagate exception or signal.
    """

    def __init__(
        self,
        cmd: _Command,
        printer: Printer,
        *,
        standalone: bool,
    ) -> None:
        self.cmd = cmd
        self.printer = printer
        self.standalone = standalone

    def __enter__(self) -> Self:
        """Attach exceptions and signals handlers."""

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        """Dispatch exceptions and signals to handlers."""

        if isinstance(exc_value, CLIXXException):
            self.printer.print_error(self.cmd, exc_value)
            return self._exit(exc_value.exit_code)
        if isinstance(exc_value, HelpSignal):
            self.printer.print_help(self.cmd)
            return self._exit(exc_value.exit_code)
        if isinstance(exc_value, VersionSignal):
            self.printer.print_version(self.cmd)
            return self._exit(exc_value.exit_code)
        return False

    def _exit(self, exit_code: int) -> bool:
        if self.standalone:
            sys.exit(exit_code)
        return False
