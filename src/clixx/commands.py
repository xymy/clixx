from __future__ import annotations

from .groups import ArgumentGroup, OptionGroup
from .parser import Parser


class Command:
    def __init__(self, name: str | None = None, version: str | None = None, *, parent: Command | None = None) -> None:
        self.name = name
        self.version = version
        self.parent = parent
        self.argument_groups: list[ArgumentGroup] = []
        self.option_groups: list[OptionGroup] = []

    def add_argument_group(self, *args, **kwargs) -> ArgumentGroup:
        group = ArgumentGroup(*args, **kwargs)
        self.argument_groups.append(group)
        return group

    def add_option_group(self, *args, **kwargs) -> OptionGroup:
        group = OptionGroup(*args, **kwargs)
        self.option_groups.append(group)
        return group

    def parse_args(self, argv):
        parser = Parser(self.argument_groups, self.option_groups)
        parser.parse_args(argv)
