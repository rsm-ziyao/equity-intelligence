"""SQLAlchemy ORM models for Equity Intelligence.

Tables:
- Stock: Master registry of stocks (symbol, company_name)
- StockPrice: Time-series price data (OHLCV, provider, timestamps)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index, Numeric
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Stock(Base):
    """Master stock registry.
    
    Attributes:
        id: Primary key
        symbol: Stock ticker (e.g., "AAPL"), unique
        company_name: Company full name (optional)
        created_at: Insertion timestamp
        updated_at: Last modification timestamp
    """
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to prices
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    financial_periods = relationship("FinancialPeriod", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Stock id={self.id} symbol={self.symbol}>"


class StockPrice(Base):
    """Time-series stock price data (OHLCV).
    
    Attributes:
        id: Primary key
        stock_id: Foreign key to Stock
        timestamp: ISO timestamp of the price (supports intraday and daily)
        open, high, low, close: Price in USD (DECIMAL in DB)
        volume: Share volume traded
        provider: Data provider identifier (e.g., "alpha_vantage")
        provider_timestamp: Raw timestamp from provider
        retrieved_at: When we fetched from provider
        created_at: When we inserted into our database
        stock: Relationship to Stock
        
    Uniqueness:
        Constraint (stock_id, provider, provider_timestamp) ensures:
        - Same provider + same timestamp = rejected (duplicate prevention)
        - Different providers + same timestamp = allowed
        - Same provider + different timestamp = allowed (intraday updates)
    """
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Price data (stored as DECIMAL in database for precision)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Provenance
    provider = Column(String(50), nullable=False)  # e.g., "alpha_vantage"
    provider_timestamp = Column(String(50), nullable=False)  # Raw string from provider
    retrieved_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    # Uniqueness constraint: prevent same provider + same timestamp for same stock
    __table_args__ = (
        UniqueConstraint("stock_id", "provider", "provider_timestamp", name="uq_stock_provider_timestamp"),
        Index("idx_stock_timestamp", "stock_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<StockPrice id={self.id} stock_id={self.stock_id} timestamp={self.timestamp} provider={self.provider}>"


class FinancialPeriod(Base):
    __tablename__ = "financial_periods"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    fiscal_period_type = Column(String(20), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=False, index=True)
    filing_date = Column(DateTime, nullable=True)
    provider_period_key = Column(String(100), nullable=True)
    provider_effective_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    stock = relationship("Stock", back_populates="financial_periods")
    income_statement = relationship("IncomeStatementPeriod", back_populates="period", uselist=False, cascade="all, delete-orphan")
    cash_flow = relationship("CashFlowPeriod", back_populates="period", uselist=False, cascade="all, delete-orphan")
    balance_sheet = relationship("BalanceSheetPeriod", back_populates="period", uselist=False, cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("stock_id", "provider", "fiscal_period_type", "period_end", name="uq_financial_period_key"), Index("idx_financial_period_stock_type_end", "stock_id", "fiscal_period_type", "period_end"))


class IncomeStatementPeriod(Base):
    __tablename__ = "income_statement_periods"
    period_id = Column(Integer, ForeignKey("financial_periods.id", ondelete="CASCADE"), primary_key=True, index=True)
    revenue = Column(Numeric(24, 6), nullable=True)
    gross_profit = Column(Numeric(24, 6), nullable=True)
    operating_income = Column(Numeric(24, 6), nullable=True)
    net_income = Column(Numeric(24, 6), nullable=True)
    diluted_eps = Column(Numeric(24, 6), nullable=True)
    currency = Column(String(20), nullable=True)
    unit = Column(String(50), nullable=True)
    period = relationship("FinancialPeriod", back_populates="income_statement")


class CashFlowPeriod(Base):
    __tablename__ = "cash_flow_periods"
    period_id = Column(Integer, ForeignKey("financial_periods.id", ondelete="CASCADE"), primary_key=True, index=True)
    operating_cash_flow = Column(Numeric(24, 6), nullable=True)
    capital_expenditures = Column(Numeric(24, 6), nullable=True)
    currency = Column(String(20), nullable=True)
    unit = Column(String(50), nullable=True)
    period = relationship("FinancialPeriod", back_populates="cash_flow")


class BalanceSheetPeriod(Base):
    __tablename__ = "balance_sheet_periods"
    period_id = Column(Integer, ForeignKey("financial_periods.id", ondelete="CASCADE"), primary_key=True, index=True)
    cash_and_cash_equivalents = Column(Numeric(24, 6), nullable=True)
    total_debt = Column(Numeric(24, 6), nullable=True)
    currency = Column(String(20), nullable=True)
    unit = Column(String(50), nullable=True)
    period = relationship("FinancialPeriod", back_populates="balance_sheet")
