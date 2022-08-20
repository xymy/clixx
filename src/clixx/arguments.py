from abc import ABCMeta, abstractmethod
from keyword import iskeyword
from typing import Any, List, Optional, Sequence, Tuple

from .exceptions import DefinitionError


def _check_dest(dest: str) -> str:
    dest = dest.replace("-", "_")
    if not dest.isidentifier():
        raise DefinitionError(f"{dest!r} is not a valid identifier")
    if iskeyword(dest):
        raise DefinitionError(f"{dest!r} is a keyword")
    return dest


def _check_nargs(nargs: int) -> int:
    if nargs < -1:
        raise DefinitionError(f"require nargs >= -1, got {nargs!r}")
    return nargs


def _parse_decls(decls: Sequence[str]) -> Tuple[List[str], List[str]]:
    if not decls:
        raise DefinitionError("no option defined")

    long_options: List[str] = []
    short_options: List[str] = []
    for decl in decls:
        if decl.startswith("--"):
            long_options.append(decl)
        elif decl.startswith("-"):
            short_options.append(decl)
        else:
            raise DefinitionError(f"{decl!r} is not a valid option")
    return long_options, short_options


class ArgumentBase(metaclass=ABCMeta):
    """Abstract base class for argument and option."""

    def __init__(self, nargs: int = 1, required: bool = False, default: Any = None, help: Optional[str] = None) -> None:
        self.nargs = _check_nargs(nargs)
        self.required = required
        self.default = default
        self.help = help


class Argument(ArgumentBase):
    def __init__(
        self,
        decl: str,
        *,
        dest: Optional[str] = None,
        nargs: int = 1,
        required: bool = False,
        default: Any = None,
        help: Optional[str] = None,
    ) -> None:
        super().__init__(nargs=nargs, required=required, default=default, help=help)
        self.dest, self.argument = self._parse(decl, dest=dest)

    @staticmethod
    def _parse(decl: str, *, dest: Optional[str]) -> Tuple[str, str]:
        if dest is not None:
            dest = _check_dest(dest)
        else:
            dest = _check_dest(decl)
        return dest, decl


class OptionBase(ArgumentBase, metaclass=ABCMeta):
    """Abstract base class for option."""

    def __init__(
        self,
        *decls: str,
        dest: Optional[str] = None,
        nargs: int = 1,
        required: bool = False,
        default: Any = None,
        help: Optional[str] = None,
    ) -> None:
        super().__init__(nargs=nargs, required=required, default=default, help=help)
        self.dest, self.long_options, self.short_options = self._parse(decls, dest=dest)

    @staticmethod
    @abstractmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        ...


class Option(OptionBase):
    @staticmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        long_options, short_options = _parse_decls(decls)

        if dest is not None:
            dest = _check_dest(dest)
        elif long_options:
            dest = _check_dest(long_options[0][2:])
        else:
            dest = _check_dest(short_options[0][1:])
        return dest, long_options, short_options


class Flag(Option):
    def __init__(
        self,
        *decls: str,
        dest: Optional[str] = None,
        required: bool = False,
        default: bool = False,
        help: Optional[str] = None,
    ) -> None:
        super().__init__(*decls, dest=dest, nargs=0, required=required, default=default, help=help)


class SideOption(OptionBase):
    def __init__(
        self, *decls: str, nargs: int = 1, required: bool = False, default: Any = None, help: Optional[str] = None
    ) -> None:
        super().__init__(nargs=nargs, required=required, default=default, help=help)
        self.long_options, self.short_options = _parse_decls(decls)

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        return "", *_parse_decls(decls)


class SideFlag(SideOption):
    def __init__(self, *decls: str, required: bool = False, default: bool = False, help: Optional[str] = None) -> None:
        super().__init__(*decls, nargs=0, required=required, default=default, help=help)
