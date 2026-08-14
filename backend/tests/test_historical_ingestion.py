from datetime import datetime

from app.marketdata.client import MarketDataClient
from app.marketdata.exceptions import ProviderRateLimitError
from app.marketdata.models import Bar
from app.services.historical_ingestion import (
    HistoricalIngestionCoordinator,
    summarize_results,
)
from app.services.ingestion_service import IngestionService
from app.repositories.stock_repository import StockPriceRepository, StockRepository


def bar(symbol: str, day: str) -> Bar:
    return Bar(
        symbol=symbol,
        provider="alphavantage",
        provider_timestamp=day,
        retrieved_at=datetime(2026, 8, 12),
        open=10,
        high=11,
        low=9,
        close=10.5,
        volume=100,
    )


class BatchClient(MarketDataClient):
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_intraday(self, symbol: str, interval: str = "1min"):
        raise AssertionError("historical batch must not use intraday")

    def get_historical_daily(self, symbol: str, start=None, end=None):
        self.calls.append(symbol)
        response = self.responses[symbol]
        if isinstance(response, Exception):
            raise response
        return iter(response)


def test_configured_symbols_are_normalized_and_deduplicated(monkeypatch):
    from app.marketdata.config import get_supported_symbols

    assert get_supported_symbols(" aapl, MSFT, AAPL, ,nvda ") == ("AAPL", "MSFT", "NVDA")
    monkeypatch.setenv("SUPPORTED_SYMBOLS", " AMD, NFLX, AMD ")
    assert get_supported_symbols() == ("AMD", "NFLX")


def test_configured_symbols_reject_invalid_values():
    from app.marketdata.config import get_supported_symbols

    import pytest
    with pytest.raises(ValueError, match="Invalid stock symbol"):
        get_supported_symbols("AAPL,not valid")


def test_coordinator_processes_sequentially_and_reports_results(test_db_session):
    client = BatchClient({"AMD": [bar("AMD", "2026-08-11")], "NVDA": []})
    service = IngestionService(client)
    sleeps = []
    coordinator = HistoricalIngestionCoordinator(service, delay_seconds=2, sleep=sleeps.append)

    results = coordinator.ingest(test_db_session, [" AMD ", "NVDA"])

    assert client.calls == ["AMD", "NVDA"]
    assert sleeps == [2]
    assert [(result.symbol, result.status, result.created) for result in results] == [
        ("AMD", "ok", 1),
        ("NVDA", "no_data", 0),
    ]


def test_coordinator_continues_after_failure_and_stops_after_rate_limit(test_db_session):
    client = BatchClient({
        "AMD": RuntimeError("timeout"),
        "NVDA": [bar("NVDA", "2026-08-11")],
        "MSFT": ProviderRateLimitError("limited"),
        "AAPL": [bar("AAPL", "2026-08-11")],
    })
    results = HistoricalIngestionCoordinator(IngestionService(client)).ingest(
        test_db_session, ["AMD", "NVDA", "MSFT", "AAPL"]
    )

    assert client.calls == ["AMD", "NVDA", "MSFT"]
    assert [result.status for result in results] == ["failed", "ok", "rate_limited", "not_attempted"]
    assert summarize_results(results) == {"successful": 1, "failed": 2, "no_data": 0}


def test_repeated_batch_ingestion_is_idempotent(test_db_session):
    client = BatchClient({"AMD": [bar("AMD", "2026-08-11")]})
    coordinator = HistoricalIngestionCoordinator(IngestionService(client))

    first = coordinator.ingest(test_db_session, ["AMD"])[0]
    second = coordinator.ingest(test_db_session, ["AMD"])[0]

    assert (first.created, first.skipped) == (1, 0)
    assert (second.created, second.skipped) == (0, 1)
    stock = StockRepository.get_by_symbol(test_db_session, "AMD")
    assert len(StockPriceRepository.get_latest_by_stock(test_db_session, stock.id)) == 1
