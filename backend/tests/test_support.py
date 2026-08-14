from app.fundamentals.normalize import normalize_rows
from app.repositories.fundamentals_repository import FundamentalsRepository


def persist_financial_period(session, stock_id, period_type, year, quarter=None):
    month_day = "06-30" if period_type == "annual" else ("03-31", "06-30", "09-30", "12-31")[quarter - 1]
    row = {"_period_type": period_type, "fiscalDateEnding": f"{year}-{month_day}", "fiscalYear": year, "reportedCurrency": "USD", "totalRevenue": "100", "grossProfit": "40", "operatingIncome": "20", "netIncome": "10", "dilutedEPS": "1", "operatingCashflow": "70", "capitalExpenditures": "-20", "cashAndCashEquivalentsAtCarryingValue": "50", "totalDebt": "30"}
    if quarter is not None:
        row["fiscalQuarter"] = quarter
    FundamentalsRepository.upsert_records(session, stock_id, normalize_rows([row], "TEST", "alphavantage", "income"), normalize_rows([row], "TEST", "alphavantage", "cash_flow"), normalize_rows([row], "TEST", "alphavantage", "balance"))
