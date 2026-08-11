"""Database module for Equity Intelligence backend.

Provides:
- Connection management (engine, session)
- ORM models (Stock, StockPrice)
- Schema initialization
- Repository layer for CRUD operations
"""

from .connection import get_session, get_engine, init_db
from .models import Base, Stock, StockPrice

__all__ = [
    "get_session",
    "get_engine",
    "init_db",
    "Base",
    "Stock",
    "StockPrice",
]
