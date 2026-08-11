"""Pytest configuration and fixtures for database tests."""

import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database.models import Base
from app.marketdata.adapters.alphavantage import AlphaVantageAdapter
from app.repositories.stock_repository import StockRepository, StockPriceRepository


# Use in-memory SQLite for testing (no external DB required)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a fresh in-memory SQLite database engine for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite requirement
        poolclass=StaticPool,  # Share the in-memory database with TestClient threads
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Session:
    """Create a fresh database session for each test."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
    }


@pytest.fixture
def sample_price_data():
    """Sample price data for testing (named for StockPriceRepository.create())."""
    return {
        "timestamp": datetime(2026, 8, 11, 14, 30, 0),
        "open_price": 150.0,
        "high": 151.5,
        "low": 149.5,
        "close": 151.0,
        "volume": 1000000,
        "provider": "alpha_vantage",
        "provider_timestamp": "2026-08-11 14:30:00",
        "retrieved_at": datetime(2026, 8, 11, 14, 35, 0),
    }


@pytest.fixture
def mock_alpha_vantage_adapter():
    """Mock Alpha Vantage adapter for testing (no live API calls)."""
    return AlphaVantageAdapter(
        api_key="test_key",
        base_url="https://www.alphavantage.co",
        timeout=5.0,
    )
