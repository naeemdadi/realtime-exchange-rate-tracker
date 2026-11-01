from app.models import Snapshot
from app.providers.base import RateProvider


class PremiumProvider:
    """
    Stand-in for the paid vendor the brief says to assume exists.
    It serves real data from a wrapped provider and only relabels the source,
    so swapping in a real vendor means replacing this one class.
    """

    def __init__(self, upstream: RateProvider):
        self._upstream = upstream

    async def fetch(self) -> Snapshot:
        snapshot = await self._upstream.fetch()
        return snapshot.model_copy(update={"source": "premium"})
