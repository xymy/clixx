from typing import Final

SEPARATOR: Final = "--"
LONG_PREFIX: Final = "--"
SHORT_PREFIX: Final = "-"
LONG_PREFIX_LEN: Final = len(LONG_PREFIX)
SHORT_PREFIX_LEN: Final = len(SHORT_PREFIX)

# The reserved characters for arguments and options.
RESERVED_CHARACTERS: Final = frozenset("\"'<>")

# The special destination used by parser to store command name.
DEST_COMMAND_NAME: Final = "<command_name>"
