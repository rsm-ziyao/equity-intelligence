from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes.quotes import get_quote_service
from app.main import app
from app.marketdata.exceptions import ProviderError
from app.quotes.adapters.finnhub import FinnhubQuoteAdapter, classify_freshness, normalize_market_status
from app.quotes.cache import QuoteCache
from app.quotes.models import Freshness, MarketStatus, Quote
from app.quotes.service import QuoteService


def quote(symbol="AAPL", freshness=Freshness.DELAYED):
    now = datetime.now(timezone.utc)
    return Quote(symbol=symbol, price=100, change=1, change_percent=1, provider="finnhub", provider_timestamp=now, retrieved_at=now, freshness=freshness, market_status=MarketStatus.OPEN)


class FakeClient:
    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail or set()

    def get_quote(self, symbol):
        self.calls.append(symbol)
        if symbol in self.fail:
            raise ProviderError("provider down")
        return quote(symbol)


def test_finnhub_adapter_parses_quote_and_never_exposes_key():
    def handler(request):
        if request.url.path == "/quote":
            assert request.url.params["symbol"] == "AAPL"
            assert request.url.params["token"] == "secret"
            return httpx.Response(200, json={"c": 190.5, "d": 1.5, "dp": 0.79, "t": 1786640000})
        return httpx.Response(200, json={"marketStatus": "open"})

    adapter = FinnhubQuoteAdapter(api_key="secret", client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://test"), realtime_entitled=False)
    result = adapter.get_quote(" aapl ")
    assert result.symbol == "AAPL"
    assert result.price == 190.5
    assert result.freshness in {Freshness.DELAYED, Freshness.LATEST_TRADING_DAY}
    assert "secret" not in result.model_dump_json()


def test_config_missing_key_is_rejected(monkeypatch):
    monkeypatch.setattr("app.quotes.adapters.finnhub.FINNHUB_API_KEY", None)
    with pytest.raises(ProviderError, match="not configured"):
        FinnhubQuoteAdapter()


def test_normalization_deduplicates_and_classifies():
    client = FakeClient()
    service = QuoteService(client)
    results, failures = service.get_quotes([" aapl", "AAPL", "msft"])
    assert [result.symbol for result in results] == ["AAPL", "MSFT"]
    assert client.calls == ["AAPL", "MSFT"]
    assert failures == []
    now = datetime.now(timezone.utc)
    assert classify_freshness(now, now, False) == Freshness.DELAYED
    assert classify_freshness(now, now, True) == Freshness.REALTIME
    assert classify_freshness(now - timedelta(days=1), now) == Freshness.LATEST_TRADING_DAY
    assert normalize_market_status("post_market") == MarketStatus.POST_MARKET


def test_cache_and_stale_if_error():
    client = FakeClient(fail={"AAPL"})
    cache = QuoteCache(ttl_seconds=0, stale_seconds=600)
    service = QuoteService(client, cache)
    cache.put("AAPL", quote())
    result = service.get_quote("AAPL")
    assert result.quote.freshness == Freshness.STALE
    assert result.error


def test_single_and_batch_quote_endpoints_preserve_partial_failures():
    service = QuoteService(FakeClient(fail={"NVDA"}))
    app.dependency_overrides[get_quote_service] = lambda: service
    try:
        with TestClient(app) as client:
            single = client.get("/api/v1/quotes/aapl")
            assert single.status_code == 200
            assert single.json()["data"]["symbol"] == "AAPL"
            batch = client.get("/api/v1/quotes?symbols=AAPL,MSFT,AAPL,NVDA")
            body = batch.json()
            assert batch.status_code == 200
            assert [item["symbol"] for item in body["data"]] == ["AAPL", "MSFT", "NVDA"]
            assert body["meta"]["requested_symbol_count"] == 3
            assert body["meta"]["returned_symbol_count"] == 2
            assert body["meta"]["failed_symbols"] == ["NVDA"]
            assert body["data"][2]["quote"] is None
    finally:
        app.dependency_overrides.clear()
