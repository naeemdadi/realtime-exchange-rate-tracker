from datetime import UTC, datetime

import httpx

from app.models import Snapshot
from app.providers.base import ProviderError, fetch_json, pick_supported


class OpenErApiProvider:
    def __init__(self, client: httpx.AsyncClient, url: str, timeout: float):
        self._client = client
        self._url = url
        self._timeout = timeout

    async def fetch(self) -> Snapshot:
        body = await fetch_json(self._client, self._url, self._timeout)
        try:
            if body["result"] != "success":
                raise ValueError(body.get("error-type", "unknown error"))
            rates = pick_supported(body["rates"])
            # Stamp with the upstream publish time so daily data never looks fresh.
            updated_at = datetime.fromtimestamp(body["time_last_update_unix"], tz=UTC)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"open.er-api: unexpected payload {exc!r}") from exc
        return Snapshot(rates=rates, fetched_at=updated_at, source="open-er-api")
