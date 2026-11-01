import time


class MemoryStore:
    """Per-process store for local dev, tests and as the fallback when Redis is down."""

    def __init__(self):
        self._values: dict[str, tuple[str, float | None]] = {}

    def _live(self, key: str) -> str | None:
        entry = self._values.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() >= expires_at:
            del self._values[key]
            return None
        return value

    async def get(self, key: str) -> str | None:
        return self._live(key)

    async def set(self, key: str, value: str, px: int | None = None, nx: bool = False) -> bool:
        if nx and self._live(key) is not None:
            return False
        expires_at = time.monotonic() + px / 1000 if px is not None else None
        self._values[key] = (value, expires_at)
        return True

    async def delete(self, key: str) -> None:
        self._values.pop(key, None)

    async def incr(self, key: str, expire_seconds: int) -> int:
        current = self._live(key)
        count = int(current) + 1 if current is not None else 1
        if current is None:
            self._values[key] = (str(count), time.monotonic() + expire_seconds)
        else:
            self._values[key] = (str(count), self._values[key][1])
        return count
