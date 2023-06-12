from .arguments import (
    AppendOption,
    Argument,
    CountOption,
    FlagOption,
    HelpOption,
    Option,
    SignalOption,
    VersionOption,
    is_long_option,
    is_separator,
    is_short_option,
)
from .commands import Command, SuperCommand
from .decorators import (
    append_option,
    argument,
    argument_group,
    command,
    count_option,
    flag_option,
    help_option,
    option,
    option_group,
    simple_super_command,
    version_option,
)
from .groups import ALL, ANY, AT_LEAST_ONE, AT_MOST_ONE, EXACTLY_ONE, NONE, ArgumentGroup, GroupType, OptionGroup
from .printers import PrinterHelper, SuperPrinterHelper
from .types import (
    Bool,
    Choice,
    DateTime,
    DirPath,
    Enum,
    File,
    FilePath,
    Float,
    Int,
    IntChoice,
    IntEnum,
    Path,
    Str,
    Type,
    resolve_type,
)

__all__ = [
    # arguments
    "Argument",
    "Option",
    "FlagOption",
    "AppendOption",
    "CountOption",
    "SignalOption",
    "HelpOption",
    "VersionOption",
    "is_separator",
    "is_long_option",
    "is_short_option",
    # commands
    "Command",
    "SuperCommand",
    # decorators
    "argument",
    "option",
    "flag_option",
    "append_option",
    "count_option",
    "help_option",
    "version_option",
    "argument_group",
    "option_group",
    "command",
    "simple_super_command",
    # groups
    "GroupType",
    "ANY",
    "ALL",
    "NONE",
    "AT_LEAST_ONE",
    "AT_MOST_ONE",
    "EXACTLY_ONE",
    "ArgumentGroup",
    "OptionGroup",
    # printers
    "PrinterHelper",
    "SuperPrinterHelper",
    # types
    "Type",
    "Str",
    "Bool",
    "Int",
    "Float",
    "Choice",
    "IntChoice",
    "Enum",
    "IntEnum",
    "DateTime",
    "File",
    "Path",
    "DirPath",
    "FilePath",
    "resolve_type",
]

__title__ = "clixx"
__version__ = "0.8.0a"
__author__ = "xymy"
__email__ = "thyfan@163.com"
