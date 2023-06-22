from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union

from .arguments import AppendOption, Argument, CountOption, FlagOption, HelpOption, Option, VersionOption
from .commands import Command, CommandFunction, SimpleSuperCommand, SuperCommandFunction
from .exceptions import DefinitionError
from .groups import ANY, ArgumentGroup, GroupType, OptionGroup

if TYPE_CHECKING:
    from .printers import PrinterFactory, SuperPrinterFactory
    from .types import Type

CF = TypeVar("CF", bound=CommandFunction)
SCF = TypeVar("SCF", bound=SuperCommandFunction)
F = TypeVar("F", bound=Union[CommandFunction, SuperCommandFunction])


def _prepare_definition(func: F, obj: Argument | Option | ArgumentGroup | OptionGroup) -> None:
    if not hasattr(func, "__clixx_definition__"):
        func.__clixx_definition__ = []  # type: ignore [union-attr]
    func.__clixx_definition__.append(obj)  # type: ignore [union-attr]


def argument(
    decl: str,
    *,
    dest: str | None = None,
    nargs: int = 1,
    required: bool = False,
    type: Type | type | None = None,
    default: Any = None,
    hidden: bool = False,
    show_default: bool = False,
    metavar: str | None = None,
    help: str = "",
) -> Callable[[CF], CF]:
    """The argument, aka positional argument.

    Parameters:
        decl (str):
            The declaration for this argument.
        dest (str | None, default=None):
            The destination used to store the argument value. If ``None``, infer
            from declaration. If empty string, disable the store action.
        nargs (int, default=1):
            The number of argument values. Valid values are ``1`` or ``-1``.
        required (bool, default=False):
            Whether this argument is required or optional.
        type (Type | type | None, default=None):
            The type converter. If ``None``, use :class:`clixx.types.Str()`.
        default (Any, default=None):
            The default value used if argument omitted.
        hidden (bool, default=False):
            If ``True``, hide this argument from help information.
        show_default (bool, default=False):
            If ``True``, show the default value in help information.
        metavar (str | None, default=None):
            The argument value name used in usage. If ``None``, infer from
            declaration. If empty string, disable metavar.
        help (str, default=''):
            The help information.
    """

    def decorator(func: CF) -> CF:
        obj = Argument(
            decl,
            dest=dest,
            nargs=nargs,
            required=required,
            type=type,
            default=default,
            hidden=hidden,
            show_default=show_default,
            metavar=metavar,
            help=help,
        )
        _prepare_definition(func, obj)
        return func

    return decorator


def option(
    *decls: str,
    dest: str | None = None,
    required: bool = False,
    type: Type | type | None = None,
    default: Any = None,
    hidden: bool = False,
    show_default: bool = False,
    metavar: str | None = None,
    help: str = "",
) -> Callable[[F], F]:
    """The option, aka optional argument.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store the option value. If ``None``, infer
            from declarations. If empty string, disable the store action.
        required (bool, default=False):
            Whether this option is required or optional.
        type (Type | type | None, default=None):
            The type converter. If ``None``, use :class:`clixx.types.Str()`.
        default (Any, default=None):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        show_default (bool, default=False):
            If ``True``, show the default value in help information.
        metavar (str | None, default=None):
            The option value name used in usage. If ``None``, infer from
            declarations. If empty string, disable metavar.
        help (str, default=''):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = Option(
            *decls,
            dest=dest,
            required=required,
            type=type,
            default=default,
            hidden=hidden,
            show_default=show_default,
            metavar=metavar,
            help=help,
        )
        _prepare_definition(func, obj)
        return func

    return decorator


def flag_option(
    *decls: str,
    dest: str | None = None,
    const: Any = True,
    default: Any = False,
    hidden: bool = False,
    help: str = "",
) -> Callable[[F], F]:
    """The flag option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store the option value. If ``None``, infer
            from declarations. If empty string, disable the store action.
        const (Any, default=True):
            The constant value used if option occurred.
        default (Any, default=False):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default=''):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = FlagOption(*decls, dest=dest, const=const, default=default, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def append_option(
    *decls: str,
    dest: str | None = None,
    type: Type | type | None = None,
    hidden: bool = False,
    metavar: str | None = None,
    help: str = "",
) -> Callable[[F], F]:
    """The append option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store the option value. If ``None``, infer
            from declarations. If empty string, disable the store action.
        type (Type | type | None, default=None):
            The type converter. If ``None``, use :class:`clixx.types.Str()`.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        metavar (str | None, default=None):
            The option value name used in usage. If ``None``, infer from
            declarations. If empty string, disable metavar.
        help (str, default=''):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = AppendOption(*decls, dest=dest, type=type, hidden=hidden, metavar=metavar, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def count_option(
    *decls: str, dest: str | None = None, default: Any = 0, hidden: bool = False, help: str = ""
) -> Callable[[F], F]:
    """The count option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store the option value. If ``None``, infer
            from declarations. If empty string, disable the store action.
        default (int, default=0):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default=''):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = CountOption(*decls, dest=dest, default=default, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def help_option(*decls: str, hidden: bool = False, help: str = "Show help information and exit.") -> Callable[[F], F]:
    """The help option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default='Show help information and exit.'):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = HelpOption(*decls, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def version_option(
    *decls: str, hidden: bool = False, help: str = "Show version information and exit."
) -> Callable[[F], F]:
    """The version option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default='Show version information and exit.'):
            The help information.
    """

    def decorator(func: F) -> F:
        obj = VersionOption(*decls, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def argument_group(title: str, *, hidden: bool = True) -> Callable[[F], F]:
    """The argument group.

    Parameters:
        title (str):
            The group title.
        hidden (bool, default=True):
            If ``True``, hide this argument group from help information.
    """

    def decorator(func: F) -> F:
        obj = ArgumentGroup(title, hidden=hidden)
        _prepare_definition(func, obj)
        return func

    return decorator


def option_group(title: str, *, type: GroupType = ANY, hidden: bool = False) -> Callable[[F], F]:
    """The option group.

    Parameters:
        title (str):
            The group title.
        type (GroupType, default=ANY):
            The group constraint type.
        hidden (bool, default=False):
            If ``True``, hide this option group from help information.
    """

    def decorator(func: F) -> F:
        obj = OptionGroup(title, type=type, hidden=hidden)
        _prepare_definition(func, obj)
        return func

    return decorator


def command(
    name: str | None = None,
    version: str | None = None,
    description: str = "",
    *,
    pass_cmd: bool = False,
    printer_factory: PrinterFactory | None = None,
    printer_config: dict[str, Any] | None = None,
) -> Callable[[CF], Command]:
    def decorator(func: CF) -> Command:
        cmd = Command(
            name,
            version,
            description,
            pass_cmd=pass_cmd,
            printer_factory=printer_factory,
            printer_config=printer_config,
        )

        if hasattr(func, "__clixx_definition__"):
            it = reversed(func.__clixx_definition__)
            with suppress(StopIteration):
                group = next(it)
                while True:
                    if isinstance(group, ArgumentGroup):
                        cmd.add_argument_group(group)
                        while isinstance(member := next(it), Argument):
                            group.add(member)
                    elif isinstance(group, OptionGroup):
                        cmd.add_option_group(group)
                        while isinstance(member := next(it), Option):
                            group.add(member)
                    else:
                        if isinstance(group, Argument):
                            raise DefinitionError(f"Found non-grouped argument {group!r}.")
                        if isinstance(group, Option):
                            raise DefinitionError(f"Found non-grouped option {group!r}.")
                        raise DefinitionError(f"Found unexpected object {group!r}.")
                    group = member

        cmd.function = func
        return cmd

    return decorator


def simple_super_command(
    name: str | None = None,
    version: str | None = None,
    description: str = "",
    *,
    pass_cmd: bool = False,
    printer_factory: SuperPrinterFactory | None = None,
    printer_config: dict[str, Any] | None = None,
) -> Callable[[SCF], SimpleSuperCommand]:
    def decorator(func: SCF) -> SimpleSuperCommand:
        cmd = SimpleSuperCommand(
            name,
            version,
            description,
            pass_cmd=pass_cmd,
            printer_factory=printer_factory,
            printer_config=printer_config,
        )

        if hasattr(func, "__clixx_definition__"):
            it = reversed(func.__clixx_definition__)
            with suppress(StopIteration):
                group = next(it)
                while True:
                    if isinstance(group, ArgumentGroup):
                        raise DefinitionError("Super command does not support argument group.")
                    elif isinstance(group, OptionGroup):
                        cmd.add_option_group(group)
                        while isinstance(member := next(it), Option):
                            group.add(member)
                    else:
                        if isinstance(group, Argument):
                            raise DefinitionError("Super command does not support argument.")
                        if isinstance(group, Option):
                            raise DefinitionError(f"Found non-grouped option {group!r}.")
                        raise DefinitionError(f"Found unexpected object {group!r}.")
                    group = member

        cmd.function = func
        return cmd

    return decorator
