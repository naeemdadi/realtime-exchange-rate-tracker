from collections.abc import Callable
from datetime import datetime

import httpx

from app.models import Snapshot
from app.providers.base import ProviderError, fetch_json, pick_supported


class CoinbaseProvider:
    def __init__(
        self, client: httpx.AsyncClient, url: str, timeout: float, now: Callable[[], datetime]
    ):
        self._client = client
        self._url = url
        self._timeout = timeout
        self._now = now

    async def fetch(self) -> Snapshot:
        body = await fetch_json(self._client, self._url, self._timeout, {"currency": "USD"})
        try:
            rates = pick_supported(body["data"]["rates"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"coinbase: unexpected payload {exc!r}") from exc
        # Coinbase sends no timestamp; its rates are near real-time, so fetch time is honest.
        return Snapshot(rates=rates, fetched_at=self._now(), source="coinbase")
