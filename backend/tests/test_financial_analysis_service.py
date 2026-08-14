from decimal import Decimal

from app.services.financial_analysis_service import FinancialAnalysisService


def period(year, *, revenue_growth=None, net_growth=None, eps_growth=None, fcf_growth=None,
           gross=.4, operating=.2, profit=.1, net_income=100,
           fcf=50, ocf=70, capex=20, cash=100, debt=50):
    return {
        "period_type": "annual", "fiscal_year": year, "fiscal_quarter": None,
        "period_end": None, "revenue_yoy_growth": revenue_growth,
        "net_income_yoy_growth": net_growth, "eps_yoy_growth": eps_growth,
        "free_cash_flow_yoy_growth": fcf_growth, "gross_margin": gross,
        "operating_margin": operating, "profit_margin": profit,
        "net_income": net_income, "free_cash_flow": fcf,
        "operating_cash_flow": ocf, "capital_expenditures": capex,
        "cash_and_cash_equivalents": cash, "total_debt": debt,
    }


def test_growth_classifications_and_evidence():
    assert FinancialAnalysisService.growth([period(2024), period(2025, revenue_growth=Decimal(".5"), net_growth=Decimal("1.6"), eps_growth=Decimal(".3"))])["status"] == "STRONG"
    assert FinancialAnalysisService.growth([period(2025, revenue_growth=Decimal(".08"), net_growth=Decimal(".03"), eps_growth=Decimal("-.02"))])["status"] == "MODERATE"
    assert FinancialAnalysisService.growth([period(2025, revenue_growth=Decimal(".01"), net_growth=Decimal("-.01"), eps_growth=Decimal(".02"))])["status"] == "WEAK"
    assert FinancialAnalysisService.growth([period(2025, revenue_growth=Decimal("-.2"), net_growth=Decimal("-.3"), eps_growth=Decimal("-.15"))])["status"] == "DECLINING"
    result = FinancialAnalysisService.growth([period(2025, revenue_growth=Decimal(".5"))])
    assert result["status"] == "UNAVAILABLE" and result["available"] is False
    assert "Revenue" in result["metrics_used"]


def test_profitability_and_margin_classifications():
    improving = [period(2024), period(2025, gross=.42, operating=.23, profit=.12, net_growth=Decimal(".2"))]
    stable = [period(2024), period(2025, gross=.405, operating=.198, profit=.102)]
    deteriorating = [period(2024), period(2025, gross=.37, operating=.17, profit=.08, net_growth=Decimal("-.3"))]
    assert FinancialAnalysisService.profitability(improving)["status"] == "IMPROVING"
    assert FinancialAnalysisService.profitability(stable)["status"] == "STABLE"
    assert FinancialAnalysisService.profitability(deteriorating)["status"] == "DETERIORATING"
    assert FinancialAnalysisService.margins(improving)["status"] == "EXPANDING"
    assert FinancialAnalysisService.margins(stable)["status"] == "STABLE"
    assert FinancialAnalysisService.margins(deteriorating)["status"] == "CONTRACTING"


def test_margin_four_period_average_does_not_overreact_to_one_period():
    records = [period(2022, gross=.40, operating=.20, profit=.10), period(2023, gross=.40, operating=.20, profit=.10),
               period(2024, gross=.41, operating=.21, profit=.11), period(2025, gross=.40, operating=.20, profit=.10)]
    result = FinancialAnalysisService.margins(records)
    assert result["status"] == "STABLE"
    assert result["basis"]["periods_used"] == 4


def test_cash_flow_sign_safe_classifications():
    assert FinancialAnalysisService.cash_flow([period(2024, fcf=40, ocf=60), period(2025, fcf=-5, ocf=70)])["status"] == "NEGATIVE"
    assert FinancialAnalysisService.cash_flow([period(2024, fcf=40, ocf=60), period(2025, fcf=60, ocf=80)])["status"] == "IMPROVING"
    assert FinancialAnalysisService.cash_flow([period(2024, fcf=100, ocf=120), period(2025, fcf=70, ocf=100)])["status"] == "WEAKENING"
    result = FinancialAnalysisService.cash_flow([period(2024, fcf=-20, ocf=40), period(2025, fcf=10, ocf=60)])
    assert result["status"] == "IMPROVING"
    assert any("changed from" in line for line in result["evidence"])


def test_financial_strength_and_composite():
    healthy = FinancialAnalysisService.financial_strength([period(2025, cash=100, debt=50, ocf=20, fcf=10)])
    mixed = FinancialAnalysisService.financial_strength([period(2025, cash=100, debt=50, ocf=-2, fcf=10)])
    weak = FinancialAnalysisService.financial_strength([period(2025, cash=20, debt=50, ocf=-2, fcf=-5)])
    assert healthy["status"] == "HEALTHY"
    assert mixed["status"] == "MIXED"
    assert weak["status"] == "WEAK"
    signals = [
        {"signal": "GROWTH", "status": "STRONG", "available": True},
        {"signal": "PROFITABILITY", "status": "IMPROVING", "available": True},
        {"signal": "CASH_FLOW", "status": "STABLE", "available": True},
        {"signal": "MARGINS", "status": "CONTRACTING", "available": True},
    ]
    assert FinancialAnalysisService.overall(signals, [period(2025)])["status"] == "POSITIVE"
    signals[0]["status"] = "DECLINING"
    assert FinancialAnalysisService.overall(signals, [period(2025)])["status"] == "MIXED"
    signals[1]["status"] = "DETERIORATING"
    signals[2]["status"] = "WEAKENING"
    assert FinancialAnalysisService.overall(signals, [period(2025)])["status"] == "NEGATIVE"
    assert FinancialAnalysisService.overall([{**signal, "available": False, "status": "UNAVAILABLE"} for signal in signals], [period(2025)])["status"] == "UNAVAILABLE"
