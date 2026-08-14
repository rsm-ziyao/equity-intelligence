from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db_session, get_fundamentals_service, get_financial_trend_service
from ..schemas.fundamentals import FinancialHistoryResponse, FundamentalsResponse
from ...services.fundamentals_service import FundamentalsService
from ...services.financial_trend_service import FinancialTrendService
from ...api.exceptions import StockNotFoundError

router = APIRouter(prefix="/stocks", tags=["fundamentals"])
@router.get("/{symbol}/fundamentals", response_model=FundamentalsResponse)
def get_fundamentals(symbol: Annotated[str, Path(min_length=1, max_length=10, pattern=r"^[A-Za-z][A-Za-z0-9.-]{0,9}$")], period_type: str = Query("latest"), session: Session = Depends(get_db_session), service: FundamentalsService = Depends(get_fundamentals_service)):
    try: result = service.get(session, symbol, period_type.lower())
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FundamentalsResponse(**result)

@router.get("/{symbol}/fundamentals/history", response_model=FinancialHistoryResponse)
def get_financial_history(
    symbol: Annotated[str, Path(min_length=1, max_length=10, pattern=r"^[A-Za-z][A-Za-z0-9.-]{0,9}$")],
    period_type: str = Query("annual"),
    limit: int = Query(8, ge=1, le=20),
    session: Session = Depends(get_db_session),
    service: FinancialTrendService = Depends(get_financial_trend_service),
):
    try:
        result = service.get_history(session, symbol, period_type.lower(), limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FinancialHistoryResponse(**result)
