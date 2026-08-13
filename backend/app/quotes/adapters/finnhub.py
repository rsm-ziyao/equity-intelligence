from datetime import datetime, timezone
from typing import Any

import httpx

from ...marketdata.config import FINNHUB_API_KEY, FINNHUB_BASE, FINNHUB_REALTIME_ENTITLED
from ...marketdata.exceptions import ProviderError
from ..client import QuoteClient
from ..models import Freshness, MarketStatus, Quote, normalize_symbol, utc_now


def normalize_market_status(value: Any) -> MarketStatus:
    normalized = str(value or "").strip().lower().replace("_", "-").replace(" ", "-")
    return {"pre-market": MarketStatus.PRE_MARKET, "premarket": MarketStatus.PRE_MARKET, "open": MarketStatus.OPEN, "post-market": MarketStatus.POST_MARKET, "postmarket": MarketStatus.POST_MARKET, "closed": MarketStatus.CLOSED, "holiday": MarketStatus.HOLIDAY}.get(normalized, MarketStatus.UNKNOWN)


def classify_freshness(provider_timestamp: datetime, retrieved_at: datetime, realtime_entitled: bool = False) -> Freshness:
    provider_timestamp = provider_timestamp.astimezone(timezone.utc)
    retrieved_at = retrieved_at.astimezone(timezone.utc)
    if provider_timestamp.date() < retrieved_at.date():
        return Freshness.LATEST_TRADING_DAY
    return Freshness.REALTIME if realtime_entitled else Freshness.DELAYED


class FinnhubQuoteAdapter(QuoteClient):
    provider_name = "finnhub"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 10.0, realtime_entitled: bool | None = None, client: httpx.Client | None = None):
        self.api_key = api_key or FINNHUB_API_KEY
        if not self.api_key:
            raise ProviderError("Finnhub API key not configured")
        self.base = base_url or FINNHUB_BASE
        self.realtime_entitled = FINNHUB_REALTIME_ENTITLED if realtime_entitled is None else realtime_entitled
        self.client = client or httpx.Client(base_url=self.base, timeout=timeout)

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        response = self.client.get(path, params={**params, "token": self.api_key})
        if response.status_code in {401, 403}:
            raise ProviderError("Finnhub authentication failed")
        if response.status_code == 429:
            raise ProviderError("Finnhub rate limit exceeded")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ProviderError("Finnhub returned an invalid response")
        return payload

    def get_quote(self, symbol: str) -> Quote:
        symbol = normalize_symbol(symbol)
        payload = self._get("/quote", {"symbol": symbol})
        try:
            price = float(payload["c"])
            change = float(payload.get("d", 0) or 0)
            change_percent = float(payload.get("dp", 0) or 0)
            timestamp = datetime.fromtimestamp(int(payload["t"]), tz=timezone.utc)
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise ProviderError(f"Finnhub returned malformed quote for {symbol}") from exc
        retrieved_at = utc_now()
        status = MarketStatus.UNKNOWN
        try:
            market = self._get("/stock/market-status", {"exchange": "US"})
            status = normalize_market_status(market.get("marketStatus") or market.get("status"))
        except (httpx.HTTPError, ProviderError):
            pass
        return Quote(symbol=symbol, price=price, change=change, change_percent=change_percent, provider=self.provider_name, provider_timestamp=timestamp, retrieved_at=retrieved_at, freshness=classify_freshness(timestamp, retrieved_at, self.realtime_entitled), market_status=status)
