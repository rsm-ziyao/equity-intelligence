from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_db_session, get_valuation_service
from app.main import app
from app.quotes.models import Freshness, MarketStatus, Quote, QuoteResult
from app.repositories.stock_repository import StockRepository
from app.services.valuation_service import ValuationService
from test_fundamentals import persist_period


class FakeQuoteService:
    def __init__(self, quote):
        self.quote = quote

    def get_quote(self, symbol):
        return QuoteResult(symbol=symbol, quote=self.quote)


def quote(freshness=Freshness.DELAYED):
    now = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    return Quote(symbol="AAPL", price=303.25, change=1, change_percent=0.3, provider="finnhub", provider_timestamp=now, retrieved_at=now, freshness=freshness, market_status=MarketStatus.CLOSED)


@pytest.fixture
def api_client(test_db_session):
    def override_db_session():
        yield test_db_session

    app.dependency_overrides[get_db_session] = override_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_service(service):
    app.dependency_overrides[get_valuation_service] = lambda: service


def test_valuation_endpoint_contract_and_normalization(api_client, test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AAPL")
    persist_period(test_db_session, "AAPL", "annual", 2025, eps="10.67")
    use_service(ValuationService(FakeQuoteService(quote())))
    response = api_client.get("/api/v1/stocks/aapl/valuation")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["symbol"] == "AAPL"
    assert body["data"]["metrics"]["pe"]["value"] == 28.42
    assert body["data"]["financial_basis"]["type"] == "ANNUAL"
    assert body["data"]["market"]["freshness"] == "DELAYED"
    assert body["data"]["metrics"]["price_to_sales"]["reason"] == "SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE"


def test_valuation_unknown_stock_returns_404(api_client):
    use_service(ValuationService(FakeQuoteService(quote())))
    assert api_client.get("/api/v1/stocks/UNKNOWN/valuation").status_code == 404


def test_valuation_quote_failure_and_negative_eps(api_client, test_db_session):
    StockRepository.get_or_create(test_db_session, "AAPL")
    persist_period(test_db_session, "AAPL", "annual", 2025, eps="-1")
    use_service(ValuationService(FakeQuoteService(None)))
    unavailable = api_client.get("/api/v1/stocks/AAPL/valuation").json()
    assert unavailable["data"]["market"] is None
    assert unavailable["data"]["financial_basis"]["diluted_eps"] == -1.0
    assert unavailable["data"]["metrics"]["pe"]["reason"] == "MISSING_INPUT"

    use_service(ValuationService(FakeQuoteService(quote())))
    negative = api_client.get("/api/v1/stocks/AAPL/valuation").json()
    assert negative["data"]["metrics"]["pe"]["reason"] == "NEGATIVE_DENOMINATOR"


def test_valuation_stale_quote(api_client, test_db_session):
    StockRepository.get_or_create(test_db_session, "AAPL")
    persist_period(test_db_session, "AAPL", "annual", 2025, eps="10")
    use_service(ValuationService(FakeQuoteService(quote(Freshness.STALE))))
    body = api_client.get("/api/v1/stocks/AAPL/valuation").json()
    assert body["data"]["market"]["freshness"] == "STALE"
    assert body["data"]["metrics"]["pe"]["reason"] == "STALE_MARKET_PRICE"


def test_valuation_database_error(api_client, test_db_session, monkeypatch):
    StockRepository.get_or_create(test_db_session, "AAPL")
    from app.repositories import fundamentals_repository
    monkeypatch.setattr(fundamentals_repository.FundamentalsRepository, "get_all_annual_periods", lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("down")))
    use_service(ValuationService(FakeQuoteService(quote())))
    assert api_client.get("/api/v1/stocks/AAPL/valuation").status_code == 503
