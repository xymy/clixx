from __future__ import annotations

import sys
from contextlib import suppress
from typing import Any, Callable, Iterator, Literal, Optional, TypeVar, Union, overload

from typing_extensions import Never, Self, TypeAlias

from .constants import DEST_COMMAND_NAME
from .exceptions import CommandError, ParserContextError
from .groups import ArgumentGroup, CommandGroup, OptionGroup
from .parsers import Parser, SuperParser
from .printers import PrinterFactory, PrinterHelper, SuperPrinterFactory, SuperPrinterHelper

CommandFunction: TypeAlias = Callable[..., Optional[int]]
SuperCommandFunction: TypeAlias = Callable[..., Optional["dict[str, Any]"]]


def _print_args(*args: Any, **kwargs: Any) -> None:
    from rich.console import Console

    console = Console()
    if args:
        if len(args) == 1:
            console.print(args[0])
        else:
            raise AssertionError
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
    return exit_code if exit_code is not None else 0


class _Command:
    parent: SuperCommand | None = None
    _prog: str | None = None
    _args: dict[str, Any] | None = None
    _argv: list[str] | None = None

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

    def get_cmd_path(self) -> str:
        if self.parent is None:
            return self.prog
        return f"{self.parent.get_cmd_path()} {self.prog}"

    @property
    def prog(self) -> str:
        if self._prog is None:
            raise ParserContextError("This command is not running.")
        return self._prog

    @prog.setter
    def prog(self, value: str) -> None:
        self._prog = value

    @property
    def args(self) -> dict[str, Any]:
        if self._args is None:
            raise ParserContextError("This command is not running.")
        return self._args

    @args.setter
    def args(self, value: dict[str, Any]) -> None:
        self._args = value

    @property
    def argv(self) -> list[str]:
        if self._argv is None:
            raise ParserContextError("This command is not running.")
        return self._argv

    @argv.setter
    def argv(self, value: list[str]) -> None:
        self._argv = value

    @staticmethod
    def _check_parent_args(
        parent: SuperCommand | None, prog: str | None, args: dict[str, Any] | None, argv: list[str] | None
    ) -> None:
        if parent is not None:
            if prog is None:
                raise ParserContextError("Parent command must provide prog.")
            if args is None:
                raise ParserContextError("Parent command must provide args.")
            if argv is None:
                raise ParserContextError("Parent command must provide argv.")


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
            If ``True``, pass this command instance to the command function.
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

        self.function = _print_args

        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

        self.printer_factory = printer_factory
        self.printer_config = printer_config

    @property
    def function(self) -> CommandFunction:
        """The command function."""

        return self._function

    @function.setter
    def function(self, value: CommandFunction) -> None:
        self._function = value

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
        self._check_parent_args(parent, prog, args, argv)
        self.parent = parent
        self.prog = prog if prog is not None else sys.argv[0]
        self.args = args = args if args is not None else {}
        self.argv = argv = argv if argv is not None else sys.argv[1:]

        with PrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            parser = Parser(self.argument_groups, self.option_groups)
            parser.parse_args(args, argv)

            if self.pass_cmd:  # noqa
                exit_code = self.function(self, **args)
            else:
                exit_code = self.function(**args)
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
            If ``True``, pass this command instance to the command function.
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

        self.function = _print_args

        self.option_groups: list[OptionGroup] = []

        self.printer_factory = printer_factory
        self.printer_config = printer_config

    @property
    def function(self) -> SuperCommandFunction:
        """The super command function."""

        return self._function

    @function.setter
    def function(self, value: SuperCommandFunction) -> None:
        self._function = value

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
        self._check_parent_args(parent, prog, args, argv)
        self.parent = parent
        self.prog = prog if prog is not None else sys.argv[0]
        self.args = args = args if args is not None else {}
        self.argv = argv = argv if argv is not None else sys.argv[1:]

        with SuperPrinterHelper(self, self.printer_factory, self.printer_config, **_interpret_standalone(standalone)):
            parser = SuperParser(self.option_groups)
            ctx = parser.parse_args(args, argv)

            if (cmd_name := args.pop(DEST_COMMAND_NAME, None)) is None:
                raise CommandError("Missing command.")

            if (cmd := self.load_command(cmd_name)) is None:
                raise CommandError(f"Unknown command {cmd_name!r}.")

            if self.pass_cmd:  # noqa
                args = self.function(self, **args)
            else:
                args = self.function(**args)

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
