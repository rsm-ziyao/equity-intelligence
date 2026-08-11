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


def mock_get_daily_success(*args, **kwargs):
    j = {
        "Meta Data": {"1. Information": "Daily Prices"},
        "Time Series (Daily)": {
            "2026-08-11": {"1. open": "190.0", "2. high": "191.0", "3. low": "189.5", "4. close": "190.5", "5. volume": "1200"},
            "2026-08-10": {"1. open": "189.0", "2. high": "190.0", "3. low": "188.5", "4. close": "189.5", "5. volume": "800"},
        },
    }
    return DummyResp(200, j)


def mock_get_rate_limited(*args, **kwargs):
    return DummyResp(200, {"Note": "Thank you for using Alpha Vantage"})


def test_intraday_is_not_requested_without_entitlement():
    adapter = AlphaVantageAdapter(api_key="DUMMYKEY", base_url="https://www.alphavantage.co")
    with pytest.raises(ProviderError, match="intraday data is not available"):
        adapter.get_intraday("AAPL", interval="1min")


def test_daily_uses_compact_unadjusted_endpoint(monkeypatch):
    adapter = AlphaVantageAdapter(api_key="DUMMYKEY", base_url="https://www.alphavantage.co")
    calls = []

    def request(self, method, url, **kwargs):
        calls.append(kwargs["params"])
        return mock_get_daily_success()

    monkeypatch.setattr(adapter, "client", type("C", (), {"request": request})())
    bars = adapter.get_historical_daily("AAPL")

    assert len(bars) == 2
    assert calls == [{"function": "TIME_SERIES_DAILY", "symbol": "AAPL", "outputsize": "compact", "apikey": "DUMMYKEY"}]
    assert bars[0].close == 190.5


def test_rate_limit_handling(monkeypatch):
    adapter = AlphaVantageAdapter(api_key="DUMMYKEY", base_url="https://www.alphavantage.co")
    monkeypatch.setattr(adapter, "client", type("C", (), {"request": lambda self, m, u, **k: mock_get_rate_limited()})())
    with pytest.raises(ProviderRateLimitError):
        adapter.get_historical_daily("AAPL")
