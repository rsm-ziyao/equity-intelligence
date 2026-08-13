from pydantic import BaseModel, Field

from ...quotes.models import Quote, QuoteResult


class QuoteMeta(BaseModel):
    symbol: str | None = None
    provider: str = "finnhub"
    requested_symbol_count: int = 1
    returned_symbol_count: int = 0
    failed_symbols: list[str] = Field(default_factory=list)


class QuoteResponse(BaseModel):
    data: Quote | None
    meta: QuoteMeta


class QuoteBatchResponse(BaseModel):
    data: list[QuoteResult]
    meta: QuoteMeta
