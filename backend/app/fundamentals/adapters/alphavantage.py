from __future__ import annotations
from datetime import datetime
from typing import Any
import httpx
from ..client import FundamentalsClient
from ..exceptions import FundamentalsProviderError, FundamentalsRateLimitError
from ..models import first
from ...marketdata.config import ALPHAVANTAGE_API_KEY, ALPHAVANTAGE_BASE
from ...marketdata.utils import request_with_retry

class AlphaVantageFundamentalsAdapter(FundamentalsClient):
    provider_name = "alphavantage"
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 15.0):
        self.api_key = api_key or ALPHAVANTAGE_API_KEY
        if not self.api_key: raise FundamentalsProviderError("Alpha Vantage API key not configured")
        self.client = httpx.Client(base_url=base_url or ALPHAVANTAGE_BASE, timeout=timeout)
    def _safe_message(self, value: Any) -> str:
        message = str(value)
        return message.replace(self.api_key or "", "[redacted-api-key]")
    def _call(self, function: str, symbol: str) -> dict[str, Any]:
        response = request_with_retry(self.client, "GET", "/query", params={"function": function, "symbol": symbol, "apikey": self.api_key})
        body = response.json()
        if "Note" in body: raise FundamentalsRateLimitError(self._safe_message(body["Note"]))
        if "Information" in body:
            message = self._safe_message(body["Information"])
            if "rate limit" in message.lower() or "requests per day" in message.lower():
                raise FundamentalsRateLimitError(message)
            raise FundamentalsProviderError(message)
        if "Error Message" in body: raise FundamentalsProviderError(self._safe_message(body["Error Message"]))
        key = {"INCOME_STATEMENT":"annualReports", "BALANCE_SHEET":"annualReports", "CASH_FLOW":"annualReports"}[function]
        if key not in body or not isinstance(body[key], list): raise FundamentalsProviderError(f"Unexpected {function} response shape")
        return body
    def _rows(self, function: str, symbol: str) -> list[dict[str, Any]]:
        body = self._call(function, symbol); rows = []
        for row in body.get("annualReports", []) + body.get("quarterlyReports", []):
            item = dict(row); item["_period_type"] = "annual" if row in body.get("annualReports", []) else "quarterly"; rows.append(item)
        return rows
    def get_income_statement(self, symbol: str) -> list[dict[str, Any]]: return self._rows("INCOME_STATEMENT", symbol)
    def get_balance_sheet(self, symbol: str) -> list[dict[str, Any]]: return self._rows("BALANCE_SHEET", symbol)
    def get_cash_flow(self, symbol: str) -> list[dict[str, Any]]: return self._rows("CASH_FLOW", symbol)
