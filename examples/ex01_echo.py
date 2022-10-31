from rich.console import Console

import clixx


def main() -> None:
    cmd = clixx.Command("MyEcho", "1.0")

    arguments = clixx.ArgumentGroup("Arguments", hidden=True)
    arguments += clixx.Argument("strings", nargs=-1)
    cmd.add_argument_group(arguments)

    options = clixx.OptionGroup("Options")
    options += clixx.HelpOption("-h", "--help")
    options += clixx.VersionOption("-V", "--version")
    options += clixx.CountOption("-v", "--verbose", help="Show more information.")
    cmd.add_option_group(options)

    # ------------------------------------------------------------------------

    args = cmd.parse_args()

    console = Console()

    for string in args["strings"]:
        console.print(string)

    if args["verbose"] > 0:
        console.print(args)


if __name__ == "__main__":
    main()
