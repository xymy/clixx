from __future__ import annotations

import os
import pathlib
import stat
from typing import Any

from .exceptions import DefinitionError, TypeConversionError


class Type:
    """The base class for all CLIXX type converters.

    This class also represents any type which does not apply type conversion.
    """

    def __call__(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.convert_str(value)
        return self.convert(value)

    def convert(self, value: Any) -> Any:
        """Convert non-string to expected value."""

        return value

    def convert_str(self, value: str) -> Any:
        """Convert string to expected value."""

        return value

    def check(self, value: Any) -> bool:
        """Check the constant/default value."""

        return True

    def suggest_metavar(self) -> str | None:
        """Suggest metavar for help information."""

        return None


class Str(Type):
    """The class used to convert command-line arguments to string."""

    def convert(self, value: Any) -> Any:
        raise TypeConversionError(f"{value!r} is not a valid string.")

    def convert_str(self, value: str) -> Any:
        return value

    def check(self, value: Any) -> bool:
        return isinstance(value, str)


class Bool(Type):
    """The class used to convert command-line arguments to boolean."""

    def convert(self, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        raise TypeConversionError(f"{value!r} is not a valid boolean.")

    def convert_str(self, value: str) -> Any:
        v = value.lower()
        if v in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if v in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise TypeConversionError(f"{value!r} is not a valid boolean.")

    def check(self, value: Any) -> bool:
        return isinstance(value, bool)


class Int(Type):
    """The class used to convert command-line arguments to integer.

    Parameters:
        base (int, default=10):
            The integer base used when parsing from string. Valid values are
            ``2 <= base <= 36`` or ``base == 0``.
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
        except ValueError:
            if self.base in {0, 10}:
                raise TypeConversionError(f"{value!r} is not a valid integer.")
            else:
                raise TypeConversionError(f"{value!r} is not a valid integer with base {self.base!r}.")

    def check(self, value: Any) -> bool:
        return isinstance(value, int)


class Float(Type):
    """The class used to convert command-line arguments to floating point
    number."""

    def convert(self, value: Any) -> Any:
        if isinstance(value, float):
            return value
        raise TypeConversionError(f"{value!r} is not a valid floating point number.")

    def convert_str(self, value: str) -> Any:
        try:
            return float(value)
        except ValueError:
            raise TypeConversionError(f"{value!r} is not a valid floating point number.")

    def check(self, value: Any) -> bool:
        return isinstance(value, float)


class File(Type):
    """The class used to convert command-line arguments to file.

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
    """

    def __init__(
        self,
        mode: str = "r",
        buffering: int = -1,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> None:
        self.mode = mode
        self.buffering = buffering
        self.encoding = encoding
        self.errors = errors
        self.newline = newline

    def convert(self, value: Any) -> Any:
        if hasattr(value, "read") or hasattr(value, "write"):
            return value
        raise TypeConversionError(f"{value!r} is not a valid file.")

    def convert_str(self, value: str) -> Any:
        try:
            return open(  # noqa
                value, self.mode, self.buffering, encoding=self.encoding, errors=self.errors, newline=self.newline
            )
        except OSError as e:
            raise TypeConversionError(f"{e.strerror}: {value!r}.")

    def check(self, value: Any) -> bool:
        return isinstance(value, str) or hasattr(value, "read") or hasattr(value, "write")


class Path(Type):
    """The class used to convert command-line arguments to path.

    Parameters:
        resolve (bool, default=False):
            If ``True``, make the path absolute, resolve all symlinks, and
            normalize it.
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
        raise TypeConversionError(f"{value!r} is not a valid path.")

    def convert_str(self, value: str) -> Any:
        return self._check_path(pathlib.Path(value))

    def _check_path(self, path: pathlib.Path) -> pathlib.Path:
        if self.resolve:
            path = path.resolve()

        try:
            st = path.stat()
        except OSError:
            if not self.exists:
                return path
            raise TypeConversionError(f"{str(path)!r} does not exist.")

        self._check_path_attr(path, st)
        if self.readable and not os.access(path, os.R_OK):
            raise TypeConversionError(f"{str(path)!r} is not readable.")
        if self.writable and not os.access(path, os.W_OK):
            raise TypeConversionError(f"{str(path)!r} is not writable.")
        if self.executable and not os.access(path, os.X_OK):
            raise TypeConversionError(f"{str(path)!r} is not executable.")
        return path

    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result) -> None:
        pass

    def check(self, value: Any) -> bool:
        return isinstance(value, (str, pathlib.Path))

    def suggest_metavar(self) -> str | None:
        return "<path>"


class DirPath(Path):
    """Similar to :class:`Path`, but check whether the path is a directory if it
    exists."""

    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result) -> None:
        if not stat.S_ISDIR(st.st_mode):
            raise TypeConversionError(f"{str(path)!r} is not a directory.")

    def suggest_metavar(self) -> str | None:
        return "<directory>"


class FilePath(Path):
    """Similar to :class:`Path`, but check whether the path is a file if it
    exists."""

    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result) -> None:
        if not stat.S_ISREG(st.st_mode):
            raise TypeConversionError(f"{str(path)!r} is not a file.")

    def suggest_metavar(self) -> str | None:
        return "<file>"
