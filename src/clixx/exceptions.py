class DefinitionError(ValueError):
    """Define a bad command, group, argument, option, type, etc."""


class ParserContextError(RuntimeError):
    """Parser context error."""


class TypeConversionError(TypeError):
    """Type conversion error."""


class CLIXXException(Exception):
    """The base class for all CLIXX exceptions."""

    exit_code = 128

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ArgumentError(CLIXXException):
    """Argument error."""


class TooFewArguments(ArgumentError):
    """Too few arguments given."""


class TooManyArguments(ArgumentError):
    """Too many arguments given."""


class InvalidArgument(ArgumentError):
    """Invalid argument given."""


class OptionError(CLIXXException):
    """Option error."""


class MissingOption(OptionError):
    """Missing option."""


class UnknownOption(OptionError):
    """Unknown option."""


class MultiOption(OptionError):
    """Multi option."""


class TooFewOptionValues(OptionError):
    """Too few option values given."""


class TooManyOptionValues(OptionError):
    """Too many option values given."""


class InvalidOptionValue(OptionError):
    """Invalid option value given."""


class GroupError(CLIXXException):
    """Group error."""


class CommandError(CLIXXException):
    """Command error."""


class CLIXXSignal(BaseException):
    """The base class for all CLIXX signals."""

    exit_code = 0


class HelpSignal(CLIXXSignal):
    """The signal for showing help information."""


class VersionSignal(CLIXXSignal):
    """The signal for showing version information."""
