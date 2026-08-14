from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db_session, get_fundamentals_service
from ..schemas.fundamentals import FundamentalsResponse
from ...services.fundamentals_service import FundamentalsService
from ...api.exceptions import StockNotFoundError

router = APIRouter(prefix="/stocks", tags=["fundamentals"])
@router.get("/{symbol}/fundamentals", response_model=FundamentalsResponse)
def get_fundamentals(symbol: Annotated[str, Path(min_length=1, max_length=10, pattern=r"^[A-Za-z][A-Za-z0-9.-]{0,9}$")], period_type: str = Query("latest"), session: Session = Depends(get_db_session), service: FundamentalsService = Depends(get_fundamentals_service)):
    try: result = service.get(session, symbol, period_type.lower())
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FundamentalsResponse(**result)
