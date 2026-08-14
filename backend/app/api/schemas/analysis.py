from typing import Literal

from pydantic import BaseModel

from .fundamentals import FundamentalsProvenance


SignalStatus = str


class AnalysisBasis(BaseModel):
    period_type: str | None = None
    latest_period: str | None = None
    comparison_period: str | None = None
    periods_used: int


class AnalysisSignal(BaseModel):
    signal: str
    status: SignalStatus
    available: bool
    evidence: list[str]
    basis: AnalysisBasis
    metrics_used: list[str]
    metrics_missing: list[str]


class FinancialAnalysisSignals(BaseModel):
    growth: AnalysisSignal
    profitability: AnalysisSignal
    cash_flow: AnalysisSignal
    margins: AnalysisSignal
    financial_strength: AnalysisSignal
    overall: AnalysisSignal


class FinancialAnalysisData(BaseModel):
    symbol: str
    company_name: str | None = None
    period_type: Literal["annual", "quarterly"]
    signals: FinancialAnalysisSignals
    provenance: FundamentalsProvenance


class FinancialAnalysisMeta(BaseModel):
    available: bool
    periods_used: int
    missing_metrics: list[str]
    data_availability: dict[str, int]
    reason: str | None = None


class FinancialAnalysisResponse(BaseModel):
    data: FinancialAnalysisData | None
    meta: FinancialAnalysisMeta
