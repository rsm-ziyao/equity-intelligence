"""Stock and historical price routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_stock_service
from ..schemas.common import ApiResponse
from ..schemas.stocks import StockPricesMeta, StockPricesResponse, StockResponse
from ...services.stock_service import StockService


router = APIRouter(prefix="/stocks", tags=["stocks"])
SymbolPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z][A-Z0-9.-]{0,9}$",
        description="Uppercase stock symbol, such as AAPL or BRK.B",
    ),
]


@router.get("/{symbol}", response_model=ApiResponse[StockResponse])
def get_stock(
    symbol: SymbolPath,
    session: Session = Depends(get_db_session),
    service: StockService = Depends(get_stock_service),
) -> ApiResponse[StockResponse]:
    stock = service.get_stock(session, symbol)
    return ApiResponse(data=StockResponse.model_validate(stock), meta={})


@router.get("/{symbol}/prices", response_model=StockPricesResponse)
def get_stock_prices(
    symbol: SymbolPath,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    session: Session = Depends(get_db_session),
    service: StockService = Depends(get_stock_service),
) -> StockPricesResponse:
    prices = service.get_prices(
        session,
        symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return StockPricesResponse(
        data=[price for price in prices["data"]],
        meta=StockPricesMeta(**prices["meta"]),
    )
