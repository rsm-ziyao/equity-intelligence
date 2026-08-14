from datetime import datetime
from decimal import Decimal

from app.fundamentals.normalize import normalize_rows
from app.repositories.fundamentals_repository import FundamentalsRepository
from app.repositories.stock_repository import StockRepository
from app.services.fundamentals_service import FundamentalsService


def rows(period_type="quarterly"):
    return [{"_period_type": period_type, "fiscalDateEnding": "2026-06-30", "reportedCurrency": "USD", "totalRevenue": "100", "grossProfit": "40", "operatingIncome": "20", "netIncome": "10", "dilutedEPS": "1.25"}]


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
