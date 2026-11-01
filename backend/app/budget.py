import logging
from collections.abc import Callable
from datetime import datetime

from app.store.base import Store

logger = logging.getLogger(__name__)

COUNTER_TTL_SECONDS = 48 * 60 * 60


class PremiumBudget:
    """Daily (UTC) premium call counters. Spend is counted on attempt, not on success."""

    def __init__(self, store: Store, now: Callable[[], datetime]):
        self._store = store
        self._now = now

    def _key(self, bucket: str) -> str:
        return f"premium:{bucket}:{self._now().date().isoformat()}"

    async def try_spend(self, bucket: str, cap: int) -> bool:
        try:
            count = await self._store.incr(self._key(bucket), COUNTER_TTL_SECONDS)
        except Exception:
            logger.exception("budget counter unavailable, refusing premium spend")
            return False
        return count <= cap

    async def record(self, bucket: str) -> None:
        try:
            await self._store.incr(self._key(bucket), COUNTER_TTL_SECONDS)
        except Exception:
            logger.exception("could not record premium usage for %s", bucket)
