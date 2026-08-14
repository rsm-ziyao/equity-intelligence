"""FastAPI dependencies for API routes."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from ..database.connection import get_session
from ..services.stock_service import StockService
from ..quotes.service import QuoteService
from ..quotes.adapters.finnhub import FinnhubQuoteAdapter
from ..services.fundamentals_service import FundamentalsService
from ..services.financial_trend_service import FinancialTrendService

_quote_service: QuoteService | None = None


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()


def get_stock_service() -> StockService:
    return StockService()

def get_fundamentals_service() -> FundamentalsService:
    return FundamentalsService()

def get_financial_trend_service() -> FinancialTrendService:
    return FinancialTrendService()


def get_quote_service() -> QuoteService:
    global _quote_service
    if _quote_service is None:
        try:
            _quote_service = QuoteService(FinnhubQuoteAdapter())
        except Exception as exc:
            class UnavailableClient:
                def get_quote(self, symbol, error=exc):
                    raise error
            _quote_service = QuoteService(UnavailableClient())
    return _quote_service
