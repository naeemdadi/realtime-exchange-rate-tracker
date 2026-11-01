import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from app.config import Settings
from app.main import build_service
from app.rates_service import RatesService
from app.store.memory_store import MemoryStore

COINBASE_URL = "https://api.coinbase.com/v2/exchange-rates"
OPEN_ER_API_URL = "https://open.er-api.com/v6/latest/USD"


class FakeClock:
    def __init__(self):
        self.current = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)


def coinbase_body(eur: float = 0.9, jpy: float = 150.0) -> dict:
    rates = {"EUR": str(eur), "JPY": str(jpy), "BTC": "0.00001"}
    return {"data": {"currency": "USD", "rates": rates}}


def open_er_api_body(updated_at: datetime) -> dict:
    return {
        "result": "success",
        "time_last_update_unix": int(updated_at.timestamp()),
        "rates": {"USD": 1, "EUR": 0.9, "JPY": 150.0},
    }


def make_service(clock: FakeClock, client: httpx.AsyncClient, **overrides) -> RatesService:
    return build_service(replace(Settings(), **overrides), client, MemoryStore(), clock.now)


@respx.mock
async def test_free_user_always_gets_honest_rates_as_sources_fail_and_recover():
    clock = FakeClock()
    async with httpx.AsyncClient() as client:
        service = make_service(clock, client)
        coinbase = respx.get(COINBASE_URL).mock(return_value=httpx.Response(500))
        three_hours_ago = clock.now() - timedelta(hours=3)
        open_er_api = respx.get(OPEN_ER_API_URL).mock(
            return_value=httpx.Response(200, json=open_er_api_body(three_hours_ago))
        )

        # Coinbase down on a cold cache: daily fallback data is shown with its real age.
        response = await service.get_rates("USD", "free")
        assert (response.source, response.freshness) == ("open-er-api", "very_stale")
        assert response.age_seconds == 3 * 60 * 60

        # Coinbase recovers; a bogus JPY rate is replaced by the daily reference.
        coinbase.mock(return_value=httpx.Response(200, json=coinbase_body(eur=0.91, jpy=1.0)))
        clock.advance(61)
        response = await service.get_rates("EUR", "free")
        assert (response.source, response.freshness) == ("coinbase", "fresh")
        assert response.rates["USD"] == pytest.approx(1 / 0.91)
        assert response.rates["JPY"] == pytest.approx(150.0 / 0.91)
        assert "BTC" not in response.rates

        # Within the free window the cache is served without touching upstream.
        upstream_calls = coinbase.call_count + open_er_api.call_count
        clock.advance(30)
        assert (await service.get_rates("USD", "free")).age_seconds == 30
        assert coinbase.call_count + open_er_api.call_count == upstream_calls

        # Everything down: last good rates keep flowing, labelled by age, never an error.
        coinbase.mock(return_value=httpx.Response(500))
        open_er_api.mock(side_effect=httpx.ConnectError("down"))
        clock.advance(31)
        response = await service.get_rates("USD", "free")
        assert (response.source, response.freshness, response.age_seconds) == (
            "coinbase",
            "stale",
            61,
        )
        clock.advance(600)
        assert (await service.get_rates("USD", "free")).freshness == "very_stale"


@respx.mock
async def test_paid_users_get_rates_under_two_seconds_old_sharing_one_premium_call():
    clock = FakeClock()
    async with httpx.AsyncClient() as client:
        service = make_service(clock, client)
        coinbase = respx.get(COINBASE_URL).mock(
            return_value=httpx.Response(200, json=coinbase_body())
        )

        first = await service.get_rates("USD", "paid")
        assert (first.source, first.age_seconds, first.freshness) == ("premium", 0, "fresh")
        assert coinbase.call_count == 1

        clock.advance(1)
        assert (await service.get_rates("USD", "paid")).age_seconds == 1
        assert coinbase.call_count == 1

        clock.advance(2)
        responses = await asyncio.gather(*(service.get_rates("USD", "paid") for _ in range(5)))
        assert coinbase.call_count == 2
        assert {r.age_seconds for r in responses} == {0}

        # Free users read the same shared cache, so they benefit from paid refreshes.
        free = await service.get_rates("USD", "free")
        assert (free.source, free.age_seconds) == ("premium", 0)

        # Premium outage: paid users keep the last snapshot, marked stale as it ages.
        coinbase.mock(return_value=httpx.Response(503))
        clock.advance(10)
        degraded = await service.get_rates("USD", "paid")
        assert (degraded.source, degraded.age_seconds, degraded.freshness) == (
            "premium",
            10,
            "stale",
        )


@respx.mock
async def test_free_verify_spends_premium_budget_until_the_daily_cap():
    clock = FakeClock()
    async with httpx.AsyncClient() as client:
        service = make_service(clock, client, free_verify_cap=2)
        respx.get(OPEN_ER_API_URL).mock(
            return_value=httpx.Response(200, json=open_er_api_body(clock.now()))
        )
        coinbase = respx.get(COINBASE_URL).mock(
            return_value=httpx.Response(200, json=coinbase_body())
        )

        first = await service.get_rates("USD", "free", verify=True)
        assert (first.verified, first.source) == (True, "premium")
        calls_after_first_verify = coinbase.call_count

        # A recent premium snapshot is reused instead of spending again.
        clock.advance(5)
        assert (await service.get_rates("USD", "free", verify=True)).verified is True
        assert coinbase.call_count == calls_after_first_verify

        clock.advance(20)
        assert (await service.get_rates("USD", "free", verify=True)).verified is True
        assert coinbase.call_count == calls_after_first_verify + 1

        # Cap reached: the user still gets rates, unverified, and no premium call is made.
        clock.advance(20)
        capped = await service.get_rates("USD", "free", verify=True)
        assert capped.verified is False
        assert coinbase.call_count == calls_after_first_verify + 1

        # The counter resets with the UTC day.
        clock.advance(24 * 60 * 60)
        assert (await service.get_rates("USD", "free", verify=True)).verified is True
