from __future__ import annotations

from contextlib import suppress
from typing import Any, Callable, TypeVar

from .arguments import AppendOption, Argument, CountOption, FlagOption, HelpOption, Option, VersionOption
from .commands import Command
from .exceptions import DefinitionError
from .groups import ANY, ArgumentGroup, GroupType, OptionGroup
from .printers import PrinterFactory
from .types import Type

F = TypeVar("F", bound=Callable[..., Any])


def _prepare_definition(func: F, obj: Argument | Option | ArgumentGroup | OptionGroup) -> None:
    if not hasattr(func, "__clixx_definition__"):
        func.__clixx_definition__ = []  # type: ignore
    func.__clixx_definition__.append(obj)  # type: ignore


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
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
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
    def decorator(func: F) -> F:
        obj = AppendOption(*decls, dest=dest, type=type, hidden=hidden, metavar=metavar, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def count_option(
    *decls: str, dest: str | None = None, default: Any = 0, hidden: bool = False, help: str = ""
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        obj = CountOption(*decls, dest=dest, default=default, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def help_option(*decls: str, hidden: bool = False, help: str = "Show help information and exit.") -> Callable[[F], F]:
    def decorator(func: F) -> F:
        obj = HelpOption(*decls, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def version_option(
    *decls: str, hidden: bool = False, help: str = "Show version information and exit."
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        obj = VersionOption(*decls, hidden=hidden, help=help)
        _prepare_definition(func, obj)
        return func

    return decorator


def argument_group(title: str, *, hidden: bool = False) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        obj = ArgumentGroup(title, hidden=hidden)
        _prepare_definition(func, obj)
        return func

    return decorator


def option_group(title: str, *, type: GroupType = ANY, hidden: bool = False) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        obj = OptionGroup(title, type=type, hidden=hidden)
        _prepare_definition(func, obj)
        return func

    return decorator


def command(
    name: str | None = None,
    version: str | None = None,
    *,
    pass_cmd: bool = False,
    printer_factory: PrinterFactory | None = None,
    printer_config: dict[str, Any] | None = None,
) -> Callable[[F], Command]:
    def decorator(func: F) -> Command:
        cmd = Command(name, version, pass_cmd=pass_cmd, printer_factory=printer_factory, printer_config=printer_config)
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
                        raise DefinitionError(f"Found no-grouped argument {group!r}.")
                    group = member

        cmd.register(func)
        return cmd

    return decorator
