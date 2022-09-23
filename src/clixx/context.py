from __future__ import annotations

from typing import Any


class Context:
    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
        self.index = 0
        self.pos = 0
        self.args: dict[str, Any] = {}

        self._curr_arg: str | None = None

    @property
    def next_arg(self) -> str | None:
        try:
            arg = self.argv[self.index]
            self.index += 1
        except IndexError:
            arg = None
        self._curr_arg = arg
        return arg

    @property
    def curr_arg(self) -> str | None:
        return self._curr_arg
