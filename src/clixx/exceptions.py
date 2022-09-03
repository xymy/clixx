class DefinitionError(Exception):
    """Define a bad command, parser, argument, option, etc."""


class CLIXXException(Exception):
    """The base class for all CLIXX exceptions."""

    exit_code = 128


class TooFewArguments(CLIXXException):
    exit_code = 129


class TooManyArguments(CLIXXException):
    exit_code = 130


class MissingOption(CLIXXException):
    exit_code = 131


class UnknownOption(CLIXXException):
    exit_code = 132


class MissingValue(CLIXXException):
    exit_code = 133


class InvalidValue(CLIXXException):
    exit_code = 134


class GroupError(CLIXXException):
    exit_code = 135


class SubcommandError(CLIXXException):
    exit_code = 136


class CLIXXSignal(BaseException):
    """The base class for all CLIXX signals."""


class HelpSignal(CLIXXSignal):
    """The signal for showing help information."""


class VersionSignal(CLIXXSignal):
    """The signal for showing version information."""
