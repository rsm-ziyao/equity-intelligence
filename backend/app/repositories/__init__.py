"""Repositories module for Equity Intelligence backend.

Provides data access objects for Stock and StockPrice operations.
"""

from .stock_repository import StockRepository, StockPriceRepository

__all__ = [
    "StockRepository",
    "StockPriceRepository",
]
