"""API tests for stock and persisted price reads."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_session
from app.main import app
from app.repositories.stock_repository import StockPriceRepository, StockRepository


@pytest.fixture
def api_client(test_db_session):
    def override_db_session():
        yield test_db_session

    app.dependency_overrides[get_db_session] = override_db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def seed_aapl(test_db_session):
    stock = StockRepository.get_or_create(
        test_db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    for timestamp, close in (
        (datetime(2026, 8, 10, 14, 30), 150.0),
        (datetime(2026, 8, 11, 14, 30), 151.0),
    ):
        StockPriceRepository.create(
            test_db_session,
            stock_id=stock.id,
            timestamp=timestamp,
            open_price=close - 1,
            high=close + 1,
            low=close - 2,
            close=close,
            volume=1000,
            provider="alpha_vantage",
            provider_timestamp=timestamp.isoformat(),
            retrieved_at=datetime(2026, 8, 11, 15, 0),
        )
    return stock


def test_health_endpoint(api_client, monkeypatch):
    from app.api.routes import health as health_routes

    monkeypatch.setattr(health_routes, "check_db_connection", lambda: True)
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["database"] == "healthy"


def test_aapl_stock_endpoint(api_client, test_db_session):
    seed_aapl(test_db_session)

    response = api_client.get("/api/v1/stocks/AAPL")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["symbol"] == "AAPL"
    assert body["company_name"] == "Apple Inc."
    assert body["latest_price"]["close"] == 151.0
    assert body["latest_price"]["provider"] == "alpha_vantage"


def test_msft_stock_and_prices_use_the_same_symbol_agnostic_behavior(
    api_client,
    test_db_session,
):
    stock = StockRepository.get_or_create(
        test_db_session,
        symbol="MSFT",
        company_name="Microsoft Corporation",
    )
    StockPriceRepository.create(
        test_db_session,
        stock_id=stock.id,
        timestamp=datetime(2026, 8, 11, 14, 30),
        open_price=400.0,
        high=405.0,
        low=399.0,
        close=403.0,
        volume=2000,
        provider="alpha_vantage",
        provider_timestamp="2026-08-11T14:30:00",
        retrieved_at=datetime(2026, 8, 11, 15, 0),
    )

    stock_response = api_client.get("/api/v1/stocks/MSFT")
    prices_response = api_client.get("/api/v1/stocks/MSFT/prices")

    assert stock_response.status_code == 200
    assert stock_response.json()["data"]["symbol"] == "MSFT"
    assert stock_response.json()["data"]["latest_price"]["close"] == 403.0
    assert prices_response.status_code == 200
    assert prices_response.json()["meta"]["symbol"] == "MSFT"
    assert len(prices_response.json()["data"]) == 1


def test_aapl_historical_prices_endpoint(api_client, test_db_session):
    seed_aapl(test_db_session)

    response = api_client.get(
        "/api/v1/stocks/AAPL/prices",
        params={"start_date": "2026-08-10", "end_date": "2026-08-11", "limit": 100},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["count"] == 2
    assert [item["close"] for item in body["data"]] == [150.0, 151.0]
    assert body["data"][0]["timestamp"] < body["data"][1]["timestamp"]


def test_unknown_stock_returns_404(api_client):
    response = api_client.get("/api/v1/stocks/MSFT")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STOCK_NOT_FOUND"


def test_invalid_date_range_returns_422(api_client, test_db_session):
    seed_aapl(test_db_session)

    response = api_client.get(
        "/api/v1/stocks/AAPL/prices",
        params={"start_date": "2026-08-12", "end_date": "2026-08-11"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


@pytest.mark.parametrize("limit", ["0", "1001", "not-an-int"])
def test_invalid_limit_returns_422(api_client, limit):
    response = api_client.get("/api/v1/stocks/AAPL/prices", params={"limit": limit})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_existing_stock_with_no_matching_prices_returns_empty_data(api_client, test_db_session):
    StockRepository.get_or_create(test_db_session, symbol="AAPL", company_name="Apple Inc.")

    response = api_client.get(
        "/api/v1/stocks/AAPL/prices",
        params={"start_date": "2026-08-01", "end_date": "2026-08-02"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["count"] == 0
