from __future__ import annotations

from rich.console import Console

import clixx


@clixx.command("MyEcho", "1.0.0", pass_cmd=True)
@clixx.argument_group("Arguments")
@clixx.argument("strings", nargs=-1)
@clixx.option_group("Style Options", type=clixx.AT_MOST_ONE)
@clixx.flag_option("--red", help="print red message.")
@clixx.flag_option("--green", help="print green message.")
@clixx.flag_option("--blue", help="print blue message.")
@clixx.option_group("General Options")
@clixx.help_option("-h", "--help")
@clixx.version_option("-V", "--version")
@clixx.count_option("-v", "--verbose", help="Show more information.")
def main(cmd: clixx.Command, strings: list[str], red: bool, green: bool, blue: bool, verbose: int) -> None:
    # At most one color will be True.
    style: str | None = None
    if red:
        style = "red"
    elif green:
        style = "green"
    elif blue:
        style = "blue"

    # Print colorful message via Rich.
    console = Console()
    console.out(*strings, style=style, highlight=False)

    # Print prog, argv and args for verbose.
    if verbose > 0:
        console.out()
        console.out("-" * 80)
        console.out("prog:", cmd.get_prog())
        console.print("argv:", cmd.argv)
        console.print("args:", cmd.args)


if __name__ == "__main__":
    main()
