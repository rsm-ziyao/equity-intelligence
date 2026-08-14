from __future__ import annotations
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from ..api.exceptions import DatabaseUnavailableError, StockNotFoundError
from ..repositories.fundamentals_repository import FundamentalsRepository
from .financial_trend_service import FinancialTrendService

class FundamentalsService:
    def __init__(self, client=None): self.client = client
    @staticmethod
    def _payload(period): return FinancialTrendService.period_payload(period)
    def get(self, session: Session, symbol: str, period_type: str = "latest") -> dict:
        normalized = symbol.upper()
        try:
            stock = FundamentalsRepository.find_stock(session, normalized)
            if stock is None: raise StockNotFoundError(normalized)
            if period_type not in {"quarterly", "annual", "latest"}: raise ValueError("period_type must be quarterly, annual, or latest")
            if period_type == "latest": periods = {"quarterly": FundamentalsRepository.periods(session, stock.id, "quarterly", 1), "annual": FundamentalsRepository.periods(session, stock.id, "annual", 1)}
            else: periods = {period_type: FundamentalsRepository.periods(session, stock.id, period_type, 2)}
        except StockNotFoundError: raise
        except (SQLAlchemyError, OSError) as exc: raise DatabaseUnavailableError() from exc
        records = {key: [self._payload(p) for p in value] for key, value in periods.items()}
        flat = [item for values in records.values() for item in values]
        metric_names = ("revenue", "gross_profit", "operating_income", "net_income", "diluted_eps", "operating_cash_flow", "capital_expenditures", "free_cash_flow", "cash_and_cash_equivalents", "total_debt", "gross_margin", "operating_margin", "profit_margin")
        missing = [name for name in metric_names if not any(item.get(name) is not None for item in flat)]
        latest = flat[0] if flat else None
        quarterly = records.get("quarterly", [])
        annual = records.get("annual", [])
        return {"data": {"symbol": stock.symbol, "company_name": stock.company_name, "financials": {"latest_quarterly": quarterly[0] if quarterly else None, "latest_annual": annual[0] if annual else None}, "provenance": {"provider": latest["provider"] if latest else "alphavantage", "retrieved_at": latest["retrieved_at"] if latest else None, "freshness": "PERIODIC"}} if flat else None, "meta": {"available": bool(flat), "missing_metrics": missing, "periods_returned": len(flat)}}
