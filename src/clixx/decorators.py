from __future__ import annotations

from typing import Any, Callable, TypeVar

from .arguments import AppendOption, Argument, CountOption, FlagOption, HelpOption, Option, VersionOption
from .types import Type

F = TypeVar("F", bound=Callable[..., Any])


def _prepare_definition(func: F, obj: Argument | Option) -> None:
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
