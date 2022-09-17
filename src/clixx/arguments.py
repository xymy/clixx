from __future__ import annotations

from keyword import iskeyword
from typing import Any, Sequence

from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SHORT_PREFIX, SHORT_PREFIX_LEN
from .exceptions import DefinitionError, InternalError
from .types import Str, Type


def _check_dest(dest: str) -> str:
    dest = dest.replace("-", "_")
    if not dest.isidentifier():
        raise DefinitionError(f"{dest!r} is not a valid identifier.")
    if iskeyword(dest):
        raise DefinitionError(f"{dest!r} is a keyword.")
    return dest


def _parse_decls(decls: Sequence[str]) -> tuple[list[str], list[str]]:
    if not decls:
        raise DefinitionError("No option defined.")

    long_options: list[str] = []
    short_options: list[str] = []
    for decl in decls:
        if decl.startswith(LONG_PREFIX):
            decl_len = len(decl)
            if decl_len == LONG_PREFIX_LEN:
                raise DefinitionError(f"{decl!r} is not a valid long option.")
            if decl_len <= LONG_PREFIX_LEN + 1:
                raise DefinitionError(f"Long option {decl!r} is too short.")
            long_options.append(decl)
        elif decl.startswith(SHORT_PREFIX):
            decl_len = len(decl)
            if decl_len == SHORT_PREFIX_LEN:
                raise DefinitionError(f"{decl!r} is not a valid short option.")
            if decl_len >= SHORT_PREFIX_LEN + 2:
                raise DefinitionError(f"Short option {decl!r} is too long.")
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
        dest: str | None = None,
        nargs: int = 1,
        required: bool = False,
        type: Type | None = None,
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
    def _parse(decl: str, *, dest: str | None) -> tuple[str, str]:
        # Infer destination argument from declaration if `dest` not given.
        if dest is not None:
            dest = _check_dest(dest)
        else:
            dest = _check_dest(decl)
        return dest, decl

    def _store(self, args: dict[str, Any], value: str) -> None:
        result = self.type(value)
        if self.nargs == 1:
            args[self.dest] = result
        else:
            args.setdefault(self.dest, []).append(result)

    def _store_default(self, args: dict[str, Any]) -> None:
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

    @property
    def default(self) -> Any:
        return self._default

    @default.setter
    def default(self, value: Any) -> None:
        if value is not None and (nargs := self.nargs) > 1:
            if not isinstance(value, (tuple, list)):
                tn = type(value).__name__
                raise DefinitionError(f"If nargs > 1, the default value must be a tuple or list, not {tn}.")
            if (l := len(value)) != nargs:
                raise DefinitionError(f"If nargs > 1, the length of default value must be equal to {nargs!r}, got {l}.")
        self._default = value


class Option:
    """The optional argument."""

    def __init__(
        self,
        *decls: str,
        dest: str | None = None,
        required: bool = False,
        type: Type | None = None,
        default: Any = None,
        help: str = "",
    ) -> None:
        self.dest, self.long_options, self.short_options = self._parse(decls, dest=dest)
        self.required = required
        self.type = type or Str()
        self.default = default
        self.help = help

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        long_options, short_options = _parse_decls(decls)

        # Infer destination argument from declarations if `dest` not given.
        if dest is not None:
            dest = _check_dest(dest)
        elif long_options:
            dest = _check_dest(long_options[0][LONG_PREFIX_LEN:])
        else:
            dest = _check_dest(short_options[0][SHORT_PREFIX_LEN:])
        return dest, long_options, short_options

    def _store(self, args: dict[str, Any], value: str) -> None:
        result = self.type.convert_str(value)
        args[self.dest] = result

    def _store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def _store_default(self, args: dict[str, Any]) -> None:
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
        dest: str | None = None,
        type: Type | None = None,
        const: Any = True,
        default: Any = False,
        help: str = "",
    ) -> None:
        # The value of a flag is not parsed from command-line, so type conversion is unnecessary.
        type = type or Type()
        super().__init__(*decls, dest=dest, required=False, type=type, default=default, help=help)
        self.const = const

    def _store(self, args: dict[str, Any], value: str) -> None:
        raise InternalError()

    def _store_const(self, args: dict[str, Any]) -> None:
        result = self.type(self.const)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return 0


class SignalOption(Option):
    """The optional argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        # The signal option does not have destination argument.
        return "", *_parse_decls(decls)

    def _store(self, args: dict[str, Any], value: str) -> None:
        raise InternalError()

    def _store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def _store_default(self, args: dict[str, Any]) -> None:
        pass


class SignalFlag(Flag):
    """The flag argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        # The signal flag does not have destination argument.
        return "", *_parse_decls(decls)

    def _store(self, args: dict[str, Any], value: str) -> None:
        raise InternalError()

    def _store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def _store_default(self, args: dict[str, Any]) -> None:
        pass
