from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

Source = Literal["coinbase", "open-er-api", "premium"]
Tier = Literal["free", "paid"]
Freshness = Literal["fresh", "stale", "very_stale"]


class Snapshot(BaseModel):
    """USD-based rates plus when the upstream data was produced."""

    rates: dict[str, float]
    fetched_at: datetime
    source: Source


class RatesResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    base: str
    rates: dict[str, float]
    fetched_at: datetime
    age_seconds: int
    source: Source
    freshness: Freshness
    tier: Tier
    verified: bool
