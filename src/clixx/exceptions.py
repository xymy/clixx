class CLIXXException(Exception):
    """The base class for all CLIXX exceptions."""

    exit_code = 128


class DefinitionError(CLIXXException):
    exit_code = 129


class GroupDefinitionError(DefinitionError):
    exit_code = 130


class UsageError(CLIXXException):
    exit_code = 137


class GroupUsageError(UsageError):
    exit_code = 138


class CLIXXSignal(BaseException):
    """The base class for all CLIXX signals."""

    exit_code = 0


class HelpSignal(CLIXXSignal):
    """The signal for showing help information."""


class VersionSignal(CLIXXSignal):
    """The signal for showing version information."""
