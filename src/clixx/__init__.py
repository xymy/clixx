from .arguments import Argument, CountOption, FlagOption, Option, SignalOption
from .commands import Command
from .groups import ALL, ANY, AT_LEAST_ONE, AT_MOST_ONE, EXACTLY_ONE, NONE, ArgumentGroup, GroupType, OptionGroup
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
)

__all__ = [
    # arguments
    "Argument",
    "Option",
    "FlagOption",
    "CountOption",
    "SignalOption",
    # commands
    "Command",
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
]

__title__ = "clixx"
__version__ = "0.2.0a"
__author__ = "xymy"
__email__ = "thyfan@163.com"
