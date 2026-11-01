from typing import Protocol


class Store(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, px: int | None = None, nx: bool = False) -> bool:
        """Returns False when nx=True and the key already exists."""
        ...

    async def delete(self, key: str) -> None: ...

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Increments a counter, setting its expiry when the key is first created."""
        ...
