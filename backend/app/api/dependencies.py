"""FastAPI dependencies for API routes."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from ..database.connection import get_session
from ..services.stock_service import StockService


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()


def get_stock_service() -> StockService:
    return StockService()
