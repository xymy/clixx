from __future__ import annotations

import sys
from typing import TextIO


class InternalError(Exception):
    """Invoke internal APIs incorrectly."""


class DefinitionError(Exception):
    """Define a bad command, parser, argument, option, etc."""


class CLIXXException(Exception):
    """The base class for all CLIXX exceptions."""

    exit_code = 128

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def show(self, *, file: TextIO | None = None) -> None:
        file = file or sys.stderr
        file.write(f"Error: {self.message}\n")


class TooFewArguments(CLIXXException):
    exit_code = 129


class TooManyArguments(CLIXXException):
    exit_code = 130


class MissingOption(CLIXXException):
    exit_code = 131


class UnknownOption(CLIXXException):
    exit_code = 132


class TooFewOptionValues(CLIXXException):
    exit_code = 133


class TooManyOptionValues(CLIXXException):
    exit_code = 134


class InvalidValue(CLIXXException):
    exit_code = 135


class GroupError(CLIXXException):
    exit_code = 144


class SubcommandError(CLIXXException):
    exit_code = 145


class CLIXXSignal(BaseException):
    """The base class for all CLIXX signals."""


class HelpSignal(CLIXXSignal):
    """The signal for showing help information."""


class VersionSignal(CLIXXSignal):
    """The signal for showing version information."""
