from __future__ import annotations

import sys
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, NoReturn, Optional, TypeVar, Union, overload

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
    return {"is_exit": standalone, "is_raise": not standalone}


def _exit_command(exit_code: int | None, standalone: bool) -> int | NoReturn:
    if standalone:
        sys.exit(exit_code)
    return 0 if exit_code is None else exit_code


class _Command:
    #: The parent command. Should be set by parent.
    parent: SuperCommand | None
    #: The program name. Should be set by parent.
    prog: str | None
    #: The parsed arguments. Should be set after parsing by ``__call__``.
    args: dict[str, Any] | None

    def __init__(
        self, name: str | None = None, version: str | None = None, description: str = "", *, pass_cmd: bool = False
    ) -> None:
        self.name = name
        self.version = version
        self.description = description

        self.pass_cmd = pass_cmd

        self.parent = None
        self.prog = None
        self.args = None

        self.process_function = _dummy_func

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

    def get_prog(self) -> str:
        prog = sys.argv[0] if self.prog is None else self.prog
        if self.parent is None:
            return prog
        return f"{self.parent.get_prog()} {prog}"

    @property
    def process_function(self) -> ProcessFunction:
        """The process function."""

        return self._process_function

    @process_function.setter
    def process_function(self, value: ProcessFunction) -> None:
        self._process_function = value


class Command(_Command):
    """The command.

    Parameters:
        name (str | None, default=None):
            The name used when showing version information.
        version (str | None, default=None):
            The version used when showing version information.
        description (str, default=''):
            The description.
        pass_cmd (bool, default=False):
            If ``True``, pass this command instance to the process function.
        printer_factory (PrinterFactory | None, default=None):
            The printer factory.
        printer_config (dict[str, Any] | None, default=None):
            The printer config.
    """

    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        description: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: PrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, description, pass_cmd=pass_cmd)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

    def add_argument_group(self, group: ArgumentGroup) -> Self:
        self.argument_groups.append(group)
        return self

    def add_option_group(self, group: OptionGroup) -> Self:
        self.option_groups.append(group)
        return self

    def __call__(
        self,
        argv: list[str] | None = None,
        *,
        parent: SuperCommand | None = None,
        prog: str | None = None,
        standalone: bool = True,
    ) -> int | NoReturn:
        with PrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            self.parent = parent
            self.prog = prog

            args = self.parse_args(argv, **_interpret_standalone(standalone))
            self.args = args

            if self.pass_cmd:  # noqa
                exit_code = self.process_function(self, **args)
            else:
                exit_code = self.process_function(**args)

        return _exit_command(exit_code, standalone)

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
    """The super command.

    Parameters:
        name (str | None, default=None):
            The name used when showing version information.
        version (str | None, default=None):
            The version used when showing version information.
        description (str, default=''):
            The description.
        pass_cmd (bool, default=False):
            If ``True``, pass this command instance to the process function.
        printer_factory (SuperPrinterFactory | None, default=None):
            The super printer factory.
        printer_config (dict[str, Any] | None, default=None):
            The super printer config.
    """

    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        description: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, description, pass_cmd=pass_cmd)

        self.printer_factory = printer_factory
        self.printer_config = printer_config

        self.option_groups: list[OptionGroup] = []

    def add_option_group(self, group: OptionGroup) -> Self:
        self.option_groups.append(group)
        return self

    def iter_command_group(self) -> Iterator[CommandGroup]:
        raise NotImplementedError

    def load_command(self, name: str) -> Command | SuperCommand | None:
        raise NotImplementedError

    def __call__(
        self,
        argv: list[str] | None = None,
        *,
        parent: SuperCommand | None = None,
        prog: str | None = None,
        standalone: bool = True,
    ) -> int | NoReturn:
        with SuperPrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            self.parent = parent
            self.prog = prog

            args, ctx = self.parse_args(argv, **_interpret_standalone(standalone), return_ctx=True)
            self.args = args

            if (cmd_name := args.pop(DEST_COMMAND_NAME, None)) is None:
                raise CommandError("Missing command.")

            if (cmd := self.load_command(cmd_name)) is None:
                raise CommandError(f"Unknown command {cmd_name!r}.")

            if self.pass_cmd:  # noqa
                exit_code = self.process_function(self, **args)
            else:
                exit_code = self.process_function(**args)

            exit_code = cmd(ctx.argv_remained, standalone=standalone)

        return _exit_command(exit_code, standalone)

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


AnyCommand = TypeVar("AnyCommand", bound=Union[Command, SuperCommand])


class SimpleSuperCommand(SuperCommand):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        description: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name,
            version,
            description,
            pass_cmd=pass_cmd,
            printer_factory=printer_factory,
            printer_config=printer_config,
        )
        self.commands: dict[str, dict[str, Command | SuperCommand]] = {}

    def add_command(self, group_name: str, cmd_name: str, cmd: Command | SuperCommand) -> Self:
        group_dict = self.commands.setdefault(group_name, {})
        group_dict[cmd_name] = cmd
        return self

    def register_command(self, group_name: str, cmd_name: str) -> Callable[[AnyCommand], AnyCommand]:
        def decorator(cmd: AnyCommand) -> AnyCommand:
            self.add_command(group_name, cmd_name, cmd)
            return cmd

        return decorator

    def iter_command_group(self) -> Iterator[CommandGroup]:
        for group_name, group_dict in self.commands.items():
            group = CommandGroup(group_name)
            for cmd_name in group_dict:
                group.add(cmd_name)
            yield group

    def load_command(self, name: str) -> Command | SuperCommand | None:
        for group_dict in self.commands.values():
            with suppress(KeyError):
                return group_dict[name]
        return None
