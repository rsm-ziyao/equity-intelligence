from __future__ import annotations
from sqlalchemy.orm import Session, joinedload
from ..database.models import BalanceSheetPeriod, CashFlowPeriod, FinancialPeriod, IncomeStatementPeriod
from ..repositories.stock_repository import StockRepository

class FundamentalsRepository:
    @staticmethod
    def find_stock(session: Session, symbol: str): return StockRepository.get_by_symbol(session, symbol.upper())
    @staticmethod
    def upsert_period(session: Session, period, stock_id: int) -> tuple[FinancialPeriod, bool]:
        found = session.query(FinancialPeriod).filter_by(stock_id=stock_id, provider=period.provider, fiscal_period_type=period.fiscal_period_type, period_end=period.period_end).first()
        created = found is None
        if found is None:
            found = FinancialPeriod(stock_id=stock_id)
            session.add(found)
        for field in ("provider", "fiscal_period_type", "fiscal_year", "fiscal_quarter", "period_start", "period_end", "filing_date", "provider_period_key", "provider_effective_at", "retrieved_at"):
            setattr(found, field, getattr(period, field))
        return found, created
    @staticmethod
    def upsert_records(session: Session, stock_id: int, income, cash_flow, balance) -> dict[str, int]:
        stats = {"created": 0, "updated": 0, "skipped": 0}; all_records = [(income, IncomeStatementPeriod, ("revenue", "gross_profit", "operating_income", "net_income", "diluted_eps", "currency", "unit")), (cash_flow, CashFlowPeriod, ("operating_cash_flow", "capital_expenditures", "currency", "unit")), (balance, BalanceSheetPeriod, ("cash_and_cash_equivalents", "total_debt", "currency", "unit"))]
        for records, model, fields in all_records:
            for record in records:
                period, created = FundamentalsRepository.upsert_period(session, record.period, stock_id)
                session.flush()
                statement = session.get(model, period.id)
                if statement is None: statement = model(period_id=period.id); session.add(statement); stats["created"] += 1
                else: stats["updated"] += 1
                for field in fields: setattr(statement, field, getattr(record, field))
        session.commit(); return stats
    @staticmethod
    def periods(session: Session, stock_id: int, period_type: str | None = None, limit: int = 1):
        query = session.query(FinancialPeriod).options(joinedload(FinancialPeriod.income_statement), joinedload(FinancialPeriod.cash_flow), joinedload(FinancialPeriod.balance_sheet)).filter_by(stock_id=stock_id)
        if period_type and period_type != "latest": query = query.filter_by(fiscal_period_type=period_type)
        return query.order_by(FinancialPeriod.period_end.desc(), FinancialPeriod.id.desc()).limit(limit if period_type and period_type != "latest" else 100).all()

    @staticmethod
    def get_financial_history(
        session: Session,
        stock_id: int,
        period_type: str,
        limit: int,
        provider: str = "alphavantage",
    ) -> list[FinancialPeriod]:
        """Load persisted financial periods for trend calculations.

        The newest rows are selected efficiently, while the service owns the
        public oldest-to-newest ordering used by charts and API consumers.
        """
        query = (
            session.query(FinancialPeriod)
            .options(
                joinedload(FinancialPeriod.income_statement),
                joinedload(FinancialPeriod.cash_flow),
                joinedload(FinancialPeriod.balance_sheet),
            )
            .filter(
                FinancialPeriod.stock_id == stock_id,
                FinancialPeriod.provider == provider,
                FinancialPeriod.fiscal_period_type == period_type,
            )
            .order_by(FinancialPeriod.period_end.desc(), FinancialPeriod.id.desc())
            .limit(limit)
        )
        return query.all()

    @staticmethod
    def get_latest_annual_periods(
        session: Session, stock_id: int, limit: int = 8, provider: str = "alphavantage"
    ) -> list[FinancialPeriod]:
        return FundamentalsRepository.get_financial_history(session, stock_id, "annual", limit, provider)

    @staticmethod
    def get_all_annual_periods(
        session: Session, stock_id: int, provider: str = "alphavantage"
    ) -> list[FinancialPeriod]:
        return (
            session.query(FinancialPeriod)
            .options(
                joinedload(FinancialPeriod.income_statement),
                joinedload(FinancialPeriod.cash_flow),
                joinedload(FinancialPeriod.balance_sheet),
            )
            .filter(
                FinancialPeriod.stock_id == stock_id,
                FinancialPeriod.provider == provider,
                FinancialPeriod.fiscal_period_type == "annual",
            )
            .order_by(FinancialPeriod.period_end.desc(), FinancialPeriod.id.desc())
            .all()
        )

    @staticmethod
    def get_latest_quarterly_periods(
        session: Session, stock_id: int, limit: int = 8, provider: str = "alphavantage"
    ) -> list[FinancialPeriod]:
        return FundamentalsRepository.get_financial_history(session, stock_id, "quarterly", limit, provider)
