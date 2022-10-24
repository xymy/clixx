from __future__ import annotations

from keyword import iskeyword
from typing import Any, Sequence, cast

from .constants import LONG_PREFIX, LONG_PREFIX_LEN, SHORT_PREFIX, SHORT_PREFIX_LEN
from .exceptions import DefinitionError, HelpSignal, TypeConversionError, VersionSignal
from .types import Int, Str, Type, _resolve_type


def _check_dest(dest: str) -> str:
    dest = dest.replace("-", "_")
    if not dest.isidentifier():
        raise DefinitionError(f"{dest!r} is not a valid identifier.")
    if iskeyword(dest):
        raise DefinitionError(f"{dest!r} is a keyword.")
    return dest


def _parse_decl(decl: str) -> str:
    if not decl:
        raise DefinitionError("Argument must be non-empty.")
    return decl


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
    """The argument, aka positional argument.

    Parameters:
        decl (str):
            The declaration for this argument.
        dest (str | None, default=None):
            The destination used to store/forward the argument value.
        nargs (int, default=1):
            The number of argument values. Valid values are ``nargs == 1`` or ``nargs == -1``.
        required (bool, default=False):
            Whether this argument is required or optional.
        type (Type | type | None, default=None):
            The type converter. If ``None``, use ``Str()``.
        default (Any, default=None):
            The default value used if argument omitted.
        hidden (bool, default=False):
            If ``True``, hide this argument from help information.
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
        type: Type | type | None = None,
        default: Any = None,
        hidden: bool = False,
        metavar: str | None = None,
        help: str = "",
    ) -> None:
        self.dest, self.argument = self._parse(decl, dest=dest)
        self.nargs = nargs
        self.required = required
        self.type = _resolve_type(type or Str())
        self.default = default
        self.hidden = hidden
        self.metavar = metavar
        self.help = help

    @staticmethod
    def _parse(decl: str, *, dest: str | None) -> tuple[str, str]:
        argument = _parse_decl(decl)

        # Infer destination from declaration if `dest` not given.
        if dest is not None:
            dest = _check_dest(dest) if dest else ""
        else:
            dest = _check_dest(argument)
        return dest, argument

    def store(self, args: dict[str, Any], value: str) -> None:
        """Store value to destination."""

        if not self.dest:
            return

        result = self.type.convert_str(value)
        if self.nargs == 1:
            args[self.dest] = result
        else:
            # Variadic arguments are stored as list.
            cast(list, args.setdefault(self.dest, [])).append(result)

    def store_default(self, args: dict[str, Any]) -> None:
        """Store default value to destination."""

        if not self.dest:
            return

        if self.nargs == 1:
            result = None if self.default is None else self.type(self.default)
        else:
            # Variadic arguments are stored as list. Defaults to empty list.
            if self.default is None:
                result = []
            else:
                result = [self.type(value) for value in cast(list, self.default)]
        args[self.dest] = result

    def show(self) -> str:
        """Show argument."""

        return repr(self.argument)

    def show_metavar(self) -> str:
        """Resolve and show metavar."""

        if self.metavar is not None:
            return self.metavar
        else:
            return self.dest.upper()

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
        return self._default

    @default.setter
    def default(self, value: Any) -> None:
        if value is not None:
            if self.nargs == 1:
                value = self._verify(value)
            else:
                if not isinstance(value, (list, tuple)):
                    raise DefinitionError("For nargs == -1, the default value must be list, tuple or None.")
                value = [self._verify(v) for v in value]
        self._default = value

    def _verify(self, value: Any) -> Any:
        try:
            return self.type.safe_convert(value)
        except TypeConversionError as e:
            raise DefinitionError(f"Invalid default value for argument {self.show()}. {str(e)}")


class Option:
    """The option, aka optional argument.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store/forward the option value.
        required (bool, default=False):
            Whether this option is required or optional.
        type (Type | type | None, default=None):
            The type converter. If ``None``, use ``Str()``.
        default (Any, default=None):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
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
        type: Type | type | None = None,
        default: Any = None,
        hidden: bool = False,
        metavar: str | None = None,
        help: str = "",
    ) -> None:
        self.dest, self.long_options, self.short_options = self._parse(decls, dest=dest)
        self.required = required
        self.type = _resolve_type(type or Str())
        self.default = default
        self.hidden = hidden
        self.metavar = metavar
        self.help = help

    @staticmethod
    def _parse(decls: Sequence[str], *, dest: str | None = None) -> tuple[str, list[str], list[str]]:
        long_options, short_options = _parse_decls(decls)

        # Infer destination from declarations if `dest` not given.
        if dest is not None:
            dest = _check_dest(dest) if dest else ""
        elif long_options:
            dest = _check_dest(long_options[0][LONG_PREFIX_LEN:])
        else:
            dest = _check_dest(short_options[0][SHORT_PREFIX_LEN:])
        return dest, long_options, short_options

    def store(self, args: dict[str, Any], value: str) -> None:
        """Store value to destination.

        Availability: ``nargs == 1``.
        """

        if not self.dest:
            return

        result = self.type.convert_str(value)
        args[self.dest] = result

    def store_const(self, args: dict[str, Any]) -> None:
        """Store constant value to destination.

        Availability: ``nargs == 0``.
        """

        raise NotImplementedError

    def store_default(self, args: dict[str, Any]) -> None:
        """Store default value to destination."""

        if not self.dest:
            return

        result = None if self.default is None else self.type(self.default)
        args[self.dest] = result

    def show(self) -> str:
        """Show short options and long options."""

        return " / ".join(map(repr, self.short_options + self.long_options))

    def show_metavar(self) -> str:
        """Resolve and show metavar."""

        if self.metavar is not None:
            return self.metavar
        elif (metavar := self.type.suggest_metavar()) is not None:
            return metavar
        else:
            return self.dest.upper()

    @property
    def nargs(self) -> int:
        """Return ``1``."""

        return 1

    @property
    def default(self) -> Any:
        return self._default

    @default.setter
    def default(self, value: Any) -> None:
        if value is not None:
            try:
                value = self.type.safe_convert(value)
            except TypeConversionError as e:
                raise DefinitionError(f"Invalid default value for option {self.show()}. {str(e)}")
        self._default = value


class FlagOption(Option):
    """The flag option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store/forward the option value.
        const (Any, default=True):
            The constant value used if option occurred.
        default (Any, default=False):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default=''):
            The help information.
    """

    def __init__(
        self,
        *decls: str,
        dest: str | None = None,
        const: Any = True,
        default: Any = False,
        hidden: bool = False,
        help: str = "",
    ) -> None:
        super().__init__(
            *decls, dest=dest, required=False, type=Type(), default=default, hidden=hidden, metavar="", help=help
        )
        self.const = const

    def store(self, args: dict[str, Any], value: str) -> None:
        raise NotImplementedError

    def store_const(self, args: dict[str, Any]) -> None:
        if not self.dest:
            return

        result = None if self.const is None else self.type(self.const)
        args[self.dest] = result

    @property
    def nargs(self) -> int:
        """Return ``0``."""

        return 0

    @property
    def const(self) -> Any:
        return self._const

    @const.setter
    def const(self, value: Any) -> None:
        if value is not None:
            try:
                value = self.type.safe_convert(value)
            except TypeConversionError as e:
                raise DefinitionError(f"Invalid constant value for option {self.show()}. {str(e)}")
        self._const = value


class CountOption(Option):
    """The count option.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        dest (str | None, default=None):
            The destination used to store/forward the option value.
        default (Any, default=0):
            The default value used if option omitted.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default=''):
            The help information.
    """

    def __init__(
        self, *decls: str, dest: str | None = None, default: Any = 0, hidden: bool = False, help: str = ""
    ) -> None:
        super().__init__(
            *decls, dest=dest, required=False, type=Int(), default=default, hidden=hidden, metavar="", help=help
        )

    def store(self, args: dict[str, Any], value: str) -> None:
        raise NotImplementedError

    def store_const(self, args: dict[str, Any]) -> None:
        if not self.dest:
            return

        args[self.dest] = args.get(self.dest, 0) + 1

    @property
    def nargs(self) -> int:
        """Return ``0``."""

        return 0


class SignalOption(Option):
    """The option that can raise a signal.

    Parameters:
        decls (tuple[str, ...]):
            The declarations for this option.
        hidden (bool, default=False):
            If ``True``, hide this option from help information.
        help (str, default=''):
            The help information.
    """

    def __init__(self, *decls: str, hidden: bool = False, help: str = "") -> None:
        super().__init__(
            *decls, dest="", required=False, type=Type(), default=None, hidden=hidden, metavar="", help=help
        )

    def store(self, args: dict[str, Any], value: str) -> None:
        raise NotImplementedError

    def store_const(self, args: dict[str, Any]) -> None:
        raise NotImplementedError

    def store_default(self, args: dict[str, Any]) -> None:
        pass  # do nothing

    @property
    def nargs(self) -> int:
        """Return ``0``."""

        return 0


class HelpOption(SignalOption):
    """The help option."""

    def __init__(self, *decls: str, hidden: bool = False, help: str = "Show help information and exit.") -> None:
        super().__init__(*decls, hidden=hidden, help=help)

    def store_const(self, args: dict[str, Any]) -> None:
        raise HelpSignal


class VersionOption(SignalOption):
    """The version option."""

    def __init__(self, *decls: str, hidden: bool = False, help: str = "Show version information and exit.") -> None:
        super().__init__(*decls, hidden=hidden, help=help)

    def store_const(self, args: dict[str, Any]) -> None:
        raise VersionSignal
