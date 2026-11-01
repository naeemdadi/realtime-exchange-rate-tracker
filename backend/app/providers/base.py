from typing import Any, Protocol

import httpx

from app.config import SUPPORTED_CURRENCIES
from app.models import Snapshot


class ProviderError(Exception):
    pass


class RateProvider(Protocol):
    async def fetch(self) -> Snapshot: ...


async def fetch_json(
    client: httpx.AsyncClient, url: str, timeout: float, params: dict[str, str] | None = None
) -> Any:
    try:
        response = await client.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderError(f"{url}: {exc!r}") from exc


def pick_supported(raw_rates: dict[str, Any]) -> dict[str, float]:
    rates = {code: float(raw_rates[code]) for code in SUPPORTED_CURRENCIES if code in raw_rates}
    rates["USD"] = 1.0
    return rates
