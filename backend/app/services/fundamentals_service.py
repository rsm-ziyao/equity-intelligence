from __future__ import annotations
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from ..api.exceptions import DatabaseUnavailableError, StockNotFoundError
from ..repositories.fundamentals_repository import FundamentalsRepository

class FundamentalsService:
    def __init__(self, client=None): self.client = client
    @staticmethod
    def _divide(a, b): return a / b if a is not None and b not in (None, 0) else None
    @staticmethod
    def _payload(period):
        income, cash, balance = period.income_statement, period.cash_flow, period.balance_sheet
        revenue = income.revenue if income else None
        free_cash_flow = (cash.operating_cash_flow - cash.capital_expenditures
                          if cash and cash.operating_cash_flow is not None and cash.capital_expenditures is not None
                          else None)
        source = income or cash or balance
        return {
            "period_type": period.fiscal_period_type, "fiscal_year": period.fiscal_year,
            "fiscal_quarter": period.fiscal_quarter, "period_start": period.period_start,
            "period_end": period.period_end, "filing_date": period.filing_date,
            "revenue": revenue, "gross_profit": income.gross_profit if income else None,
            "operating_income": income.operating_income if income else None,
            "net_income": income.net_income if income else None,
            "diluted_eps": income.diluted_eps if income else None,
            "operating_cash_flow": cash.operating_cash_flow if cash else None,
            "capital_expenditures": cash.capital_expenditures if cash else None,
            "free_cash_flow": free_cash_flow,
            "cash_and_cash_equivalents": balance.cash_and_cash_equivalents if balance else None,
            "total_debt": balance.total_debt if balance else None,
            "gross_margin": FundamentalsService._divide(income.gross_profit if income else None, revenue),
            "operating_margin": FundamentalsService._divide(income.operating_income if income else None, revenue),
            "profit_margin": FundamentalsService._divide(income.net_income if income else None, revenue),
            "currency": source.currency if source else None, "unit": source.unit if source else None,
            "provider": period.provider, "retrieved_at": period.retrieved_at,
        }
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
