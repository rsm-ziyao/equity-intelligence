from datetime import datetime, timezone
from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, field_validator


class Freshness(StrEnum):
    REALTIME = "REALTIME"
    DELAYED = "DELAYED"
    LATEST_TRADING_DAY = "LATEST_TRADING_DAY"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class MarketStatus(StrEnum):
    PRE_MARKET = "PRE_MARKET"
    OPEN = "OPEN"
    POST_MARKET = "POST_MARKET"
    CLOSED = "CLOSED"
    HOLIDAY = "HOLIDAY"
    UNKNOWN = "UNKNOWN"


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", value):
        raise ValueError("Symbol must be 1-10 characters and contain only letters, numbers, dots, or hyphens")
    return value


class Quote(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    symbol: str
    price: float
    change: float
    change_percent: float
    provider: str
    provider_timestamp: datetime
    retrieved_at: datetime
    freshness: Freshness
    market_status: MarketStatus

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        return normalize_symbol(value)

    @field_validator("price")
    @classmethod
    def positive_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value


class QuoteResult(BaseModel):
    symbol: str
    quote: Quote | None = None
    error: str | None = None
    freshness: Freshness = Freshness.UNAVAILABLE


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
