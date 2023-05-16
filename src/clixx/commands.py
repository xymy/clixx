from __future__ import annotations

import sys
from contextlib import suppress
from typing import Any, Callable, Iterator, Literal, Optional, TypeVar, Union, overload

from typing_extensions import Never, Self, TypeAlias

from .constants import DEST_COMMAND_NAME
from .exceptions import CommandError
from .groups import ArgumentGroup, CommandGroup, OptionGroup
from .parsers import Parser, SuperParser
from .printers import PrinterFactory, PrinterHelper, SuperPrinterFactory, SuperPrinterHelper

ProcessFunction: TypeAlias = Callable[..., Optional[int]]
SuperProcessFunction: TypeAlias = Callable[..., Optional["dict[str, Any]"]]


def _dummy_function(*args: Any, **kwargs: Any) -> None:
    from rich.console import Console

    console = Console()
    if args:
        if len(args) == 1:
            console.print(args[0])
        else:
            console.print(args)
    console.print(kwargs)


def _interpret_standalone(standalone: bool) -> dict[str, bool]:
    return {"is_exit": standalone, "is_raise": not standalone}


@overload
def _exit_command(exit_code: int | None, standalone: Literal[False]) -> int:
    ...


@overload
def _exit_command(exit_code: int | None, standalone: Literal[True]) -> Never:
    ...


@overload
def _exit_command(exit_code: int | None, standalone: bool) -> int | Never:
    ...


def _exit_command(exit_code: int | None, standalone: bool) -> int | Never:
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
        self,
        name: str | None = None,
        version: str | None = None,
        description: str = "",
        epilog: str = "",
        *,
        pass_cmd: bool = False,
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.epilog = epilog

        self.pass_cmd = pass_cmd

        self.parent = None
        self.prog = None
        self.args = None

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


class Command(_Command):
    """The command.

    Parameters:
        name (str | None, default=None):
            The name to display in the version information.
        version (str | None, default=None):
            The version to display in the version information.
        description (str, default=''):
            The description to display before the main help.
        epilog (str, default=''):
            The epilog to display after the main help.
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
        epilog: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: PrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, description, epilog, pass_cmd=pass_cmd)

        self.process_function = _dummy_function

        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

        self.printer_factory = printer_factory
        self.printer_config = printer_config

    @property
    def process_function(self) -> ProcessFunction:
        """The process function."""

        return self._process_function

    @process_function.setter
    def process_function(self, value: ProcessFunction) -> None:
        self._process_function = value

    def add_argument_group(self, group: ArgumentGroup) -> Self:
        self.argument_groups.append(group)
        return self

    def add_option_group(self, group: OptionGroup) -> Self:
        self.option_groups.append(group)
        return self

    def __call__(
        self,
        args: dict[str, Any] | None = None,
        argv: list[str] | None = None,
        *,
        parent: SuperCommand | None = None,
        prog: str | None = None,
        standalone: bool = True,
    ) -> int | Never:
        with PrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            self.parent = parent
            self.prog = prog
            self.args = args = args if args is not None else {}
            self.argv = argv = argv if argv is not None else sys.argv[1:]

            parser = Parser(self.argument_groups, self.option_groups)
            parser.parse_args(args, argv)

            if self.pass_cmd:  # noqa
                exit_code = self.process_function(self, **args)
            else:
                exit_code = self.process_function(**args)
        return _exit_command(exit_code, standalone)


class SuperCommand(_Command):
    """The super command.

    Parameters:
        name (str | None, default=None):
            The name to display in the version information.
        version (str | None, default=None):
            The version to display in the version information.
        description (str, default=''):
            The description to display before the main help.
        epilog (str, default=''):
            The epilog to display after the main help.
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
        epilog: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, description, epilog, pass_cmd=pass_cmd)

        self.super_process_function = _dummy_function

        self.option_groups: list[OptionGroup] = []

        self.printer_factory = printer_factory
        self.printer_config = printer_config

    @property
    def super_process_function(self) -> SuperProcessFunction:
        """The super process function."""

        return self._super_process_function

    @super_process_function.setter
    def super_process_function(self, value: SuperProcessFunction) -> None:
        self._super_process_function = value

    def add_option_group(self, group: OptionGroup) -> Self:
        self.option_groups.append(group)
        return self

    def iter_command_group(self) -> Iterator[CommandGroup]:
        raise NotImplementedError

    def load_command(self, name: str) -> Command | SuperCommand | None:
        raise NotImplementedError

    def __call__(
        self,
        args: dict[str, Any] | None = None,
        argv: list[str] | None = None,
        *,
        parent: SuperCommand | None = None,
        prog: str | None = None,
        standalone: bool = True,
    ) -> int | Never:
        with SuperPrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            self.parent = parent
            self.prog = prog
            self.args = args = args if args is not None else {}
            self.argv = argv = argv if argv is not None else sys.argv[1:]

            parser = SuperParser(self.option_groups)
            ctx = parser.parse_args(args, argv)

            if (cmd_name := args.pop(DEST_COMMAND_NAME, None)) is None:
                raise CommandError("Missing command.")

            if (cmd := self.load_command(cmd_name)) is None:
                raise CommandError(f"Unknown command {cmd_name!r}.")

            if self.pass_cmd:  # noqa
                args = self.super_process_function(self, **args)
            else:
                args = self.super_process_function(**args)

            args = args if args is not None else {}
            exit_code = cmd(args, ctx.argv_remained, parent=self, standalone=standalone)
        return _exit_command(exit_code, standalone)


AnyCommand = TypeVar("AnyCommand", bound=Union[Command, SuperCommand])


class SimpleSuperCommand(SuperCommand):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        description: str = "",
        epilog: str = "",
        *,
        pass_cmd: bool = False,
        printer_factory: SuperPrinterFactory | None = None,
        printer_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name,
            version,
            description,
            epilog,
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
