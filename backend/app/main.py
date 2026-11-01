import logging
import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from upstash_redis.asyncio import Redis

from app.config import SUPPORTED_CURRENCIES, Settings, load_settings
from app.models import RatesResponse, Tier
from app.providers.coinbase import CoinbaseProvider
from app.providers.open_er_api import OpenErApiProvider
from app.providers.premium import PremiumProvider
from app.rates_service import NoRatesAvailable, RatesService
from app.store.base import Store
from app.store.memory_store import MemoryStore
from app.store.redis_store import FallbackStore, RedisStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = load_settings()


def utc_now() -> datetime:
    return datetime.now(UTC)


def build_store() -> tuple[Store, Redis | None]:
    if not os.getenv("UPSTASH_REDIS_REST_URL"):
        logger.info("UPSTASH_REDIS_REST_URL not set, using in-memory store")
        return MemoryStore(), None
    # No client retries: a slow Redis should fall back to memory, not stall the request.
    redis = Redis.from_env(allow_telemetry=False, rest_retries=0)
    return FallbackStore(RedisStore(redis), MemoryStore()), redis


def build_service(
    settings: Settings,
    client: httpx.AsyncClient,
    store: Store,
    now: Callable[[], datetime] = utc_now,
) -> RatesService:
    premium_upstream = CoinbaseProvider(client, settings.coinbase_url, settings.premium_timeout, now)
    return RatesService(
        store=store,
        coinbase=CoinbaseProvider(client, settings.coinbase_url, settings.free_timeout, now),
        open_er_api=OpenErApiProvider(client, settings.open_er_api_url, settings.free_timeout),
        premium=PremiumProvider(premium_upstream),
        settings=settings,
        now=now,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    store, redis = build_store()
    async with httpx.AsyncClient() as client:
        app.state.rates_service = build_service(settings, client, store)
        yield
    if redis is not None:
        await redis.close()


app = FastAPI(title="Exchange rate tracker", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["GET"])


@app.get("/api/rates", response_model=RatesResponse)
async def get_rates(
    request: Request,
    base: str = Query("USD", min_length=3, max_length=3),
    tier: Tier = "free",
    verify: bool = False,
) -> RatesResponse | JSONResponse:
    base = base.upper()
    if base not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported base currency: {base}")
    service: RatesService = request.app.state.rates_service
    try:
        return await service.get_rates(base, tier, verify)
    except NoRatesAvailable:
        return JSONResponse(
            status_code=503,
            content={"error": "No exchange rate source is reachable", "retryAfterSeconds": 30},
        )


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "Internal error"})
