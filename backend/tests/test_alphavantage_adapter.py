import json
from datetime import datetime
import httpx
import pytest

from app.marketdata.adapters.alphavantage import AlphaVantageAdapter
from app.marketdata.exceptions import ProviderRateLimitError, ProviderError


class DummyResp:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    @property
    def is_error(self):
        return not (200 <= self.status_code < 300)

    def json(self):
        return self._json


def mock_get_intraday_success(*args, **kwargs):
    # minimal intraday response shape
    j = {
        "Meta Data": {"1. Information": "Intraday"},
        "Time Series (1min)": {
            "2026-08-11 15:59:00": {"1. open": "190.0", "2. high": "191.0", "3. low": "189.5", "4. close": "190.5", "5. volume": "1200"},
            "2026-08-11 15:58:00": {"1. open": "189.0", "2. high": "190.0", "3. low": "188.5", "4. close": "189.5", "5. volume": "800"},
        },
    }
    return DummyResp(200, j)


def mock_get_rate_limited(*args, **kwargs):
    return DummyResp(200, {"Note": "Thank you for using Alpha Vantage"})


def test_intraday_parsing(monkeypatch):
    adapter = AlphaVantageAdapter(api_key="DUMMYKEY", base_url="https://www.alphavantage.co")

    def fake_request(method, url, **kwargs):
        return mock_get_intraday_success()

    monkeypatch.setattr(adapter, "client", type("C", (), {"request": lambda self, m, u, **k: mock_get_intraday_success()})())
    bars = adapter.get_intraday("AAPL", interval="1min")
    assert len(bars) == 2
    # check fields
    b0 = bars[0]
    assert b0.symbol == "AAPL"
    assert b0.provider == "alphavantage"
    assert b0.open >= 0


def test_rate_limit_handling(monkeypatch):
    adapter = AlphaVantageAdapter(api_key="DUMMYKEY", base_url="https://www.alphavantage.co")
    monkeypatch.setattr(adapter, "client", type("C", (), {"request": lambda self, m, u, **k: mock_get_rate_limited()})())
    with pytest.raises(ProviderRateLimitError):
        adapter.get_intraday("AAPL")
