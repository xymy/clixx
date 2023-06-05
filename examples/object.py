from __future__ import annotations

from typing import Any

from rich.console import Console

import clixx


def main(**kwargs: dict[str, Any]) -> None:
    console = Console()
    console.print(kwargs)


cmd = clixx.Command("Object", "1.0.0")
cmd.add_argument_group(clixx.ArgumentGroup("Arguments").add(clixx.Argument("strings", nargs=-1)))
cmd.add_option_group(
    clixx.OptionGroup("Options")
    .add(clixx.Option("-n", "--number", type=clixx.Int(), help="This is a number."))
    .add(clixx.Option("-p", "--path", type=clixx.Path(), help="This is a path."))
    .add(clixx.FlagOption("-f", "--flag", help="This is a flag"))
    .add(clixx.HelpOption("-h", "--help"))
    .add(clixx.VersionOption("-V", "--version"))
)

cmd.function = main

if __name__ == "__main__":
    cmd()
