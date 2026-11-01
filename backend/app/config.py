import os
from dataclasses import dataclass, field

SUPPORTED_CURRENCIES = frozenset(
    "USD EUR GBP JPY INR AUD CAD CHF CNY HKD SGD AED SAR NZD SEK NOK DKK "
    "ZAR BRL MXN KRW TRY PLN THB IDR MYR PHP PKR BDT NGN EGP KES".split()
)


@dataclass(frozen=True)
class Settings:
    coinbase_url: str = "https://api.coinbase.com/v2/exchange-rates"
    open_er_api_url: str = "https://open.er-api.com/v6/latest/USD"
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])

    # Max snapshot age (seconds) each tier accepts before a refresh.
    free_max_age: float = 60
    paid_max_age: float = 2
    free_premium_fallback_after: float = 300
    verify_reuse_age: float = 15

    # (fresh_until, stale_until) in seconds; anything older is very_stale.
    free_freshness: tuple[float, float] = (60, 600)
    paid_freshness: tuple[float, float] = (5, 60)

    free_timeout: float = 2
    premium_timeout: float = 3
    refresh_lock_ms: int = 10_000
    reference_ttl_ms: int = 6 * 60 * 60 * 1000
    max_deviation: float = 0.02

    free_fallback_cap: int = 1500
    free_verify_cap: int = 3500


def load_settings() -> Settings:
    defaults = Settings()
    origins = os.getenv("ALLOWED_ORIGIN")
    return Settings(
        coinbase_url=os.getenv("COINBASE_URL", defaults.coinbase_url),
        open_er_api_url=os.getenv("OPEN_ER_API_URL", defaults.open_er_api_url),
        allowed_origins=origins.split(",") if origins else defaults.allowed_origins,
        free_fallback_cap=int(os.getenv("FREE_FALLBACK_CAP", defaults.free_fallback_cap)),
        free_verify_cap=int(os.getenv("FREE_VERIFY_CAP", defaults.free_verify_cap)),
    )
