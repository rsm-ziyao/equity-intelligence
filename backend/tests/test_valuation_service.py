from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.quotes.models import Freshness, MarketStatus, Quote, QuoteResult
from app.repositories.stock_repository import StockRepository
from app.services.valuation_service import ValuationService
from test_fundamentals import persist_period


def make_quote(price=303.25, freshness=Freshness.DELAYED):
    now = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    return Quote(symbol="AAPL", price=price, change=1, change_percent=0.3, provider="finnhub", provider_timestamp=now, retrieved_at=now, freshness=freshness, market_status=MarketStatus.CLOSED)


class FakeQuoteService:
    def __init__(self, result):
        self.result = result

    def get_quote(self, symbol):
        return self.result


def valuation(session, quote_result, eps="10.67", year=2025):
    persist_period(session, "AAPL", "annual", year, eps=eps)
    return ValuationService(FakeQuoteService(quote_result)).get_valuation(session, "aapl")


def test_valid_positive_pe_is_decimal_safe_and_preserves_provenance(test_db_session):
    result = valuation(test_db_session, QuoteResult(symbol="AAPL", quote=make_quote()))
    metric = result["data"]["metrics"]["pe"]
    assert metric["value"] == Decimal("28.42")
    assert metric["status"] == "AVAILABLE"
    assert result["data"]["financial_basis"]["label"] == "FY2025"
    assert result["data"]["market"]["freshness"] == "DELAYED"
    assert result["data"]["provenance"] == {"quote_provider": "finnhub", "financial_provider": "alphavantage"}


@pytest.mark.parametrize(
    ("eps", "reason"),
    [(None, "MISSING_INPUT"), ("0", "ZERO_DENOMINATOR"), ("-1", "NEGATIVE_DENOMINATOR")],
)
def test_invalid_eps_keeps_basis_but_does_not_fabricate_pe(test_db_session, eps, reason):
    if eps is None:
        StockRepository.get_or_create(test_db_session, "AAPL")
    else:
        persist_period(test_db_session, "AAPL", "annual", 2025, eps=eps)
    result = ValuationService(FakeQuoteService(QuoteResult(symbol="AAPL", quote=make_quote()))).get_valuation(test_db_session, "AAPL")
    assert result["data"]["metrics"]["pe"]["value"] is None
    assert result["data"]["metrics"]["pe"]["reason"] == reason
    if eps is not None:
        assert result["data"]["financial_basis"]["label"] == "FY2025"


@pytest.mark.parametrize("freshness", [Freshness.REALTIME, Freshness.DELAYED, Freshness.LATEST_TRADING_DAY])
def test_acceptable_quote_freshness_allows_pe(test_db_session, freshness):
    result = valuation(test_db_session, QuoteResult(symbol="AAPL", quote=make_quote(freshness=freshness)))
    assert result["data"]["metrics"]["pe"]["status"] == "AVAILABLE"
    assert result["data"]["market"]["freshness"] == freshness.value


def test_stale_and_unavailable_quotes_isolate_pe(test_db_session):
    stale = valuation(test_db_session, QuoteResult(symbol="AAPL", quote=make_quote(freshness=Freshness.STALE), error="stale"))
    assert stale["data"]["market"]["freshness"] == "STALE"
    assert stale["data"]["metrics"]["pe"]["reason"] == "STALE_MARKET_PRICE"

    unavailable = valuation(test_db_session, QuoteResult(symbol="AAPL", quote=None, error="down"))
    assert unavailable["data"]["market"] is None
    assert unavailable["data"]["financial_basis"]["label"] == "FY2025"
    assert unavailable["data"]["metrics"]["pe"]["reason"] == "MISSING_INPUT"


def test_older_valid_annual_basis_is_explicitly_labeled(test_db_session):
    persist_period(test_db_session, "AAPL", "annual", 2025, eps="")
    persist_period(test_db_session, "AAPL", "annual", 2024, eps="10")
    result = ValuationService(FakeQuoteService(QuoteResult(symbol="AAPL", quote=make_quote()))).get_valuation(test_db_session, "AAPL")
    assert result["data"]["financial_basis"]["label"] == "FY2024"
    assert result["data"]["metrics"]["pe"]["denominator"] == "FY2024 diluted EPS"


def test_deferred_metrics_are_always_unavailable(test_db_session):
    result = valuation(test_db_session, QuoteResult(symbol="AAPL", quote=make_quote()))
    for name in ("price_to_sales", "price_to_fcf"):
        assert result["data"]["metrics"][name]["value"] is None
        assert result["data"]["metrics"][name]["reason"] == "SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE"


def test_missing_fundamentals_returns_market_data(test_db_session):
    StockRepository.get_or_create(test_db_session, "AAPL")
    result = ValuationService(FakeQuoteService(QuoteResult(symbol="AAPL", quote=make_quote()))).get_valuation(test_db_session, "AAPL")
    assert result["data"]["market"]["price"] == 303.25
    assert result["data"]["financial_basis"] is None
    assert result["data"]["metrics"]["pe"]["reason"] == "MISSING_INPUT"
