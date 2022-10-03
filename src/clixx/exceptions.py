from __future__ import annotations


class InternalError(Exception):
    """Invoke internal APIs incorrectly."""


class ProgrammingError(Exception):
    """Invoke APIs incorrectly."""


class DefinitionError(ProgrammingError):
    """Define a bad command, argument, option, type, etc."""


class CLIXXException(Exception):
    """The base class for all CLIXX exceptions."""

    exit_code = 128

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def format_message(self) -> str:
        return self.message


class TooFewArguments(CLIXXException):
    """Too few arguments given."""


class TooManyArguments(CLIXXException):
    """Too many arguments given."""


class MissingOption(CLIXXException):
    """Missing required option."""


class UnknownOption(CLIXXException):
    """Unknown option."""


class TooFewOptionValues(CLIXXException):
    """Too few option values given."""


class TooManyOptionValues(CLIXXException):
    """Too many option values given."""


class InvalidValue(CLIXXException):
    """Invalid value given."""

    def __init__(self, message: str, *, key: str) -> None:
        super().__init__(message)
        self.key = key

    def format_message(self) -> str:
        return f"Invalid value for {self.key!r}. {self.message}"


class GroupError(CLIXXException):
    """Group error."""


class SubcommandError(CLIXXException):
    """Subcommand error."""


class CLIXXSignal(BaseException):
    """The base class for all CLIXX signals."""


class HelpSignal(CLIXXSignal):
    """The signal for showing help information."""


class VersionSignal(CLIXXSignal):
    """The signal for showing version information."""
