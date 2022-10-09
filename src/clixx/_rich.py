from __future__ import annotations

from typing import TextIO

from rich.console import Console
from rich.style import Style


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
