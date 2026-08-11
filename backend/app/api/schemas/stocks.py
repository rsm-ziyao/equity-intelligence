"""Stock and price response schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StockPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    provider: str
    provider_timestamp: str
    retrieved_at: datetime


class StockResponse(BaseModel):
    symbol: str
    company_name: str | None
    latest_price: StockPriceResponse | None


class StockPricesMeta(BaseModel):
    symbol: str
    count: int
    limit: int
    start_date: date | None
    end_date: date | None


class StockPricesResponse(BaseModel):
    data: list[StockPriceResponse]
    meta: StockPricesMeta
