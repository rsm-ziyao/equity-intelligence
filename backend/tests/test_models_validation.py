from datetime import datetime
import pytest

from app.marketdata.models import Bar
from app.marketdata.exceptions import ValidationError


def test_valid_bar():
    b = Bar(
        symbol="AAPL",
        provider="alphavantage",
        provider_timestamp=datetime.utcnow().isoformat(),
        retrieved_at=datetime.utcnow().isoformat(),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000,
    )
    assert b.symbol == "AAPL"


def test_invalid_prices():
    with pytest.raises(ValidationError):
        Bar(
            symbol="AAPL",
            provider="alphavantage",
            provider_timestamp=datetime.utcnow().isoformat(),
            retrieved_at=datetime.utcnow().isoformat(),
            open=-1.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=0,
        )


def test_relation_checks():
    # high too low
    with pytest.raises(ValidationError):
        Bar(
            symbol="AAPL",
            provider="alphavantage",
            provider_timestamp=datetime.utcnow().isoformat(),
            retrieved_at=datetime.utcnow().isoformat(),
            open=10.0,
            high=9.0,
            low=8.0,
            close=9.5,
            volume=1,
        )
