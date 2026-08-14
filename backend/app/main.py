from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.exceptions import (
    DatabaseUnavailableError,
    InvalidDateRangeError,
    StockNotFoundError,
)
from .api.routes.health import router as health_router
from .api.routes.stocks import router as stocks_router
from .api.routes.quotes import router as quotes_router
from .api.routes.fundamentals import router as fundamentals_router

app = FastAPI(
    title="Equity Intelligence Platform API",
    version="0.1.0",
    description="A minimal backend foundation for research and decision support."
)


app.include_router(health_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(quotes_router, prefix="/api/v1")
app.include_router(fundamentals_router, prefix="/api/v1")


@app.exception_handler(StockNotFoundError)
def stock_not_found_handler(request: Request, exc: StockNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "STOCK_NOT_FOUND",
                "message": str(exc),
                "details": {"symbol": exc.symbol},
            }
        },
    )


@app.exception_handler(InvalidDateRangeError)
def invalid_date_range_handler(request: Request, exc: InvalidDateRangeError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_DATE_RANGE",
                "message": str(exc),
                "details": {
                    "start_date": exc.start_date.isoformat(),
                    "end_date": exc.end_date.isoformat(),
                },
            }
        },
    )


@app.exception_handler(DatabaseUnavailableError)
def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": str(exc),
                "details": {},
            }
        },
    )


@app.exception_handler(RequestValidationError)
def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": {"errors": exc.errors()},
            }
        },
    )
