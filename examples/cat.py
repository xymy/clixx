from __future__ import annotations

import sys
from pathlib import Path

import clixx


@clixx.command("MyCat", "1.0.0")
@clixx.argument_group("Arguments", hidden=True)
@clixx.argument("paths", nargs=-1, type=clixx.Path(exists=True, readable=True))
@clixx.option_group("Options")
@clixx.help_option("-h", "--help")
@clixx.version_option("-V", "--version")
def main(paths: list[Path]) -> None:
    for path in paths:
        sys.stdout.buffer.write(path.read_bytes())


if __name__ == "__main__":
    main()
