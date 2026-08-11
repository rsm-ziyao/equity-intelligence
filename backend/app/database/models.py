"""SQLAlchemy ORM models for Equity Intelligence.

Tables:
- Stock: Master registry of stocks (symbol, company_name)
- StockPrice: Time-series price data (OHLCV, provider, timestamps)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index
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
