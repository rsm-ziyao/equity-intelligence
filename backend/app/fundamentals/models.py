from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

def parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "" or value == "None" or value == "null": return None
    try: return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError): return None

def parse_date(value: Any) -> datetime | None:
    if not value: return None
    try: return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError): return None

def first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row: return row[key]
    return None

@dataclass
class FinancialPeriod:
    symbol: str; provider: str; fiscal_period_type: str; fiscal_year: int; fiscal_quarter: int | None
    period_start: datetime | None; period_end: datetime; filing_date: datetime | None
    provider_period_key: str | None; provider_effective_at: datetime | None; retrieved_at: datetime

@dataclass
class IncomeStatementRecord:
    period: FinancialPeriod; revenue: Decimal | None = None; gross_profit: Decimal | None = None; operating_income: Decimal | None = None; net_income: Decimal | None = None; diluted_eps: Decimal | None = None; currency: str | None = None; unit: str | None = None

@dataclass
class CashFlowRecord:
    period: FinancialPeriod; operating_cash_flow: Decimal | None = None; capital_expenditures: Decimal | None = None; currency: str | None = None; unit: str | None = None

@dataclass
class BalanceSheetRecord:
    period: FinancialPeriod; cash_and_cash_equivalents: Decimal | None = None; total_debt: Decimal | None = None; currency: str | None = None; unit: str | None = None
