from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .commands import Command, SuperCommand
from .exceptions import CLIXXException


def _get_console_params(config: dict[str, Any]) -> dict[str, Any]:
    params = {}
    for param in ["markup", "emoji", "highlight", "highlighter"]:
        if param in config:
            params[param] = config.pop(param)
    return params


def _print_error(console: Console, exc: CLIXXException) -> None:
    # SECURITY: ``message`` usually contains user input.
    # To avoid injection, construct :class:`rich.text.Text`.
    style = Style(color="red", bold=True)
    text = Text("Error: " + exc.format_message(), style=style)
    console.print(text, soft_wrap=True)


class RichPrinter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.console_params = _get_console_params(config)

    def _print_usage(self, console: Console, cmd: Command) -> None:
        parts = ["Usage: ", cmd.get_prog()]

        if cmd.option_groups:
            parts.append(" ")
            parts.append("[OPTIONS]...")

        metavars: list[str] = []
        for argument_group in cmd.argument_groups:
            for argument in argument_group:
                if metavar := argument.resolve_metavar():
                    if not argument.required:
                        metavar = f"[{metavar}]"
                    if argument.nargs == -1:
                        metavar += "..."
                    metavars.append(metavar)

        if metavars:
            parts.append(" ")
            parts.append(" ".join(metavars))

        text = Text.assemble(parts)
        console.print(text)

    def _print_try_help(self, console: Console, cmd: Command) -> None:
        prog = cmd.get_prog()
        option = self.config.get("try_help_option", "--help")
        text = Text(f"Try '{prog} {option}' for help.")
        console.print(text, soft_wrap=True)

    def print_error(self, cmd: Command, exc: CLIXXException) -> None:
        console = Console(stderr=True, **self.console_params)
        self._print_usage(console, cmd)
        self._print_try_help(console, cmd)
        console.print()
        _print_error(console, exc)

    def print_help(self, cmd: Command) -> None:
        console = Console(**self.console_params)
        self._print_usage(console, cmd)

        for argument_group in cmd.argument_groups:
            if argument_group.hidden:
                continue
            console.print(f"\n{argument_group.title}:")
            table = Table(box=None, padding=(0, 0, 0, 2), show_header=False, show_edge=False)
            table.add_column("Arguments")
            table.add_column("Descriptions")
            for argument in argument_group:
                if argument.hidden:
                    continue
                table.add_row(argument.argument, argument.help)
            console.print(table)

        for option_group in cmd.option_groups:
            if option_group.hidden:
                continue
            console.print(f"\n{option_group.title}:")
            table = Table(box=None, padding=(0, 0, 0, 2), show_header=False, show_edge=False)
            table.add_column("Options")
            table.add_column("Descriptions")
            for option in option_group:
                if option.hidden:
                    continue
                opts = ", ".join(option.short_options + option.long_options)
                if metavar := option.resolve_metavar():
                    opts += " " + metavar
                table.add_row(opts, option.help)
            console.print(table)

    def print_version(self, cmd: Command) -> None:
        console = Console(**self.console_params)
        version_info = f"{cmd.name} {cmd.version}"
        console.print(version_info, highlight=False)


class RichSuperPrinter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.console_params = _get_console_params(config)

    def print_error(self, cmd: SuperCommand, exc: CLIXXException) -> None:
        ...

    def print_help(self, cmd: SuperCommand) -> None:
        ...

    def print_version(self, cmd: SuperCommand) -> None:
        ...
