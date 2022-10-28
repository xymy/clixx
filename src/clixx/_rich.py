from __future__ import annotations

from typing import Any, TextIO

from rich.console import Console
from rich.style import Style

from .commands import Command


def echo(
    message: str,
    *,
    fg: str | None = None,
    bg: str | None = None,
    bold: bool | None = None,
    dim: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strike: bool | None = None,
    file: TextIO,
) -> None:
    console = Console(file=file)
    style = Style(color=fg, bgcolor=bg, bold=bold, dim=dim, italic=italic, underline=underline, strike=strike)
    console.out(message, style=style, highlight=False)


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
        console.print(usage, markup=False, emoji=False, highlight=False, soft_wrap=True)

    def _print_try_help(self, console: Console, cmd: Command) -> None:
        prog = cmd.get_prog()
        option = self.config.get("try_help_option", "--help")
        try_help = f"Try '{prog} {option}' for help."
        console.print(try_help, markup=False, emoji=False, highlight=False, soft_wrap=True)

    def print_error(self, cmd: Command, message: str) -> None:
        console = Console(stderr=True, **self.console_params)
        self._print_usage(console, cmd)
        self._print_try_help(console, cmd)
        console.out()
        self._print_error(console, message)

    def print_help(self, cmd: Command) -> None:
        ...

    def print_version(self, cmd: Command) -> None:
        console = Console(**self.console_params)
        prog = cmd.get_prog()
        version_info = f"{prog} {cmd.version}"
        console.print(version_info, markup=False, emoji=False, highlight=False, soft_wrap=True)
