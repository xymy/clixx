from __future__ import annotations

import datetime
import enum
import os
import pathlib
import stat
import sys
from contextlib import suppress
from typing import IO, Any, Callable, Sequence, Union, cast

from .exceptions import DefinitionError, TypeConversionError


def _force_decode(filename: Any) -> str:
    fname = cast(Union[str, bytes], os.fspath(filename))
    if isinstance(fname, str):
        return fname
    return fname.decode(sys.getfilesystemencoding(), "backslashreplace")


def _resolve_normcase(case_sensitive: bool) -> Callable[[str], str]:
    if case_sensitive:
        return str
    return str.casefold


class Type:
    """The base class for all CLIXX type converters.

    This class also represents *any* type which does not apply type conversion.
    """

    def __call__(self, value: Any) -> Any:
        """Convert to expected value."""

        if isinstance(value, str):
            return self.convert_str(value)
        return self.convert(value)

    def convert(self, value: Any) -> Any:
        """Convert non-string to expected value."""

        return value

    def convert_str(self, value: str) -> Any:
        """Convert string to expected value."""

        return value

    def safe_convert(self, value: Any) -> Any:
        """Safe convert to compatible value without side effect.

        This is used to verify and preprocess the *constant*/*default* values.
        """

        return self(value)

    def format(self, value: Any) -> str:
        """Format value to pretty string.

        The ``value`` must be compatible with this type, usually the return
        value of :meth:`~clixx.types.Type.safe_convert`.
        """

        return str(value)

    @property
    def metavar(self) -> str:
        """The metavar suitable for this type. Empty string means inavailable."""

        return ""


class Str(Type):
    """The class used to convert command-line arguments to string.

    Target type: :class:`str`.
    """

    def convert(self, value: Any) -> Any:
        raise TypeConversionError(f"{value!r} is not a valid string.")

    def convert_str(self, value: str) -> Any:
        return value


class Bool(Type):
    """The class used to convert command-line arguments to boolean.

    Target type: :class:`bool`.

    Note:
        When parsing from string, recognize the following values (case insensitive):

        - ``True``: ``"t"``, ``"true"``, ``"y"``, ``"yes"``, ``"on"``, ``"1"``.
        - ``False``: ``"f"``, ``"false"``, ``"n"``, ``"no"``, ``"off"``, ``"0"``.
    """

    def convert(self, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        raise TypeConversionError(f"{value!r} is not a valid boolean.")

    def convert_str(self, value: str) -> Any:
        value_norm = value.lower()
        if value_norm in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if value_norm in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise TypeConversionError(f"{value!r} is not a valid boolean.")

    def format(self, value: Any) -> str:
        assert isinstance(value, bool)
        return "true" if value else "false"

    @property
    def metavar(self) -> str:
        return "BOOLEAN"


class Int(Type):
    """The class used to convert command-line arguments to integer.

    Target type: :class:`int`.

    Parameters:
        base (int, default=10):
            The integer base used when parsing from string. Valid values are
            ``2 <= base <= 36`` or ``base == 0``.

    See Also:
        - https://docs.python.org/3/library/functions.html#int
    """

    def __init__(self, *, base: int = 10) -> None:
        if not (2 <= base <= 36 or base == 0):
            raise DefinitionError(f"Require 2 <= base <= 36 or base == 0, got {base!r}.")
        self.base = base

    def convert(self, value: Any) -> Any:
        if isinstance(value, int):
            return value
        raise TypeConversionError(f"{value!r} is not a valid integer.")

    def convert_str(self, value: str) -> Any:
        try:
            return int(value, base=self.base)
        except ValueError as e:
            if self.base in {0, 10}:
                raise TypeConversionError(f"{value!r} is not a valid integer.") from e
            elif self.base == 16:
                raise TypeConversionError(f"{value!r} is not a valid hexadecimal integer.") from e
            elif self.base == 8:
                raise TypeConversionError(f"{value!r} is not a valid octal integer.") from e
            elif self.base == 2:
                raise TypeConversionError(f"{value!r} is not a valid binary integer.") from e
            else:
                raise TypeConversionError(f"{value!r} is not a valid integer with base {self.base!r}.") from e

    @property
    def metavar(self) -> str:
        return "INTEGER"


class Float(Type):
    """The class used to convert command-line arguments to floating point number.

    Target type: :class:`float`.

    See Also:
        - https://docs.python.org/3/library/functions.html#float
    """

    def convert(self, value: Any) -> Any:
        if isinstance(value, float):
            return value
        raise TypeConversionError(f"{value!r} is not a valid floating point number.")

    def convert_str(self, value: str) -> Any:
        try:
            return float(value)
        except ValueError as e:
            raise TypeConversionError(f"{value!r} is not a valid floating point number.") from e

    @property
    def metavar(self) -> str:
        return "FLOAT"


class Choice(Type):
    """The class used to convert command-line arguments to string in choices.

    Target type: :class:`str`.

    Parameters:
        choices (Sequence[str]):
            The allowed values.
        case_sensitive (bool, default=True):
            If ``True``, the allowed values are case sensitive.
    """

    def __init__(self, choices: Sequence[str], *, case_sensitive: bool = True) -> None:
        if not choices:
            raise DefinitionError("No choice defined.")
        self.choices = list(choices)
        self.case_sensitive = case_sensitive

    def convert(self, value: Any) -> Any:
        choices_str = ", ".join(map(repr, self.choices))
        raise TypeConversionError(f"{value!r} is not one of {choices_str}.")

    def convert_str(self, value: str) -> Any:
        normcase = _resolve_normcase(self.case_sensitive)
        value_norm = normcase(value)
        for choice in self.choices:
            if value_norm == normcase(choice):
                return choice

        choices_str = ", ".join(map(repr, self.choices))
        raise TypeConversionError(f"{value!r} is not one of {choices_str}.")

    @property
    def metavar(self) -> str:
        return "[" + "|".join(self.choices) + "]"


class IntChoice(Type):
    """The class used to convert command-line arguments to integer in choices.

    Target type: :class:`int`.

    Parameters:
        choices (Sequence[int]):
            The allowed values.
    """

    def __init__(self, choices: Sequence[int]) -> None:
        if not choices:
            raise DefinitionError("No choice defined.")
        self.choices = list(choices)

    def convert(self, value: Any) -> Any:
        if isinstance(value, int):
            return self._check(value)
        choices_str = ", ".join(map(repr, self.choices))
        raise TypeConversionError(f"{value!r} is not one of {choices_str}.")

    def convert_str(self, value: str) -> Any:
        return self._check(cast(int, Int().convert_str(value)))

    def _check(self, value: int) -> int:
        for choice in self.choices:
            if value == choice:
                return choice

        choices_str = ", ".join(map(repr, self.choices))
        raise TypeConversionError(f"{value!r} is not one of {choices_str}.")

    @property
    def metavar(self) -> str:
        return "[" + "|".join(map(str, self.choices)) + "]"


class Enum(Type):
    """The class used to convert command-line arguments to enumeration.

    Target type: :class:`enum.Enum`.

    Parameters:
        choices (type[enum.Enum]):
            The enumeration type.
        case_sensitive (bool, default=True):
            If ``True``, the enumeration names are case sensitive.
    """

    def __init__(self, enum_type: type[enum.Enum], *, case_sensitive: bool = True) -> None:
        if len(enum_type) == 0:
            raise DefinitionError("No enumeration member defined.")
        self.enum_type = enum_type
        self.case_sensitive = case_sensitive

    def convert(self, value: Any) -> Any:
        if isinstance(value, self.enum_type):
            return value
        raise TypeConversionError(f"{value!r} is not a valid enumeration member of {self.enum_type!r}.")

    def convert_str(self, value: str) -> Any:
        normcase = _resolve_normcase(self.case_sensitive)
        value_norm = normcase(value)
        for name, member in self.enum_type.__members__.items():
            if value_norm == normcase(name):
                return member

        enum_str = ", ".join(map(repr, self.enum_type.__members__))
        raise TypeConversionError(f"{value!r} is not one of {enum_str}.")

    def format(self, value: Any) -> str:
        assert isinstance(value, self.enum_type)
        return value.name

    @property
    def metavar(self) -> str:
        return "[" + "|".join(self.enum_type.__members__) + "]"


class IntEnum(Type):
    """The class used to convert command-line arguments to integer enumeration.

    Target type: :class:`enum.IntEnum`.

    Parameters:
        choices (type[enum.IntEnum]):
            The enumeration type.
    """

    def __init__(self, enum_type: type[enum.IntEnum]) -> None:
        if len(enum_type) == 0:
            raise DefinitionError("No enumeration member defined.")
        self.enum_type = enum_type

    def convert(self, value: Any) -> Any:
        if isinstance(value, self.enum_type):
            return value
        if isinstance(value, int):
            return self._check(value)
        raise TypeConversionError(f"{value!r} is not a valid enumeration member of {self.enum_type!r}.")

    def convert_str(self, value: str) -> Any:
        return self._check(cast(int, Int().convert_str(value)))

    def _check(self, value: int) -> enum.IntEnum:
        for member in self.enum_type:
            if value == member:
                return member

        enum_str = ", ".join(repr(m.value) for m in self.enum_type)
        raise TypeConversionError(f"{value!r} is not one of {enum_str}.")

    def format(self, value: Any) -> str:
        assert isinstance(value, self.enum_type)
        return str(value.value)

    @property
    def metavar(self) -> str:
        return "[" + "|".join(str(m.value) for m in self.enum_type) + "]"


class DateTime(Type):
    """The class used to convert command-line arguments to datetime.

    Target type: :class:`datetime.datetime`.

    Parameters:
        formats (Sequence[str] | None, default=None):
            The datetime formats used when parsing from string. If ``None``, use
            ``["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]``.

    See Also:
        - https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
    """

    def __init__(self, formats: Sequence[str] | None = None) -> None:
        if formats is None:
            self.formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
        else:
            if not formats:
                raise DefinitionError("No format defined.")
            self.formats = list(formats)

    def convert(self, value: Any) -> Any:
        if isinstance(value, datetime.datetime):
            return value
        raise TypeConversionError(f"{value!r} is not a valid datetime.")

    def convert_str(self, value: str) -> Any:
        for format in self.formats:
            with suppress(ValueError):
                return datetime.datetime.strptime(value, format)

        formats_str = ", ".join(map(repr, self.formats))
        if len(self.formats) == 1:
            hint = f"Valid format is {formats_str}."
        else:
            hint = f"Valid formats are {formats_str}."
        raise TypeConversionError(f"{value!r} is not a valid datetime. {hint}")

    @property
    def metavar(self) -> str:
        return "DATETIME"


class File(Type):
    """The class used to convert command-line arguments to file.

    Target type: :class:`typing.IO`.

    Parameters:
        mode (str, default='r'):
            The same as :func:`open`.
        buffering (int, default=-1):
            The same as :func:`open`.
        encoding (str | None, default=None):
            The same as :func:`open`.
        errors (str | None, default=None):
            The same as :func:`open`.
        newline (str | None, default=None):
            The same as :func:`open`.
        dash (bool, default=True):
            If ``True``, recognize dash (-) as stdin/stdout.

    Important:
        CLIXX will not close the file automatically when the command is
        finished. It's user's responsibility to close the file.

    Warning:
        The dash will be recognized only if ``value`` is a string. That means
        ``pathlib.Path("-")`` will never be recognized as stdin/stdout.

    See Also:
        - https://docs.python.org/3/library/functions.html#open
    """

    def __init__(
        self,
        mode: str = "r",
        buffering: int = -1,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        dash: bool = True,
    ) -> None:
        self.mode = mode
        self.buffering = buffering
        self.encoding = encoding
        self.errors = errors
        self.newline = newline
        self.dash = dash

    def convert(self, value: Any) -> Any:
        if hasattr(value, "read") or hasattr(value, "write"):
            return value
        if isinstance(value, (bytes, pathlib.Path)):
            return self._open(value)
        raise TypeConversionError(f"{value!r} is not a valid file.")

    def convert_str(self, value: str) -> Any:
        if self.dash and value == "-":
            if "r" in self.mode:
                return sys.stdin.buffer if "b" in self.mode else sys.stdin
            else:
                return sys.stdout.buffer if "b" in self.mode else sys.stdout
        return self._open(value)

    def _open(self, path: str | bytes | pathlib.Path) -> IO:
        try:
            return open(  # noqa
                path, self.mode, self.buffering, encoding=self.encoding, errors=self.errors, newline=self.newline
            )
        except OSError as e:
            raise TypeConversionError(f"Can not open {str(path)!r}. {e.strerror}.") from e

    def safe_convert(self, value: Any) -> Any:
        if isinstance(value, (str, bytes, pathlib.Path)) or hasattr(value, "read") or hasattr(value, "write"):
            return value
        raise TypeConversionError(f"{value!r} is not a valid file.")

    def format(self, value: Any) -> str:
        # These types can be decoded anyway.
        if isinstance(value, (str, bytes, pathlib.Path)):
            return _force_decode(value)
        # The file object may know its filename.
        with suppress(AttributeError, TypeError):
            return _force_decode(value.name)
        # This file does not have a pretty string representation. Just return a rough string.
        return str(value)

    @property
    def metavar(self) -> str:
        return "FILE"


class Path(Type):
    """The class used to convert command-line arguments to path.

    Target type: :class:`pathlib.Path`.

    Parameters:
        resolve (bool, default=False):
            If ``True``, resolve the path via :meth:`pathlib.Path.resolve`.
        exists (bool, default=False):
            If ``True``, check whether the path exists.
        readable (bool, default=False):
            If ``True``, check whether the path is readable.
        writable (bool, default=False):
            If ``True``, check whether the path is writable.
        executable (bool, default=False):
            If ``True``, check whether the path is executable.
    """

    def __init__(
        self,
        *,
        resolve: bool = False,
        exists: bool = False,
        readable: bool = False,
        writable: bool = False,
        executable: bool = False,
    ) -> None:
        self.resolve = resolve
        self.exists = exists
        self.readable = readable
        self.writable = writable
        self.executable = executable

    def convert(self, value: Any) -> Any:
        if isinstance(value, pathlib.Path):
            return self._check_path(value)
        if isinstance(value, bytes):
            try:
                return self.convert_str(os.fsdecode(value))
            except Exception as e:
                raise TypeConversionError(f"{value!r} is not a valid path.") from e
        raise TypeConversionError(f"{value!r} is not a valid path.")

    def convert_str(self, value: str) -> Any:
        return self._check_path(pathlib.Path(value))

    def _check_path(self, path: pathlib.Path) -> pathlib.Path:
        if self.resolve:
            path = path.resolve()

        try:
            st = path.stat()
        except OSError as e:
            if not self.exists:
                return path
            raise TypeConversionError(f"{str(path)!r} does not exist.") from e

        self._check_path_stat(path, st)
        if self.readable and not os.access(path, os.R_OK):
            raise TypeConversionError(f"{str(path)!r} is not readable.")
        if self.writable and not os.access(path, os.W_OK):
            raise TypeConversionError(f"{str(path)!r} is not writable.")
        if self.executable and not os.access(path, os.X_OK):
            raise TypeConversionError(f"{str(path)!r} is not executable.")
        return path

    @staticmethod
    def _check_path_stat(path: pathlib.Path, st: os.stat_result) -> None:
        pass

    def safe_convert(self, value: Any) -> Any:
        if isinstance(value, (str, bytes, pathlib.Path)):
            return value
        raise TypeConversionError(f"{value!r} is not a valid path.")

    def format(self, value: Any) -> str:
        return _force_decode(value)

    @property
    def metavar(self) -> str:
        return "PATH"


class DirPath(Path):
    """Similar to :class:`clixx.types.Path`, but check whether the path is a
    directory if it exists."""

    @staticmethod
    def _check_path_stat(path: pathlib.Path, st: os.stat_result) -> None:
        if not stat.S_ISDIR(st.st_mode):
            raise TypeConversionError(f"{str(path)!r} is not a directory.")

    @property
    def metavar(self) -> str:
        return "DIRECTORY"


class FilePath(Path):
    """Similar to :class:`clixx.types.Path`, but check whether the path is a
    file if it exists."""

    @staticmethod
    def _check_path_stat(path: pathlib.Path, st: os.stat_result) -> None:
        if not stat.S_ISREG(st.st_mode):
            raise TypeConversionError(f"{str(path)!r} is not a file.")

    @property
    def metavar(self) -> str:
        return "FILE"


def resolve_type(type: Type | type) -> Type:
    """Convert Python's builtin type to CLIXX's type. Return as is if ``type``
    is already an instance of :class:`clixx.types.Type`.

    +----------------+------------------------------+
    | Source         | Target                       |
    +================+==============================+
    | :class:`str`   | :class:`clixx.types.Str()`   |
    +----------------+------------------------------+
    | :class:`bool`  | :class:`clixx.types.Bool()`  |
    +----------------+------------------------------+
    | :class:`int`   | :class:`clixx.types.Int()`   |
    +----------------+------------------------------+
    | :class:`float` | :class:`clixx.types.Float()` |
    +----------------+------------------------------+
    """

    if isinstance(type, Type):
        return type
    if type is str:
        return Str()
    if type is bool:
        return Bool()
    if type is int:
        return Int()
    if type is float:
        return Float()
    raise DefinitionError(f"{type!r} is not a valid type.")
