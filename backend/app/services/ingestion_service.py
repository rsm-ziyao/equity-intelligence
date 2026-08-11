"""Ingestion service for market data.

Orchestrates the data pipeline:
MarketDataClient (fetch) → Bar (validate) → Repository (persist)
"""

from typing import Iterable
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..marketdata.client import MarketDataClient
from ..marketdata.models import Bar
from ..repositories.stock_repository import StockRepository, StockPriceRepository


class IngestionService:
    """Orchestrate ingestion of market data into PostgreSQL."""

    def __init__(self, client: MarketDataClient):
        """Initialize with a market data client.
        
        Args:
            client: MarketDataClient implementation (e.g., AlphaVantageAdapter)
        """
        self.client = client

    def ingest_intraday(
        self,
        session: Session,
        symbol: str,
        interval: str = "1min",
    ) -> dict:
        """Fetch intraday data and persist to database.
        
        Args:
            session: SQLAlchemy session
            symbol: Stock ticker (e.g., "AAPL")
            interval: Intraday interval (e.g., "1min", "5min", "15min")
            
        Returns:
            dict with counts: {"created": int, "skipped": int, "errors": int}
            
        Workflow:
        1. Fetch bars from client (raises if rate-limited or provider error)
        2. For each bar:
           - Ensure stock exists (create if needed)
           - Try to create price record (skip if duplicate)
           - Count successes and skips
        """
        stats = {"created": 0, "skipped": 0, "errors": 0}

        try:
            bars: Iterable[Bar] = self.client.get_intraday(symbol, interval=interval)
        except Exception as e:
            # Provider error; re-raise to caller
            raise RuntimeError(f"Failed to fetch intraday for {symbol}: {e}") from e

        # Ensure stock exists
        stock = StockRepository.get_or_create(session, symbol)

        # Persist each bar
        for bar in bars:
            try:
                # Check for duplicate (same provider + provider_timestamp)
                existing = StockPriceRepository.get_by_stock_and_provider_timestamp(
                    session,
                    stock.id,
                    bar.provider,
                    str(bar.provider_timestamp),
                )
                if existing:
                    stats["skipped"] += 1
                    continue

                # Create new price record
                StockPriceRepository.create(
                    session,
                    stock_id=stock.id,
                    timestamp=bar.timestamp,
                    open_price=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    provider=bar.provider,
                    provider_timestamp=bar.provider_timestamp,
                    retrieved_at=bar.retrieved_at,
                )
                stats["created"] += 1

            except IntegrityError as e:
                # Duplicate or constraint violation; skip
                session.rollback()
                stats["skipped"] += 1
            except Exception as e:
                # Unexpected error; log and continue
                session.rollback()
                stats["errors"] += 1
                print(f"Error ingesting bar {bar}: {e}")

        return stats

    def ingest_daily(
        self,
        session: Session,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """Fetch daily data and persist to database.
        
        Args:
            session: SQLAlchemy session
            symbol: Stock ticker (e.g., "AAPL")
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            dict with counts: {"created": int, "skipped": int, "errors": int}
            
        Workflow:
        1. Fetch bars from client
        2. For each bar:
           - Ensure stock exists (create if needed)
           - Try to create price record (skip if duplicate)
           - Count successes and skips
        """
        stats = {"created": 0, "skipped": 0, "errors": 0}

        try:
            bars: Iterable[Bar] = self.client.get_historical_daily(
                symbol,
                start=start_date,
                end=end_date,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch daily for {symbol}: {e}") from e

        # Ensure stock exists
        stock = StockRepository.get_or_create(session, symbol)

        # Persist each bar
        for bar in bars:
            try:
                # Check for duplicate
                existing = StockPriceRepository.get_by_stock_and_provider_timestamp(
                    session,
                    stock.id,
                    bar.provider,
                    str(bar.provider_timestamp),
                )
                if existing:
                    stats["skipped"] += 1
                    continue

                # Create new price record
                StockPriceRepository.create(
                    session,
                    stock_id=stock.id,
                    timestamp=bar.timestamp,
                    open_price=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    provider=bar.provider,
                    provider_timestamp=bar.provider_timestamp,
                    retrieved_at=bar.retrieved_at,
                )
                stats["created"] += 1

            except IntegrityError as e:
                session.rollback()
                stats["skipped"] += 1
            except Exception as e:
                session.rollback()
                stats["errors"] += 1
                print(f"Error ingesting bar {bar}: {e}")

        return stats
