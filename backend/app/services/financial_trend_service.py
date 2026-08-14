from __future__ import annotations

from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..api.exceptions import DatabaseUnavailableError, StockNotFoundError
from ..repositories.fundamentals_repository import FundamentalsRepository


FINANCIAL_METRICS = (
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "diluted_eps",
    "operating_cash_flow",
    "capital_expenditures",
    "free_cash_flow",
    "cash_and_cash_equivalents",
    "total_debt",
    "gross_margin",
    "operating_margin",
    "profit_margin",
)
GROWTH_METRICS = {
    "revenue": "revenue_yoy_growth",
    "net_income": "net_income_yoy_growth",
    "diluted_eps": "eps_yoy_growth",
    "free_cash_flow": "free_cash_flow_yoy_growth",
}


class FinancialTrendService:
    DEFAULT_LIMIT = 8
    MAX_LIMIT = 20

    @staticmethod
    def validate_period_type(period_type: str) -> str:
        normalized = period_type.lower()
        if normalized not in {"annual", "quarterly"}:
            raise ValueError("period_type must be annual or quarterly")
        return normalized

    @classmethod
    def validate_limit(cls, limit: int) -> int:
        if not isinstance(limit, int) or not 1 <= limit <= cls.MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {cls.MAX_LIMIT}")
        return limit

    @staticmethod
    def _divide(value: Decimal | None, denominator: Decimal | None) -> Decimal | None:
        if value is None or denominator in (None, 0):
            return None
        return value / denominator

    @classmethod
    def period_payload(cls, period) -> dict:
        income = period.income_statement
        cash_flow = period.cash_flow
        balance = period.balance_sheet
        revenue = income.revenue if income else None
        free_cash_flow = (
            cash_flow.operating_cash_flow - cash_flow.capital_expenditures
            if cash_flow
            and cash_flow.operating_cash_flow is not None
            and cash_flow.capital_expenditures is not None
            else None
        )
        source = income or cash_flow or balance
        return {
            "period_type": period.fiscal_period_type,
            "fiscal_year": period.fiscal_year,
            "fiscal_quarter": period.fiscal_quarter,
            "period_start": period.period_start,
            "period_end": period.period_end,
            "filing_date": period.filing_date,
            "revenue": revenue,
            "gross_profit": income.gross_profit if income else None,
            "operating_income": income.operating_income if income else None,
            "net_income": income.net_income if income else None,
            "diluted_eps": income.diluted_eps if income else None,
            "operating_cash_flow": cash_flow.operating_cash_flow if cash_flow else None,
            "capital_expenditures": cash_flow.capital_expenditures if cash_flow else None,
            "free_cash_flow": free_cash_flow,
            "cash_and_cash_equivalents": balance.cash_and_cash_equivalents if balance else None,
            "total_debt": balance.total_debt if balance else None,
            "gross_margin": cls._divide(income.gross_profit if income else None, revenue),
            "operating_margin": cls._divide(income.operating_income if income else None, revenue),
            "profit_margin": cls._divide(income.net_income if income else None, revenue),
            "currency": source.currency if source else None,
            "unit": source.unit if source else None,
            "provider": period.provider,
            "retrieved_at": period.retrieved_at,
        }

    @staticmethod
    def _period_identity(record: dict) -> tuple | None:
        fiscal_year = record.get("fiscal_year")
        if fiscal_year is None:
            return None
        if record["period_type"] == "annual":
            return ("annual", fiscal_year)
        fiscal_quarter = record.get("fiscal_quarter")
        if fiscal_quarter is None:
            return None
        return ("quarterly", fiscal_year, fiscal_quarter)

    @staticmethod
    def _growth(current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous in (None, 0):
            return None
        if current != 0 and ((current < 0) != (previous < 0)):
            return None
        return (current - previous) / abs(previous)

    @classmethod
    def _add_growth(cls, records: list[dict]) -> None:
        by_identity = {cls._period_identity(record): record for record in records}
        for record in records:
            identity = cls._period_identity(record)
            for metric, growth_name in GROWTH_METRICS.items():
                previous = None
                if identity and identity[0] == "annual":
                    previous = by_identity.get(("annual", identity[1] - 1))
                elif identity and identity[0] == "quarterly":
                    previous = by_identity.get(("quarterly", identity[1] - 1, identity[2]))
                record[growth_name] = cls._growth(
                    record.get(metric), previous.get(metric) if previous else None
                )

    @staticmethod
    def _period_label(record: dict) -> str:
        if record["period_type"] == "quarterly" and record.get("fiscal_quarter") is not None:
            return f"Q{record['fiscal_quarter']} FY{record['fiscal_year']}"
        return f"FY{record['fiscal_year']}"

    @classmethod
    def get_history(
        cls,
        session: Session,
        symbol: str,
        period_type: str = "annual",
        limit: int = DEFAULT_LIMIT,
        provider: str = "alphavantage",
    ) -> dict:
        period_type = cls.validate_period_type(period_type)
        limit = cls.validate_limit(limit)
        normalized = symbol.upper()
        try:
            stock = FundamentalsRepository.find_stock(session, normalized)
            if stock is None:
                raise StockNotFoundError(normalized)
            lookback = 1 if period_type == "annual" else 4
            periods = FundamentalsRepository.get_financial_history(
                session, stock.id, period_type, limit + lookback, provider
            )
        except StockNotFoundError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            raise DatabaseUnavailableError() from exc

        ordered = [cls.period_payload(period) for period in reversed(periods)]
        cls._add_growth(ordered)
        records = ordered[-limit:]
        metric_coverage = {
            metric: sum(record.get(metric) is not None for record in records)
            for metric in FINANCIAL_METRICS
        }
        missing_metrics = [metric for metric, count in metric_coverage.items() if count == 0]
        missing_periods = [
            {
                "label": cls._period_label(record),
                "period_end": record["period_end"],
                "missing_metrics": [
                    metric for metric in FINANCIAL_METRICS if record.get(metric) is None
                ],
            }
            for record in records
            if any(record.get(metric) is None for metric in FINANCIAL_METRICS)
        ]
        if not records:
            return {
                "data": None,
                "meta": {
                    "available": False,
                    "periods_returned": 0,
                    "requested_limit": limit,
                    "missing_metrics": [],
                    "metric_coverage": {},
                    "missing_periods": [],
                },
            }

        latest = records[-1]
        return {
            "data": {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "period_type": period_type,
                "periods": records,
                "provenance": {
                    "provider": provider,
                    "retrieved_at": latest["retrieved_at"],
                    "freshness": "PERIODIC",
                },
            },
            "meta": {
                "available": True,
                "periods_returned": len(records),
                "requested_limit": limit,
                "missing_metrics": missing_metrics,
                "metric_coverage": metric_coverage,
                "missing_periods": missing_periods,
            },
        }
