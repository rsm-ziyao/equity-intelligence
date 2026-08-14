from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..api.exceptions import DatabaseUnavailableError, StockNotFoundError
from ..quotes.models import Freshness
from ..quotes.service import QuoteService
from ..repositories.fundamentals_repository import FundamentalsRepository


class ValuationService:
    """Calculate descriptive valuation metrics from current quotes and persisted facts."""

    FINANCIAL_PROVIDER = "alphavantage"

    def __init__(self, quote_service: QuoteService):
        self.quote_service = quote_service

    @staticmethod
    def _basis(period) -> dict:
        eps = period.income_statement.diluted_eps if period.income_statement else None
        return {
            "type": "ANNUAL",
            "fiscal_year": period.fiscal_year,
            "label": f"FY{period.fiscal_year}",
            "period_end": period.period_end,
            "provider": period.provider,
            "retrieved_at": period.retrieved_at,
            "diluted_eps": eps,
        }

    @staticmethod
    def _pe(price: Decimal, eps: Decimal) -> Decimal:
        return (price / eps).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _metric(
        value,
        status: str,
        numerator: str | None = None,
        denominator: str | None = None,
        reason: str | None = None,
    ) -> dict:
        return {
            "value": value,
            "unit": "x",
            "status": status,
            "numerator": numerator,
            "denominator": denominator,
            "reason": reason,
        }

    def get_valuation(self, session: Session, symbol: str) -> dict:
        normalized = symbol.upper()
        try:
            stock = FundamentalsRepository.find_stock(session, normalized)
            if stock is None:
                raise StockNotFoundError(normalized)
            annual_periods = FundamentalsRepository.get_all_annual_periods(
                session, stock.id, self.FINANCIAL_PROVIDER
            )
        except StockNotFoundError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            raise DatabaseUnavailableError() from exc

        quote_result = self.quote_service.get_quote(normalized)
        quote = quote_result.quote
        market = quote.model_dump() if quote else None

        # Use the newest annual period with a reported EPS. If the newest
        # annual period omits EPS, the returned fiscal year makes the older
        # basis explicit rather than silently presenting it as current.
        basis_period = next(
            (
                period
                for period in annual_periods
                if period.income_statement
                and period.income_statement.diluted_eps is not None
            ),
            None,
        )
        basis = self._basis(basis_period) if basis_period else None
        eps = basis["diluted_eps"] if basis else None
        denominator = f"FY{basis_period.fiscal_year} diluted EPS" if basis_period else None

        if quote is None or quote.freshness == Freshness.UNAVAILABLE:
            reason = "MISSING_INPUT"
        elif quote.freshness == Freshness.STALE:
            reason = "STALE_MARKET_PRICE"
        elif basis is None:
            reason = "MISSING_INPUT"
        elif eps == 0:
            reason = "ZERO_DENOMINATOR"
        elif eps < 0:
            reason = "NEGATIVE_DENOMINATOR"
        else:
            reason = None

        pe = self._metric(
            None if reason else self._pe(Decimal(str(quote.price)), eps),
            "UNAVAILABLE" if reason else "AVAILABLE",
            "current share price",
            denominator,
            reason,
        )
        deferred_reason = "SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE"
        metrics = {
            "pe": pe,
            "price_to_sales": self._metric(None, "UNAVAILABLE", reason=deferred_reason),
            "price_to_fcf": self._metric(None, "UNAVAILABLE", reason=deferred_reason),
        }
        available_metrics = [
            name for name, metric in metrics.items() if metric["status"] == "AVAILABLE"
        ]

        return {
            "data": {
                "symbol": stock.symbol,
                "market": market,
                "financial_basis": basis,
                "metrics": metrics,
                "provenance": {
                    "quote_provider": quote.provider if quote else "finnhub",
                    "financial_provider": self.FINANCIAL_PROVIDER,
                },
            },
            "meta": {
                "available": bool(quote or basis),
                "available_metrics": available_metrics,
                "unavailable_metrics": [
                    name for name, metric in metrics.items() if metric["status"] != "AVAILABLE"
                ],
            },
        }
