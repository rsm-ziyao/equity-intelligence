"""Read-side business logic for stock and price API requests."""

from datetime import date, datetime, time, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..api.exceptions import DatabaseUnavailableError, InvalidDateRangeError, StockNotFoundError
from ..repositories.stock_repository import StockPriceRepository, StockRepository


class StockService:
    """Coordinate stock lookups without exposing persistence details to routes."""

    @staticmethod
    def _price_to_dict(price) -> dict:
        return {
            "timestamp": price.timestamp,
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
            "provider": price.provider,
            "provider_timestamp": price.provider_timestamp,
            "retrieved_at": price.retrieved_at,
        }

    def get_stock(self, session: Session, symbol: str) -> dict:
        normalized_symbol = symbol.upper()
        try:
            stock = StockRepository.get_by_symbol(session, normalized_symbol)
            if stock is None:
                raise StockNotFoundError(normalized_symbol)
            latest = StockPriceRepository.get_latest_for_stock(session, stock.id)
        except StockNotFoundError:
            raise
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError() from exc

        return {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "latest_price": self._price_to_dict(latest) if latest else None,
        }

    def get_prices(
        self,
        session: Session,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> dict:
        normalized_symbol = symbol.upper()
        if start_date and end_date and end_date < start_date:
            raise InvalidDateRangeError(start_date, end_date)

        start_datetime = datetime.combine(start_date, time.min) if start_date else None
        end_datetime_exclusive = (
            datetime.combine(end_date + timedelta(days=1), time.min)
            if end_date
            else None
        )

        try:
            stock = StockRepository.get_by_symbol(session, normalized_symbol)
            if stock is None:
                raise StockNotFoundError(normalized_symbol)
            prices = StockPriceRepository.get_for_stock(
                session,
                stock.id,
                start_datetime=start_datetime,
                end_datetime_exclusive=end_datetime_exclusive,
                limit=limit,
            )
        except StockNotFoundError:
            raise
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError() from exc

        return {
            "data": [self._price_to_dict(price) for price in prices],
            "meta": {
                "symbol": stock.symbol,
                "count": len(prices),
                "limit": limit,
                "start_date": start_date,
                "end_date": end_date,
            },
        }
