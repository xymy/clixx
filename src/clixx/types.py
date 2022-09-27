from __future__ import annotations

import os
import pathlib
import stat
from typing import Any

from .exceptions import DefinitionError, InvalidValue


class Type:
    def __call__(self, value: Any, *, key: str) -> Any:
        if isinstance(value, str):
            return self.convert_str(value, key=key)
        return self.convert(value, key=key)

    def convert(self, value: Any, *, key: str) -> Any:
        return value

    def convert_str(self, value: str, *, key: str) -> Any:
        return value

    def check(self, value: Any) -> bool:
        return True


class Str(Type):
    def convert(self, value: Any, *, key: str) -> Any:
        raise InvalidValue(f"{value!r} is not a valid string.", key=key)

    def convert_str(self, value: str, *, key: str) -> Any:
        return value

    def check(self, value: Any) -> bool:
        return isinstance(value, str)


class Bool(Type):
    def convert(self, value: Any, *, key: str) -> Any:
        if isinstance(value, bool):
            return value
        raise InvalidValue(f"{value!r} is not a valid boolean.", key=key)

    def convert_str(self, value: str, *, key: str) -> Any:
        v = value.lower()
        if v in {"t", "true", "y", "yes", "on", "1"}:
            return True
        if v in {"f", "false", "n", "no", "off", "0"}:
            return False
        raise InvalidValue(f"{value!r} is not a valid boolean.", key=key)

    def check(self, value: Any) -> bool:
        return isinstance(value, bool)


class Int(Type):
    def __init__(self, *, base: int = 10) -> None:
        if not (2 <= base <= 36 or base == 0):
            raise DefinitionError(f"Require 2 <= base <= 36 or base == 0, got {base!r}.")
        self.base = base

    def convert(self, value: Any, *, key: str) -> Any:
        if isinstance(value, int):
            return value
        raise InvalidValue(f"{value!r} is not a valid integer.", key=key)

    def convert_str(self, value: str, *, key: str) -> Any:
        try:
            return int(value, base=self.base)
        except ValueError:
            if self.base in {0, 10}:
                raise InvalidValue(f"{value!r} is not a valid integer.", key=key)
            else:
                raise InvalidValue(f"{value!r} is not a valid integer with base {self.base!r}.", key=key)

    def check(self, value: Any) -> bool:
        return isinstance(value, int)


class Float(Type):
    def convert(self, value: Any, *, key: str) -> Any:
        if isinstance(value, float):
            return value
        raise InvalidValue(f"{value!r} is not a valid floating point number.", key=key)

    def convert_str(self, value: str, *, key: str) -> Any:
        try:
            return float(value)
        except ValueError:
            raise InvalidValue(f"{value!r} is not a valid floating point number.", key=key)

    def check(self, value: Any) -> bool:
        return isinstance(value, float)


class Path(Type):
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

    def convert(self, value: Any, *, key: str) -> Any:
        if isinstance(value, pathlib.Path):
            return self._check_path(value, key=key)
        raise InvalidValue(f"{value!r} is not a valid path.", key=key)

    def convert_str(self, value: str, *, key: str) -> Any:
        return self._check_path(pathlib.Path(value), key=key)

    def _check_path(self, path: pathlib.Path, *, key: str) -> pathlib.Path:
        if self.resolve:
            path = path.resolve()

        try:
            st = path.stat()
        except OSError:
            if not self.exists:
                return path
            raise InvalidValue(f"{str(path)!r} does not exist.", key=key)

        self._check_path_attr(path, st, key=key)
        if self.readable and not os.access(path, os.R_OK):
            raise InvalidValue(f"{str(path)!r} is not readable.", key=key)
        if self.writable and not os.access(path, os.W_OK):
            raise InvalidValue(f"{str(path)!r} is not writable.", key=key)
        if self.executable and not os.access(path, os.X_OK):
            raise InvalidValue(f"{str(path)!r} is not executable.", key=key)
        return path

    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result, *, key: str) -> None:
        pass

    def check(self, value: Any) -> bool:
        return isinstance(value, (str, pathlib.Path))


class DirPath(Path):
    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result, *, key: str) -> None:
        if not stat.S_ISDIR(st.st_mode):
            raise InvalidValue(f"{str(path)!r} is not a directory.", key=key)


class FilePath(Path):
    @staticmethod
    def _check_path_attr(path: pathlib.Path, st: os.stat_result, *, key: str) -> None:
        if not stat.S_ISREG(st.st_mode):
            raise InvalidValue(f"{str(path)!r} is not a file.", key=key)
