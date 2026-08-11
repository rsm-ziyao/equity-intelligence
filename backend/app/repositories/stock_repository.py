"""Repository layer for database operations.

Repositories follow the Data Access Object pattern:
- Encapsulate database queries
- Provide clean interface to business logic
- Enable testing via mocking
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database.models import Stock, StockPrice


class StockRepository:
    """CRUD operations for Stock records."""

    @staticmethod
    def get_or_create(session: Session, symbol: str, company_name: Optional[str] = None) -> Stock:
        """Get existing stock by symbol or create if not found.
        
        Args:
            session: SQLAlchemy session
            symbol: Stock ticker (e.g., "AAPL")
            company_name: Optional company name
            
        Returns:
            Stock record (new or existing)
        """
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            return stock
        
        stock = Stock(symbol=symbol, company_name=company_name)
        session.add(stock)
        session.commit()
        return stock

    @staticmethod
    def get_by_symbol(session: Session, symbol: str) -> Optional[Stock]:
        """Retrieve stock by symbol.
        
        Args:
            session: SQLAlchemy session
            symbol: Stock ticker
            
        Returns:
            Stock record or None if not found
        """
        return session.query(Stock).filter(Stock.symbol == symbol).first()

    @staticmethod
    def get_all(session: Session) -> List[Stock]:
        """Retrieve all stocks.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List of Stock records
        """
        return session.query(Stock).all()


class StockPriceRepository:
    """CRUD operations for StockPrice records."""

    @staticmethod
    def create(
        session: Session,
        stock_id: int,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        provider: str,
        provider_timestamp: str | datetime,
        retrieved_at: datetime,
    ) -> StockPrice:
        """Create a new stock price record.
        
        May raise IntegrityError if uniqueness constraint is violated.
        
        Args:
            session: SQLAlchemy session
            stock_id: Foreign key to Stock
            timestamp: ISO timestamp of price
            open_price: Opening price
            high: Highest price
            low: Lowest price
            close: Closing price
            volume: Volume traded
            provider: Provider identifier (e.g., "alpha_vantage")
            provider_timestamp: Raw timestamp from provider
            retrieved_at: When we fetched from provider
            
        Returns:
            Newly created StockPrice record
            
        Raises:
            IntegrityError: If (stock_id, provider, provider_timestamp) already exists
        """
        price = StockPrice(
            stock_id=stock_id,
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            provider=provider,
            # Bar validation canonicalizes timestamps to datetime values, while
            # the database keeps the provider's timestamp as text for stable
            # duplicate keys and provider-specific formats.
            provider_timestamp=str(provider_timestamp),
            retrieved_at=retrieved_at,
        )
        session.add(price)
        session.commit()
        return price

    @staticmethod
    def get_by_stock_and_provider_timestamp(
        session: Session,
        stock_id: int,
        provider: str,
        provider_timestamp: str | datetime,
    ) -> Optional[StockPrice]:
        """Check if price already exists for stock/provider/timestamp combination.
        
        Args:
            session: SQLAlchemy session
            stock_id: Stock ID
            provider: Provider identifier
            provider_timestamp: Raw timestamp from provider
            
        Returns:
            StockPrice record or None if not found
        """
        return session.query(StockPrice).filter(
            StockPrice.stock_id == stock_id,
            StockPrice.provider == provider,
            StockPrice.provider_timestamp == str(provider_timestamp),
        ).first()

    @staticmethod
    def get_latest_by_stock(session: Session, stock_id: int, limit: int = 100) -> List[StockPrice]:
        """Retrieve latest price records for a stock.
        
        Args:
            session: SQLAlchemy session
            stock_id: Stock ID
            limit: Maximum number of records to return
            
        Returns:
            List of latest StockPrice records (descending by timestamp)
        """
        return session.query(StockPrice).filter(
            StockPrice.stock_id == stock_id
        ).order_by(StockPrice.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_by_stock_and_date_range(
        session: Session,
        stock_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[StockPrice]:
        """Retrieve prices for a stock within a date range.
        
        Args:
            session: SQLAlchemy session
            stock_id: Stock ID
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)
            
        Returns:
            List of StockPrice records (ascending by timestamp)
        """
        return session.query(StockPrice).filter(
            StockPrice.stock_id == stock_id,
            StockPrice.timestamp >= start_date,
            StockPrice.timestamp <= end_date,
        ).order_by(StockPrice.timestamp.asc()).all()
