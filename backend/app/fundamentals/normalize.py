from __future__ import annotations
from datetime import datetime
from typing import Any
from .models import BalanceSheetRecord, CashFlowRecord, FinancialPeriod, IncomeStatementRecord, first, parse_date, parse_decimal

def _period(row: dict[str, Any], symbol: str, provider: str, retrieved_at: datetime) -> FinancialPeriod | None:
    end = parse_date(first(row, "fiscalDateEnding", "period_end"))
    if end is None: return None
    kind = str(row.get("_period_type") or "quarterly").lower()
    year = end.year
    quarter = None if kind == "annual" else ((end.month - 1) // 3 + 1)
    return FinancialPeriod(symbol, provider, kind, year, quarter, parse_date(row.get("periodStart")), end, parse_date(first(row, "reportedDate", "filing_date")), first(row, "fiscalDateEnding", "provider_period_key"), parse_date(first(row, "reportedDate", "provider_effective_at")), retrieved_at)

def normalize_rows(rows: list[dict[str, Any]], symbol: str, provider: str, kind: str, retrieved_at: datetime | None = None) -> list[Any]:
    retrieved = retrieved_at or datetime.utcnow(); output = []
    for row in rows:
        period = _period(row, symbol.upper(), provider, retrieved)
        if period is None: continue
        unit = first(row, "reportedCurrency", "currency", "unit")
        currency = first(row, "reportedCurrency", "currency")
        if kind == "income":
            output.append(IncomeStatementRecord(period, parse_decimal(first(row, "totalRevenue", "revenue")), parse_decimal(first(row, "grossProfit", "gross_profit")), parse_decimal(first(row, "operatingIncome", "operating_income")), parse_decimal(first(row, "netIncome", "net_income", "netIncomeApplicableToCommonShares")), parse_decimal(first(row, "dilutedEPS", "diluted_eps")), currency, unit))
        elif kind == "cash_flow":
            # Alpha Vantage reports capitalExpenditures as a negative cash outflow.
            # The canonical model stores capex as a positive spend so FCF is OCF - capex.
            capex = parse_decimal(first(row, "capitalExpenditures", "capital_expenditures"))
            output.append(CashFlowRecord(period, parse_decimal(first(row, "operatingCashflow", "operatingCashFlow", "operating_cash_flow")), abs(capex) if capex is not None else None, currency, unit))
        else:
            cash = parse_decimal(first(row, "cashAndCashEquivalentsAtCarryingValue", "cashAndCashEquivalents", "cash_and_cash_equivalents"))
            debt = parse_decimal(first(row, "totalDebt", "total_debt"))
            output.append(BalanceSheetRecord(period, cash, debt, currency, unit))
    return output
