from keyword import iskeyword
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .constants import LONG_PREFIX, SHORT_PREFIX
from .exceptions import DefinitionError, InternalError
from .types import Str, Type


def _check_dest(dest: str) -> str:
    dest = dest.replace("-", "_")
    if not dest.isidentifier():
        raise DefinitionError(f"{dest!r} is not a valid identifier.")
    if iskeyword(dest):
        raise DefinitionError(f"{dest!r} is a keyword.")
    return dest


def _parse_decls(decls: Sequence[str]) -> Tuple[List[str], List[str]]:
    if not decls:
        raise DefinitionError("No option defined.")

    long_options: List[str] = []
    short_options: List[str] = []
    for decl in decls:
        if decl.startswith(LONG_PREFIX):
            if len(decl) == len(LONG_PREFIX):
                raise DefinitionError(f"{decl!r} is not a valid option.")
            if len(decl) <= len(LONG_PREFIX) + 1:
                raise DefinitionError(f"{decl!r} is too short.")
            long_options.append(decl)
        elif decl.startswith(SHORT_PREFIX):
            if len(decl) == len(SHORT_PREFIX):
                raise DefinitionError(f"{decl!r} is not a valid option.")
            if len(decl) >= len(SHORT_PREFIX) + 2:
                raise DefinitionError(f"{decl!r} is too long.")
            short_options.append(decl)
        else:
            raise DefinitionError(f"Option must start with {LONG_PREFIX!r} or {SHORT_PREFIX!r}, got {decl!r}.")
    return long_options, short_options


class Argument:
    """The positional argument."""

    def __init__(
        self,
        decl: str,
        *,
        dest: Optional[str] = None,
        nargs: int = 1,
        required: bool = False,
        type: Optional[Type] = None,
        default: Any = None,
        help: str = "",
    ) -> None:
        self.dest, self.argument = self._parse(decl, dest=dest)
        self.nargs = nargs
        self.required = required
        self.type = type or Str()
        self.default = default
        self.help = help

    @staticmethod
    def _parse(decl: str, *, dest: Optional[str]) -> Tuple[str, str]:
        # Infer the destination argument from the declaration if dest not given.
        if dest is not None:
            dest = _check_dest(dest)
        else:
            dest = _check_dest(decl)
        return dest, decl

    def _store(self, args: Dict[str, Any], values: Sequence[str]) -> None:
        result = tuple(map(self.type.convert_str, values))
        args[self.dest] = result

    def _store_default(self, args: Dict[str, Any]) -> None:
        if self.nargs == 1:
            result = self.type(self.default)
        else:
            if isinstance(self.default, (tuple, list)):
                result = tuple(map(self.type, self.default))
            else:
                result = (self.type(self.default),)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return self._nargs

    @nargs.setter
    def nargs(self, value: int) -> None:
        if not (value >= 1 or value == -1):
            raise DefinitionError(f"Require nargs >= 1 or nargs == -1, got {value!r}.")
        self._nargs = value


class Option:
    """The optional argument."""

    def __init__(
        self,
        *decls: str,
        dest: Optional[str] = None,
        required: bool = False,
        type: Optional[Type] = None,
        default: Any = None,
        help: str = "",
    ) -> None:
        self.dest, self.long_options, self.short_options = self._parse(decls, dest=dest)
        self.required = required
        self.type = type or Str()
        self.default = default
        self.help = help

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        long_options, short_options = _parse_decls(decls)

        # Infer the destination argument from the declarations if dest not given.
        if dest is not None:
            dest = _check_dest(dest)
        elif long_options:
            dest = _check_dest(long_options[0][2:])
        else:
            dest = _check_dest(short_options[0][1:])
        return dest, long_options, short_options

    def _store_0(self, args: Dict[str, Any]) -> None:
        raise InternalError()

    def _store_1(self, args: Dict[str, Any], value: str) -> None:
        result = self.type.convert_str(value)
        args[self.dest] = result

    def _store_default(self, args: Dict[str, Any]) -> None:
        result = self.type(self.default)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return 1


class Flag(Option):
    """The flag argument."""

    def __init__(
        self,
        *decls: str,
        dest: Optional[str] = None,
        required: bool = False,
        type: Optional[Type] = None,
        const: Any = True,
        default: Any = False,
        help: str = "",
    ) -> None:
        type = type or Type()
        super().__init__(*decls, dest=dest, required=required, type=type, default=default, help=help)
        self.const = const

    def _store_0(self, args: Dict[str, Any]) -> None:
        result = self.type(self.const)
        args[self.dest] = result

    def _store_1(self, args: Dict[str, Any], value: str) -> None:
        raise InternalError()

    @property
    def nargs(self) -> int:
        return 0


class SignalOption(Option):
    """The optional argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        # The signal option does not output the destination argument.
        return "", *_parse_decls(decls)


class SignalFlag(Flag):
    """The flag argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: Optional[str] = None) -> Tuple[str, List[str], List[str]]:
        # The signal flag does not output the destination argument.
        return "", *_parse_decls(decls)
