from .arguments import Argument, CountOption, FlagOption, Option, SignalOption
from .groups import ALL, ANY, AT_LEAST_ONE, AT_MOST_ONE, EXACTLY_ONE, NONE, ArgumentGroup, GroupType, OptionGroup
from .types import Bool, Choice, DateTime, DirPath, File, FilePath, Float, Int, IntChoice, Path, Str, Type

__all__ = [
    # arguments
    "Argument",
    "Option",
    "FlagOption",
    "CountOption",
    "SignalOption",
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
