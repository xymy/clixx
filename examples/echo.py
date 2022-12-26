from __future__ import annotations

import clixx


@clixx.command("MyEcho", "1.0.0", pass_cmd=True)
@clixx.argument_group("Arguments", hidden=True)
@clixx.argument("strings", nargs=-1)
@clixx.option_group("Options")
@clixx.help_option("-h", "--help")
@clixx.version_option("-V", "--version")
@clixx.count_option("-v", "--verbose", help="Show more information.")
def main(cmd: clixx.Command, strings: list[str], verbose: int) -> None:
    for string in strings:
        print(string)

    if verbose > 0:
        print(cmd.args)


if __name__ == "__main__":
    main()
