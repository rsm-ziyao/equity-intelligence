from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class FinancialSnapshot(BaseModel):
    period_type: str; fiscal_year: int; fiscal_quarter: int | None = None
    period_start: datetime | None = None; period_end: datetime; filing_date: datetime | None = None
    revenue: Decimal | None = None; gross_profit: Decimal | None = None; operating_income: Decimal | None = None; net_income: Decimal | None = None; diluted_eps: Decimal | None = None
    operating_cash_flow: Decimal | None = None; capital_expenditures: Decimal | None = None; free_cash_flow: Decimal | None = None
    cash_and_cash_equivalents: Decimal | None = None; total_debt: Decimal | None = None
    gross_margin: Decimal | None = None; operating_margin: Decimal | None = None; profit_margin: Decimal | None = None
    currency: str | None = None; unit: str | None = None; provider: str; retrieved_at: datetime

class FinancialTrendPeriod(FinancialSnapshot):
    revenue_yoy_growth: Decimal | None = None
    net_income_yoy_growth: Decimal | None = None
    eps_yoy_growth: Decimal | None = None
    free_cash_flow_yoy_growth: Decimal | None = None

class MissingPeriod(BaseModel):
    label: str
    period_end: datetime
    missing_metrics: list[str]

class FinancialsBlock(BaseModel):
    latest_quarterly: FinancialSnapshot | None = None
    latest_annual: FinancialSnapshot | None = None

class FundamentalsProvenance(BaseModel):
    provider: str; retrieved_at: datetime | None = None; freshness: str

class FundamentalsData(BaseModel):
    symbol: str; company_name: str | None = None; financials: FinancialsBlock; provenance: FundamentalsProvenance

class FundamentalsMeta(BaseModel):
    available: bool; missing_metrics: list[str]; periods_returned: int

class FinancialHistoryData(BaseModel):
    symbol: str; company_name: str | None = None; period_type: str
    periods: list[FinancialTrendPeriod]
    provenance: FundamentalsProvenance

class FinancialHistoryMeta(BaseModel):
    available: bool
    periods_returned: int
    requested_limit: int
    missing_metrics: list[str]
    metric_coverage: dict[str, int]
    missing_periods: list[MissingPeriod]

class FundamentalsResponse(BaseModel):
    data: FundamentalsData | None; meta: FundamentalsMeta

class FinancialHistoryResponse(BaseModel):
    data: FinancialHistoryData | None
    meta: FinancialHistoryMeta
