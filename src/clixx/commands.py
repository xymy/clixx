from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, NoReturn, Optional, overload

from .constants import DEST_COMMAND_NAME
from .exceptions import CommandError
from .groups import ArgumentGroup, CommandGroup, OptionGroup
from .parsers import Context, Parser, SuperParser
from .printers import PrinterFactory, PrinterHelper, SuperPrinterFactory, SuperPrinterHelper

if TYPE_CHECKING:
    from typing_extensions import Self

ProcessFunction = Callable[..., Optional[int]]


def _dummy_func(*args: Any, **kwargs: Any) -> None:
    pass


def _interpret_standalone(standalone: bool) -> dict[str, bool]:
    return {"is_exit": standalone, "is_rasie": not standalone}


def _norm_exit_code(exit_code: int | None) -> int:
    return 0 if exit_code is None else exit_code


class _Command:
    #: The program name. Should be set by parent.
    prog: str | None
    #: The parent command. Should be set by parent.
    parent: SuperCommand | None

    def __init__(self, name: str | None = None, version: str | None = None) -> None:
        self.prog = None
        self.parent = None

        self.name = name
        self.version = version

        self.process_function: ProcessFunction = _dummy_func

    def _init(self, prog: str | None, parent: SuperCommand | None) -> None:
        self.prog = prog
        self.parent = parent

    def get_prog(self) -> str:
        prog = sys.argv[0] if self.prog is None else self.prog
        if self.parent is None:
            return prog
        return f"{self.parent.get_prog()} {prog}"

    def get_name(self) -> str:
        if self.name is not None:
            return self.name
        if self.parent is not None:
            return self.parent.get_name()
        return "Unknown Program"

    def get_version(self) -> str:
        if self.version is not None:
            return self.version
        if self.parent is not None:
            return self.parent.get_version()
        return "Unknown Version"

    def register(self, func: ProcessFunction) -> None:
        self.process_function = func


class Command(_Command):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        *,
        printer_factory: PrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

    def add_argument_group(self, group: ArgumentGroup) -> Self:  # type: ignore [valid-type]
        self.argument_groups.append(group)
        return self

    def add_option_group(self, group: OptionGroup) -> Self:  # type: ignore [valid-type]
        self.option_groups.append(group)
        return self

    def __call__(self, argv: list[str] | None = None, *, standalone: bool = True) -> int | NoReturn:
        args = self.parse_args(argv, **_interpret_standalone(standalone))

        exit_code = self.process_function(**args)
        if standalone:
            sys.exit(exit_code)
        return _norm_exit_code(exit_code)

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: Literal[True]
    ) -> tuple[dict[str, Any], Context]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: Literal[False]
    ) -> dict[str, Any]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False
    ) -> dict[str, Any]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: bool
    ) -> dict[str, Any] | tuple[dict[str, Any], Context]:
        ...

    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: bool = False
    ) -> dict[str, Any] | tuple[dict[str, Any], Context]:
        args: dict[str, Any] = {}
        argv = sys.argv[1:] if argv is None else argv
        with PrinterHelper(self, self.printer_factory, self.printer_config, is_exit=is_exit, is_raise=is_raise):
            parser = Parser(self.argument_groups, self.option_groups)
            ctx = parser.parse_args(args, argv)

        if return_ctx:
            return args, ctx
        return args


class SuperCommand(_Command):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        *,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.option_groups: list[OptionGroup] = []

    def iter_command_group(self) -> Iterator[CommandGroup]:
        raise NotImplementedError

    def load_command(self, name: str) -> Command | SuperCommand | None:
        raise NotImplementedError

    def add_option_group(self, group: OptionGroup) -> Self:  # type: ignore [valid-type]
        self.option_groups.append(group)
        return self

    def __call__(self, argv: list[str] | None = None, *, standalone: bool = True) -> int | NoReturn:
        args, ctx = self.parse_args(argv, **_interpret_standalone(standalone), return_ctx=True)
        with SuperPrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            if (cmd_name := args.pop(DEST_COMMAND_NAME, None)) is None:
                raise CommandError("Missing command.")

            if (cmd := self.load_command(cmd_name)) is None:
                raise CommandError("Unknown command.")

        self.process_function(**args)
        exit_code = cmd(ctx.argv_remained, standalone=standalone)  # type: ignore

        if standalone:
            sys.exit(exit_code)
        return _norm_exit_code(exit_code)

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: Literal[True]
    ) -> tuple[dict[str, Any], Context]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: Literal[False]
    ) -> dict[str, Any]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False
    ) -> dict[str, Any]:
        ...

    @overload
    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: bool
    ) -> dict[str, Any] | tuple[dict[str, Any], Context]:
        ...

    def parse_args(
        self, argv: list[str] | None = None, *, is_exit: bool = True, is_raise: bool = False, return_ctx: bool = False
    ) -> dict[str, Any] | tuple[dict[str, Any], Context]:
        args: dict[str, Any] = {}
        argv = sys.argv[1:] if argv is None else argv
        with SuperPrinterHelper(self, self.printer_factory, self.printer_config, is_exit=is_exit, is_raise=is_raise):
            parser = SuperParser(self.option_groups)
            ctx = parser.parse_args(args, argv)

        if return_ctx:
            return args, ctx
        return args
