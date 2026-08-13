"""Current market quote routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ...quotes.models import normalize_symbol
from ...quotes.service import QuoteService
from ..schemas.quotes import QuoteBatchResponse, QuoteMeta, QuoteResponse

router = APIRouter(prefix="/quotes", tags=["quotes"])


def get_quote_service() -> QuoteService:
    from ..dependencies import get_quote_service as dependency
    return dependency()


@router.get("/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str, service: QuoteService = Depends(get_quote_service)) -> QuoteResponse:
    try:
        normalized = normalize_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = service.get_quote(normalized)
    return QuoteResponse(data=result.quote, meta=QuoteMeta(symbol=normalized, returned_symbol_count=int(result.quote is not None), failed_symbols=[] if result.quote else [normalized]))


@router.get("", response_model=QuoteBatchResponse)
def get_quotes(symbols: Annotated[str, Query(min_length=1)] = "AAPL", service: QuoteService = Depends(get_quote_service)) -> QuoteBatchResponse:
    requested = [part for part in symbols.split(",") if part.strip()]
    results, failures = service.get_quotes(requested)
    try:
        unique_count = len(list(dict.fromkeys(normalize_symbol(s) for s in requested)))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return QuoteBatchResponse(data=results, meta=QuoteMeta(provider="finnhub", requested_symbol_count=unique_count, returned_symbol_count=sum(result.quote is not None for result in results), failed_symbols=failures))
