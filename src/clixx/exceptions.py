class DefinitionError(Exception):
    """Define a bad command, group, argument, option, type, etc."""


class ParserContextError(Exception):
    """Parser context error."""


class TypeConversionError(Exception):
    """Type conversion error."""


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
    """Missing option."""


class UnknownOption(CLIXXException):
    """Unknown option."""


class TooFewOptionValues(CLIXXException):
    """Too few option values given."""


class TooManyOptionValues(CLIXXException):
    """Too many option values given."""


class InvalidArgumentValue(CLIXXException):
    """Invalid argument value given."""


class InvalidOptionValue(CLIXXException):
    """Invalid option value given."""


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
