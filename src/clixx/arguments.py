from __future__ import annotations

from contextlib import contextmanager
from keyword import iskeyword
from typing import Any, Generator, Sequence

from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SHORT_PREFIX, SHORT_PREFIX_LEN
from .exceptions import DefinitionError, InternalError, InvalidValue, TypeConversionError
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


@contextmanager
def _raise_invalid_value(*, key: str) -> Generator[None, None, None]:
    try:
        yield None
    except TypeConversionError as e:
        raise InvalidValue(str(e), key=key)


class Argument:
    """The positional argument.

    Parameters:
        decl (str):
            The declaration for this argument.
        dest (str | None, default=None):
            The destination used to store/forward the argument value.
        nargs (int, default=1):
            The number of argument values. Valid values are ``nargs == 1`` or
            ``nargs == -1``.
        required (bool, default=False):
            Whether this argument is required or optional.
        type (Type | None, default=None):
            The type converter. If ``None``, use ``Str()``.
        default (Any, default=None):
            The default value used if argument omitted.
        metavar (str | None, default=None):
            The argument value name used in usage.
        help (str, default=''):
            The help information.
    """

    def __init__(
        self,
        decl: str,
        *,
        dest: str | None = None,
        nargs: int = 1,
        required: bool = False,
        type: Type | None = None,
        default: Any = None,
        metavar: str | None = None,
        help: str = "",
    ) -> None:
        self.dest, self.argument = self._parse(decl, dest=dest)
        self.nargs = nargs
        self.required = required
        self.type = type or Str()
        self.default = default
        self.metavar = metavar
        self.help = help

    @staticmethod
    def _parse(decl: str, *, dest: str | None) -> tuple[str, str]:
        # Infer destination argument from declaration if `dest` not given.
        if dest is not None:
            dest = _check_dest(dest)
        else:
            dest = _check_dest(decl)
        return dest, decl

    def store(self, args: dict[str, Any], value: str) -> None:
        with _raise_invalid_value(key=self.argument):
            result = self.type.convert_str(value)
        if self.nargs == 1:
            args[self.dest] = result
        else:
            # Variadic arguments are stored as tuple.
            args[self.dest] = args.get(self.dest, ()) + (result,)

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(key=self.dest):
            if self.nargs == 1:
                result = None if self.default is None else self.type(self.default)
            else:
                # Variadic arguments are stored as tuple. The default is a empty tuple.
                if self.default is None:
                    result = ()
                elif isinstance(self.default, (tuple, list)):
                    result = tuple(self.type(value) for value in self.default)
                else:
                    result = (self.type(self.default),)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return self._nargs

    @nargs.setter
    def nargs(self, value: int) -> None:
        if not (value == 1 or value == -1):
            raise DefinitionError(f"Require nargs == 1 or nargs == -1, got {value!r}.")
        self._nargs = value

    @property
    def default(self) -> Any:
        return self._default  # type: ignore

    @default.setter
    def default(self, value: Any) -> None:
        if value is not None and not self.type.check(value):
            raise DefinitionError(f"Invalid default value {value!r}.")
        self._default = value


class Option:
    """The optional argument.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store/forward the option value.
        required (bool, default=False):
            Whether this option is required or optional.
        type (Type | None, default=None):
            The type converter. If ``None``, use ``Str()``.
        default (Any, default=None):
            The default value used if option omitted.
        metavar (str | None, default=None):
            The option value name used in usage.
        help (str, default=''):
            The help information.
    """

    def __init__(
        self,
        *decls: str,
        dest: str | None = None,
        required: bool = False,
        type: Type | None = None,
        default: Any = None,
        metavar: str | None = None,
        help: str = "",
    ) -> None:
        self.dest, self.long_options, self.short_options = self._parse(decls, dest=dest)
        self.required = required
        self.type = type or Str()
        self.default = default
        self.metavar = metavar
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

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        with _raise_invalid_value(key=key):
            result = self.type.convert_str(value)
        args[self.dest] = result

    def store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def store_default(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(key=self.dest):
            result = None if self.default is None else self.type(self.default)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return 1

    @property
    def default(self) -> Any:
        return self._default

    @default.setter
    def default(self, value: Any) -> None:
        if value is not None and not self.type.check(value):
            raise DefinitionError(f"Invalid default value {value!r}.")
        self._default = value


class Flag(Option):
    """The flag argument.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this flag.
        dest (str | None, default=None):
            The destination used to store/forward the flag value.
        type (Type | None, default=None):
            The type converter. If ``None``, use ``Type()``.
        const (Any, default=None):
            The constant value used if flag occurred.
        default (Any, default=None):
            The default value used if flag omitted.
        help (str, default=''):
            The help information.
    """

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

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        raise InternalError()

    def store_const(self, args: dict[str, Any]) -> None:
        with _raise_invalid_value(key=self.dest):
            result = None if self.const is None else self.type(self.const)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        return 0

    @property
    def const(self) -> Any:
        return self._const

    @const.setter
    def const(self, value: Any) -> None:
        if value is not None and not self.type.check(value):
            raise DefinitionError(f"Invalid constant value {value!r}.")
        self._const = value


class SignalOption(Option):
    """The optional argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        # The signal option does not have destination argument.
        return "", *_parse_decls(decls)

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        raise InternalError()

    def store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def store_default(self, args: dict[str, Any]) -> None:
        pass


class SignalFlag(Flag):
    """The flag argument that can raise a signal."""

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        # The signal flag does not have destination argument.
        return "", *_parse_decls(decls)

    def store(self, args: dict[str, Any], value: str, *, key: str) -> None:
        raise InternalError()

    def store_const(self, args: dict[str, Any]) -> None:
        raise InternalError()

    def store_default(self, args: dict[str, Any]) -> None:
        pass
