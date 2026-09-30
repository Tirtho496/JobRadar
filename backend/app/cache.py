import time
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if not item:
            return None
        expires, value = item
        if expires < time.monotonic():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        self._data.clear()


cache = TTLCache()
