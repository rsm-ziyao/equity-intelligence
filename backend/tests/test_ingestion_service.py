"""Tests for the ingestion service.

Tests the full pipline:
MarketDataClient → Bar validation → Repository (persistence)
"""

from datetime import datetime
from typing import Iterable
from unittest.mock import MagicMock

import pytest

from app.marketdata.client import MarketDataClient
from app.marketdata.models import Bar
from app.services.ingestion_service import IngestionService
from app.repositories.stock_repository import StockRepository, StockPriceRepository


class MockMarketDataClient(MarketDataClient):
    """Mock client for testing ingestion service."""

    def __init__(self, bars: list[Bar]):
        self.bars = bars

    def get_intraday(self, symbol: str, interval: str = "1min") -> Iterable[Bar]:
        return iter(self.bars)

    def get_historical_daily(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> Iterable[Bar]:
        return iter(self.bars)


class TestIngestionService:
    """Tests for IngestionService."""

    def test_ingest_intraday_creates_stock_and_prices(self, test_db_session):
        """Test ingest_intraday creates stock and persists prices."""
        bars = [
            Bar(
                symbol="AAPL",
                open=150.0,
                high=151.5,
                low=149.5,
                close=151.0,
                volume=1000000,
                provider="alpha_vantage",
                provider_timestamp="2026-08-11 14:30:00",
                retrieved_at=datetime(2026, 8, 11, 14, 35, 0),
            ),
            Bar(
                symbol="AAPL",
                open=151.0,
                high=152.0,
                low=150.5,
                close=151.5,
                volume=800000,
                provider="alpha_vantage",
                provider_timestamp="2026-08-11 14:35:00",
                retrieved_at=datetime(2026, 8, 11, 14, 40, 0),
            ),
        ]

        client = MockMarketDataClient(bars)
        service = IngestionService(client)

        stats = service.ingest_intraday(test_db_session, "AAPL", interval="1min")

        assert stats["created"] == 2
        assert stats["skipped"] == 0
        assert stats["errors"] == 0

        # Verify stock was created
        stock = StockRepository.get_by_symbol(test_db_session, "AAPL")
        assert stock is not None

        # Verify prices were persisted
        prices = StockPriceRepository.get_latest_by_stock(test_db_session, stock.id)
        assert len(prices) == 2
        assert prices[0].close == 151.5  # Latest (descending)
        assert prices[1].close == 151.0

    def test_ingest_daily_creates_stock_and_prices(self, test_db_session):
        """Test ingest_daily creates stock and persists daily prices."""
        bars = [
            Bar(
                symbol="AAPL",
                open=150.0,
                high=151.5,
                low=149.5,
                close=151.0,
                volume=10000000,
                provider="alpha_vantage",
                provider_timestamp="2026-08-10",
                retrieved_at=datetime(2026, 8, 11, 0, 0, 0),
            ),
            Bar(
                symbol="AAPL",
                open=151.0,
                high=152.0,
                low=150.5,
                close=151.5,
                volume=8000000,
                provider="alpha_vantage",
                provider_timestamp="2026-08-11",
                retrieved_at=datetime(2026, 8, 12, 0, 0, 0),
            ),
        ]

        client = MockMarketDataClient(bars)
        service = IngestionService(client)

        stats = service.ingest_daily(test_db_session, "AAPL")

        assert stats["created"] == 2
        assert stats["skipped"] == 0

    def test_ingest_skips_duplicates(self, test_db_session):
        """Test that ingest skips duplicate (stock_id, provider, provider_timestamp) records."""
        bars = [
            Bar(
                symbol="AAPL",
                open=150.0,
                high=151.5,
                low=149.5,
                close=151.0,
                volume=1000000,
                provider="alpha_vantage",
                provider_timestamp="2026-08-11 14:30:00",
                retrieved_at=datetime(2026, 8, 11, 14, 35, 0),
            ),
        ]

        client = MockMarketDataClient(bars)
        service = IngestionService(client)

        # First ingest
        stats1 = service.ingest_intraday(test_db_session, "AAPL")
        assert stats1["created"] == 1

        # Second ingest (same data)
        stats2 = service.ingest_intraday(test_db_session, "AAPL")
        assert stats2["created"] == 0
        assert stats2["skipped"] == 1

    def test_ingest_allows_different_timestamps(self, test_db_session):
        """Test that ingest allows multiple prices for same provider (different timestamps)."""
        bar1 = Bar(
            symbol="AAPL",
            open=150.0,
            high=151.5,
            low=149.5,
            close=151.0,
            volume=1000000,
            provider="alpha_vantage",
            provider_timestamp="2026-08-11 14:30:00",
            retrieved_at=datetime(2026, 8, 11, 14, 35, 0),
        )

        bar2 = Bar(
            symbol="AAPL",
            open=151.0,
            high=152.0,
            low=150.5,
            close=151.5,
            volume=800000,
            provider="alpha_vantage",
            provider_timestamp="2026-08-11 14:35:00",
            retrieved_at=datetime(2026, 8, 11, 14, 40, 0),
        )

        client = MockMarketDataClient([bar1, bar2])
        service = IngestionService(client)

        stats = service.ingest_intraday(test_db_session, "AAPL")

        assert stats["created"] == 2
        assert stats["skipped"] == 0

    def test_ingest_allows_multiple_providers(self, test_db_session):
        """Test that ingest allows same timestamp from different providers."""
        shared_ts = "2026-08-11 14:30:00"

        bar_av = Bar(
            symbol="AAPL",
            open=150.0,
            high=151.5,
            low=149.5,
            close=151.0,
            volume=1000000,
            provider="alpha_vantage",
            provider_timestamp=shared_ts,
            retrieved_at=datetime(2026, 8, 11, 14, 35, 0),
        )

        bar_polygon = Bar(
            symbol="AAPL",
            open=150.1,  # Slightly different price
            high=151.6,
            low=149.4,
            close=151.1,
            volume=1000500,
            provider="polygon_io",
            provider_timestamp=shared_ts,
            retrieved_at=datetime(2026, 8, 11, 14, 35, 0),
        )

        # First ingest: alpha_vantage
        client_av = MockMarketDataClient([bar_av])
        service_av = IngestionService(client_av)
        stats_av = service_av.ingest_intraday(test_db_session, "AAPL")
        assert stats_av["created"] == 1

        # Second ingest: polygon_io (different provider, same timestamp)
        client_polygon = MockMarketDataClient([bar_polygon])
        service_polygon = IngestionService(client_polygon)
        stats_polygon = service_polygon.ingest_intraday(test_db_session, "AAPL")
        assert stats_polygon["created"] == 1  # Should create, not skip

        # Verify both are persisted
        stock = StockRepository.get_by_symbol(test_db_session, "AAPL")
        prices = StockPriceRepository.get_latest_by_stock(test_db_session, stock.id)
        assert len(prices) == 2
        providers = {p.provider for p in prices}
        assert providers == {"alpha_vantage", "polygon_io"}

    def test_ingest_provider_error_propagates(self, test_db_session):
        """Test that provider errors are propagated."""
        class ErrorClient(MarketDataClient):
            def get_intraday(self, symbol: str, interval: str = "1min"):
                raise RuntimeError("Provider connection failed")

            def get_historical_daily(self, symbol: str, start: str | None = None, end: str | None = None):
                raise RuntimeError("Provider connection failed")

        service = IngestionService(ErrorClient())

        with pytest.raises(RuntimeError, match="Failed to fetch intraday"):
            service.ingest_intraday(test_db_session, "AAPL")
