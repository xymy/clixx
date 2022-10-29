from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.style import Style
from rich.table import Table

from .commands import Command


class RichPrinter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.console_params: dict[str, Any] = {
            "markup": config.pop("markup", False),
            "emoji": config.pop("emoji", False),
            "highlight": config.pop("highlight", False),
        }

    def _print_error(self, console: Console, message: str) -> None:
        # SECURITY: ``message`` usually contains user input.
        # To avoid injection, Rich's markup must be disabled.
        message = f"Error: {message}"
        style = Style(color="red", bold=True)
        console.out(message, style=style, highlight=False)

    def _print_usage(self, console: Console, cmd: Command) -> None:
        prog = cmd.get_prog()
        usage = f"Usage: {prog}"

        if cmd.option_groups:
            usage += " [OPTIONS]..."

        metavars: list[str] = []
        for argument_group in cmd.argument_groups:
            for argument in argument_group:
                if metavar := argument.show_metavar():
                    if not argument.required:
                        metavar = f"[{metavar}]"
                    if argument.nargs == -1:
                        metavar += "..."
                    metavars.append(metavar)

        if metavars:
            usage += " " + " ".join(metavars)

        console.out(usage, highlight=False)

    def _print_try_help(self, console: Console, cmd: Command) -> None:
        prog = cmd.get_prog()
        option = self.config.get("try_help_option", "--help")
        try_help = f"Try '{prog} {option}' for help."
        console.out(try_help, highlight=False)

    def print_error(self, cmd: Command, message: str) -> None:
        console = Console(stderr=True, **self.console_params)
        self._print_usage(console, cmd)
        self._print_try_help(console, cmd)
        console.out()
        self._print_error(console, message)

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
                if metavar := option.show_metavar():
                    opts += " " + metavar
                table.add_row(opts, option.help)
            console.print(table)

    def print_version(self, cmd: Command) -> None:
        console = Console(**self.console_params)
        version_info = f"{cmd.name} {cmd.version}"
        console.print(version_info, highlight=False)
