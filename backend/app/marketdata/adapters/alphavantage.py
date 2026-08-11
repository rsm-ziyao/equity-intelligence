from __future__ import annotations
import logging
from datetime import datetime
from typing import Iterable, Dict, Any
import httpx

from ..client import MarketDataClient
from ..models import Bar
from ..config import ALPHAVANTAGE_API_KEY, ALPHAVANTAGE_BASE
from ..exceptions import ProviderError, ProviderRateLimitError
from ..utils import request_with_retry

logger = logging.getLogger(__name__)


class AlphaVantageAdapter(MarketDataClient):
    provider_name = "alphavantage"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 10.0):
        self.api_key = api_key or ALPHAVANTAGE_API_KEY
        if not self.api_key:
            raise ProviderError("Alpha Vantage API key not configured")
        self.base = base_url or ALPHAVANTAGE_BASE
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base, timeout=self.timeout)

    def _call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params)
        params["apikey"] = self.api_key
        url = "/query"
        resp = request_with_retry(self.client, "GET", url, params=params)
        return resp.json()

    def _parse_time_series(self, meta: Dict[str, Any], series: Dict[str, Any], symbol: str) -> Iterable[Bar]:
        retrieved_at = datetime.utcnow().isoformat()
        for ts_str, values in series.items():
            # values like {'1. open': '...'}
            try:
                o = float(values.get("1. open"))
                h = float(values.get("2. high"))
                l = float(values.get("3. low"))
                c = float(values.get("4. close"))
                v = int(float(values.get("5. volume", 0)))
            except Exception as e:
                raise ProviderError(f"Malformed bar values: {values} ({e})")

            yield Bar(
                symbol=symbol,
                provider=self.provider_name,
                provider_timestamp=ts_str,
                retrieved_at=retrieved_at,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
            )

    def get_intraday(self, symbol: str, interval: str = "1min") -> Iterable[Bar]:
        raise ProviderError(
            "Alpha Vantage intraday data is not available on the configured entitlement"
        )

    def get_historical_daily(self, symbol: str, start: str | None = None, end: str | None = None) -> Iterable[Bar]:
        params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact"}
        j = self._call(params)
        if "Note" in j:
            raise ProviderRateLimitError(j["Note"])
        key = None
        for k in j.keys():
            if k.startswith("Time Series"):
                key = k
                break
        if key is None:
            raise ProviderError(f"Unexpected response shape: {j}")
        series = j[key]
        # filter by date if needed
        bars = list(self._parse_time_series(j.get("Meta Data", {}), series, symbol))
        if start or end:
            s_dt = datetime.fromisoformat(start) if start else None
            e_dt = datetime.fromisoformat(end) if end else None
            filtered = []
            for b in bars:
                if s_dt and b.provider_timestamp < s_dt:
                    continue
                if e_dt and b.provider_timestamp > e_dt:
                    continue
                filtered.append(b)
            return filtered
        return bars
