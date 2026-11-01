import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from app.budget import PremiumBudget
from app.config import Settings
from app.freshness import classify
from app.models import RatesResponse, Snapshot, Tier
from app.providers.base import ProviderError, RateProvider
from app.reconcile import reconcile
from app.store.base import Store

logger = logging.getLogger(__name__)

CACHE_KEY = "rates:USD"
REFERENCE_KEY = "rates:reference:USD"
REFRESH_LOCK_KEY = "lock:refresh:USD"


class NoRatesAvailable(Exception):
    pass


class RatesService:
    def __init__(
        self,
        store: Store,
        coinbase: RateProvider,
        open_er_api: RateProvider,
        premium: RateProvider,
        settings: Settings,
        now: Callable[[], datetime],
    ):
        self._store = store
        self._coinbase = coinbase
        self._open_er_api = open_er_api
        self._premium = premium
        self._settings = settings
        self._now = now
        self._budget = PremiumBudget(store, now)
        self._paid_inflight: asyncio.Task[Snapshot | None] | None = None

    async def get_rates(self, base: str, tier: Tier, verify: bool = False) -> RatesResponse:
        cached = await self._read(CACHE_KEY)
        verified = False
        if tier == "paid":
            snapshot = await self._serve_paid(cached)
        else:
            snapshot = await self._serve_free(cached)
            if verify and snapshot is not None:
                premium = await self._verify(snapshot)
                if premium is not None:
                    snapshot, verified = premium, True
        if snapshot is None or base not in snapshot.rates:
            raise NoRatesAvailable
        return self._respond(snapshot, base, tier, verified)

    async def _serve_paid(self, cached: Snapshot | None) -> Snapshot | None:
        if cached and self._age(cached) <= self._settings.paid_max_age:
            return cached
        # Concurrent paid requests on this instance share one premium call.
        if self._paid_inflight is None:
            self._paid_inflight = asyncio.create_task(self._fetch_premium_for_paid())
            self._paid_inflight.add_done_callback(self._clear_paid_inflight)
        fresh = await asyncio.shield(self._paid_inflight)
        return fresh or cached

    def _clear_paid_inflight(self, _: asyncio.Task) -> None:
        self._paid_inflight = None

    async def _fetch_premium_for_paid(self) -> Snapshot | None:
        await self._budget.record("paid")
        return await self._fetch_premium()

    async def _serve_free(self, cached: Snapshot | None) -> Snapshot | None:
        if cached and self._age(cached) <= self._settings.free_max_age:
            return cached
        # Only the request that wins the lock refreshes; the rest get the cache immediately.
        # A cold cache has nothing to serve, so it refreshes regardless.
        won_lock = await self._store.set(
            REFRESH_LOCK_KEY, "1", px=self._settings.refresh_lock_ms, nx=True
        )
        if not won_lock and cached is not None:
            return cached
        try:
            refreshed = await self._refresh_from_free_sources()
        finally:
            if won_lock:
                await self._store.delete(REFRESH_LOCK_KEY)

        best = self._newest(refreshed, cached)
        if refreshed is not None and best is refreshed:
            await self._write(CACHE_KEY, refreshed)
        if best is None or self._age(best) > self._settings.free_premium_fallback_after:
            if await self._budget.try_spend("free-fallback", self._settings.free_fallback_cap):
                best = self._newest(await self._fetch_premium(), best)
        return best

    async def _refresh_from_free_sources(self) -> Snapshot | None:
        try:
            snapshot = await self._coinbase.fetch()
            return await self._reconciled(snapshot)
        except ProviderError:
            logger.warning("coinbase failed, trying open.er-api", exc_info=True)
        try:
            return await self._open_er_api.fetch()
        except ProviderError:
            logger.warning("open.er-api failed", exc_info=True)
        return None

    async def _reconciled(self, snapshot: Snapshot) -> Snapshot:
        reference = await self._read(REFERENCE_KEY)
        if reference is None:
            try:
                reference = await self._open_er_api.fetch()
                await self._write(REFERENCE_KEY, reference, px=self._settings.reference_ttl_ms)
            except ProviderError:
                logger.warning("reference unavailable, skipping reconciliation", exc_info=True)
                return snapshot
        rates = reconcile(snapshot.rates, reference.rates, self._settings.max_deviation)
        return snapshot.model_copy(update={"rates": rates})

    async def _verify(self, snapshot: Snapshot) -> Snapshot | None:
        if snapshot.source == "premium" and self._age(snapshot) <= self._settings.verify_reuse_age:
            return snapshot
        if not await self._budget.try_spend("free-verify", self._settings.free_verify_cap):
            return None
        return await self._fetch_premium()

    async def _fetch_premium(self) -> Snapshot | None:
        try:
            snapshot = await self._premium.fetch()
        except ProviderError:
            logger.warning("premium provider failed", exc_info=True)
            return None
        await self._write(CACHE_KEY, snapshot)
        return snapshot

    async def _read(self, key: str) -> Snapshot | None:
        raw = await self._store.get(key)
        return Snapshot.model_validate_json(raw) if raw else None

    async def _write(self, key: str, snapshot: Snapshot, px: int | None = None) -> None:
        await self._store.set(key, snapshot.model_dump_json(), px=px)

    def _age(self, snapshot: Snapshot) -> float:
        return max(0.0, (self._now() - snapshot.fetched_at).total_seconds())

    @staticmethod
    def _newest(*snapshots: Snapshot | None) -> Snapshot | None:
        present = [s for s in snapshots if s is not None]
        return max(present, key=lambda s: s.fetched_at, default=None)

    def _respond(self, snapshot: Snapshot, base: str, tier: Tier, verified: bool) -> RatesResponse:
        base_rate = snapshot.rates[base]
        age = self._age(snapshot)
        thresholds = (
            self._settings.paid_freshness if tier == "paid" else self._settings.free_freshness
        )
        return RatesResponse(
            base=base,
            rates={code: rate / base_rate for code, rate in snapshot.rates.items()},
            fetched_at=snapshot.fetched_at,
            age_seconds=int(age),
            source=snapshot.source,
            freshness=classify(age, thresholds),
            tier=tier,
            verified=verified,
        )
