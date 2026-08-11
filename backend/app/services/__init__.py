"""Services module for Equity Intelligence backend.

Provides business logic services (ingestion, etc.).
"""

from .ingestion_service import IngestionService

__all__ = [
    "IngestionService",
]
