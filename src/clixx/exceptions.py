class ClixxException(Exception):
    exit_code = 128


class DefinitionError(ClixxException):
    exit_code = 129


class GroupDefinitionError(DefinitionError):
    exit_code = 130


class UsageError(ClixxException):
    exit_code = 137


class GroupUsageError(UsageError):
    exit_code = 138


class CLIExit(ClixxException):
    def __init__(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code
