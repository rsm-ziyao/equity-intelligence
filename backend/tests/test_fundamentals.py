from datetime import datetime
from decimal import Decimal

from app.fundamentals.normalize import normalize_rows
from app.repositories.fundamentals_repository import FundamentalsRepository
from app.repositories.stock_repository import StockRepository
from app.services.fundamentals_service import FundamentalsService
from app.services.financial_trend_service import FinancialTrendService


def rows(period_type="quarterly"):
    return [{"_period_type": period_type, "fiscalDateEnding": "2026-06-30", "reportedCurrency": "USD", "totalRevenue": "100", "grossProfit": "40", "operatingIncome": "20", "netIncome": "10", "dilutedEPS": "1.25"}]


def period_rows(period_type, year, quarter=None, revenue="100", net_income="10", eps="1", ocf="70", capex="-20"):
    month_day = "06-30" if period_type == "annual" else ("03-31", "06-30", "09-30", "12-31")[quarter - 1]
    row = {"_period_type": period_type, "fiscalDateEnding": f"{year}-{month_day}", "fiscalYear": year, "reportedCurrency": "USD", "totalRevenue": revenue, "grossProfit": str(Decimal(revenue) * Decimal("0.4")), "operatingIncome": str(Decimal(revenue) * Decimal("0.2")), "netIncome": net_income, "dilutedEPS": eps, "operatingCashflow": ocf, "capitalExpenditures": capex, "cashAndCashEquivalentsAtCarryingValue": "50", "totalDebt": "30"}
    if quarter is not None:
        row["fiscalQuarter"] = quarter
    return row


def persist_period(test_db_session, symbol, period_type, year, quarter=None, **values):
    stock = StockRepository.get_or_create(test_db_session, symbol)
    row = period_rows(period_type, year, quarter, **values)
    FundamentalsRepository.upsert_records(
        test_db_session,
        stock.id,
        normalize_rows([row], symbol, "alphavantage", "income"),
        normalize_rows([row], symbol, "alphavantage", "cash_flow"),
        normalize_rows([row], symbol, "alphavantage", "balance"),
    )
    return stock


def test_normalization_preserves_missing_and_malformed_values():
    result = normalize_rows([{**rows()[0], "grossProfit": "not-a-number", "operatingIncome": ""}], "aapl", "alphavantage", "income", datetime.utcnow())
    assert result[0].period.symbol == "AAPL"
    assert result[0].gross_profit is None
    assert result[0].operating_income is None
    assert result[0].revenue == Decimal("100")


def test_cash_flow_sign_and_derived_metrics_are_null_safe(test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AMD")
    income = normalize_rows(rows(), "AMD", "alphavantage", "income")
    cash = normalize_rows([{**rows()[0], "operatingCashflow": "70", "capitalExpenditures": "-20"}], "AMD", "alphavantage", "cash_flow")
    balance = normalize_rows([{**rows()[0], "cashAndCashEquivalentsAtCarryingValue": "50", "totalDebt": "30"}], "AMD", "alphavantage", "balance")
    FundamentalsRepository.upsert_records(test_db_session, stock.id, income, cash, balance)
    result = FundamentalsService().get(test_db_session, "AMD")
    snapshot = result["data"]["financials"]["latest_quarterly"]
    assert snapshot["capital_expenditures"] == Decimal("20")
    assert snapshot["free_cash_flow"] == Decimal("50")
    assert snapshot["gross_margin"] == Decimal("0.4")


def test_repeated_ingestion_does_not_duplicate_periods(test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "MSFT")
    income = normalize_rows(rows("annual"), "MSFT", "alphavantage", "income")
    FundamentalsRepository.upsert_records(test_db_session, stock.id, income, [], [])
    FundamentalsRepository.upsert_records(test_db_session, stock.id, income, [], [])
    assert len(FundamentalsRepository.periods(test_db_session, stock.id, "annual", 10)) == 1


def test_history_is_ordered_and_filters_type_provider_and_limit(test_db_session):
    stock = persist_period(test_db_session, "AAPL", "annual", 2022)
    persist_period(test_db_session, "AAPL", "annual", 2023)
    persist_period(test_db_session, "AAPL", "annual", 2024)
    persist_period(test_db_session, "AAPL", "quarterly", 2024, 1)
    assert [p.fiscal_year for p in reversed(FundamentalsRepository.get_financial_history(test_db_session, stock.id, "annual", 2))] == [2023, 2024]
    assert len(FundamentalsRepository.get_latest_quarterly_periods(test_db_session, stock.id, 8)) == 1
    assert FundamentalsRepository.get_financial_history(test_db_session, stock.id, "annual", 8, "other") == []


def test_annual_growth_and_metric_coverage(test_db_session):
    persist_period(test_db_session, "AAPL", "annual", 2023, revenue="100", net_income="-10", eps="-1", ocf="60", capex="-10")
    persist_period(test_db_session, "AAPL", "annual", 2024, revenue="125", net_income="-5", eps="-0.5", ocf="80", capex="-20")
    result = FinancialTrendService().get_history(test_db_session, "AAPL", "annual", 8)
    periods = result["data"]["periods"]
    assert [period["fiscal_year"] for period in periods] == [2023, 2024]
    assert periods[-1]["revenue_yoy_growth"] == Decimal("0.25")
    assert periods[-1]["net_income_yoy_growth"] == Decimal("0.5")
    assert periods[-1]["eps_yoy_growth"] == Decimal("0.5")
    assert periods[-1]["free_cash_flow_yoy_growth"] == Decimal("0.2")
    assert result["meta"]["metric_coverage"]["revenue"] == 2
    assert result["data"]["provenance"]["provider"] == "alphavantage"


def test_quarterly_growth_matches_same_quarter_and_rejects_sign_change(test_db_session):
    persist_period(test_db_session, "AMD", "quarterly", 2023, 1, revenue="100", net_income="-10")
    persist_period(test_db_session, "AMD", "quarterly", 2023, 2, revenue="100", net_income="10")
    persist_period(test_db_session, "AMD", "quarterly", 2024, 1, revenue="120", net_income="5")
    persist_period(test_db_session, "AMD", "quarterly", 2024, 2, revenue="120", net_income="-15")
    periods = FinancialTrendService().get_history(test_db_session, "AMD", "quarterly", 8)["data"]["periods"]
    q1, q2 = periods[-2:]
    assert q1["revenue_yoy_growth"] == Decimal("0.2")
    assert q2["revenue_yoy_growth"] == Decimal("0.2")
    assert q1["net_income_yoy_growth"] is None
    assert q2["net_income_yoy_growth"] is None


def test_zero_denominator_non_consecutive_year_and_null_safe_records(test_db_session):
    persist_period(test_db_session, "MSFT", "annual", 2022, revenue="0", net_income="0", ocf="70", capex="-20")
    persist_period(test_db_session, "MSFT", "annual", 2024, revenue="100", net_income="10", ocf="70", capex="-20")
    stock = StockRepository.get_or_create(test_db_session, "MSFT")
    incomplete = normalize_rows([period_rows("annual", 2025, revenue="100", net_income="10", ocf="", capex="")], "MSFT", "alphavantage", "income")
    FundamentalsRepository.upsert_records(test_db_session, stock.id, incomplete, [], [])
    result = FinancialTrendService().get_history(test_db_session, "MSFT", "annual", 8)
    records = result["data"]["periods"]
    assert records[-1]["free_cash_flow"] is None
    assert records[-1]["gross_margin"] is not None
    assert records[1]["revenue_yoy_growth"] is None
    assert result["meta"]["missing_periods"]


def test_existing_stock_without_fundamentals_is_unavailable(test_db_session):
    StockRepository.get_or_create(test_db_session, "NVDA")
    result = FinancialTrendService().get_history(test_db_session, "NVDA", "annual", 8)
    assert result["data"] is None
    assert result["meta"]["available"] is False
