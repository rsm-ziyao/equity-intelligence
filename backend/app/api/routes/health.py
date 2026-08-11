"""Health check route."""

from fastapi import APIRouter

from ...database.connection import check_db_connection
from ...api.exceptions import DatabaseUnavailableError
from ..schemas.common import ApiResponse
from ..schemas.health import HealthData


router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthData])
def health_check() -> ApiResponse[HealthData]:
    try:
        check_db_connection()
    except Exception as exc:
        raise DatabaseUnavailableError() from exc

    return ApiResponse(
        data=HealthData(
            status="healthy",
            service="equity-intelligence-api",
            version="0.1.0",
            database="healthy",
        ),
        meta={},
    )
