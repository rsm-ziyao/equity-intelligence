from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from ...quotes.models import Freshness, MarketStatus


class ValuationMarket(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    provider: str
    provider_timestamp: datetime
    retrieved_at: datetime
    freshness: Freshness
    market_status: MarketStatus


class ValuationFinancialBasis(BaseModel):
    type: Literal["ANNUAL"]
    fiscal_year: int
    label: str
    period_end: datetime
    provider: str
    retrieved_at: datetime
    diluted_eps: float


class ValuationMetric(BaseModel):
    value: float | None = None
    unit: Literal["x"] = "x"
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    numerator: str | None = None
    denominator: str | None = None
    reason: str | None = None


class ValuationMetrics(BaseModel):
    pe: ValuationMetric
    price_to_sales: ValuationMetric
    price_to_fcf: ValuationMetric


class ValuationProvenance(BaseModel):
    quote_provider: str
    financial_provider: str


class ValuationData(BaseModel):
    symbol: str
    market: ValuationMarket | None = None
    financial_basis: ValuationFinancialBasis | None = None
    metrics: ValuationMetrics
    provenance: ValuationProvenance


class ValuationMeta(BaseModel):
    available: bool
    available_metrics: list[str]
    unavailable_metrics: list[str]


class ValuationResponse(BaseModel):
    data: ValuationData | None
    meta: ValuationMeta
