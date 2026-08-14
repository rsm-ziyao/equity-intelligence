import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_db_session
from app.main import app
from app.repositories.stock_repository import StockRepository
from test_support import persist_financial_period


@pytest.fixture
def api_client(test_db_session):
    def override_db_session():
        yield test_db_session
    app.dependency_overrides[get_db_session] = override_db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_history_api_default_is_annual_and_returns_oldest_first(api_client, test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AAPL", "Apple Inc.")
    for year in (2022, 2023, 2024):
        persist_financial_period(test_db_session, stock.id, "annual", year)
    response = api_client.get("/api/v1/stocks/AAPL/fundamentals/history")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["period_type"] == "annual"
    assert [period["fiscal_year"] for period in body["data"]["periods"]] == [2022, 2023, 2024]
    assert body["meta"]["requested_limit"] == 8


def test_history_api_quarterly_limit_and_unavailable(api_client, test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AMD")
    for quarter in (1, 2, 3):
        persist_financial_period(test_db_session, stock.id, "quarterly", 2024, quarter)
    response = api_client.get("/api/v1/stocks/AMD/fundamentals/history", params={"period_type": "quarterly", "limit": 2})
    assert response.status_code == 200
    assert len(response.json()["data"]["periods"]) == 2
    StockRepository.get_or_create(test_db_session, "NVDA")
    unavailable = api_client.get("/api/v1/stocks/NVDA/fundamentals/history")
    assert unavailable.status_code == 200
    assert unavailable.json()["data"] is None
    assert unavailable.json()["meta"]["available"] is False


@pytest.mark.parametrize("params", [{"period_type": "monthly"}, {"limit": 0}, {"limit": 21}, {"limit": "bad"}])
def test_history_api_rejects_invalid_parameters(api_client, params):
    assert api_client.get("/api/v1/stocks/AAPL/fundamentals/history", params=params).status_code == 422


def test_history_api_unknown_stock_and_database_error(api_client, test_db_session, monkeypatch):
    response = api_client.get("/api/v1/stocks/UNKNOWN/fundamentals/history")
    assert response.status_code == 404

    StockRepository.get_or_create(test_db_session, "AAPL")

    from app.repositories import fundamentals_repository
    monkeypatch.setattr(fundamentals_repository.FundamentalsRepository, "get_financial_history", lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("down")))
    response = api_client.get("/api/v1/stocks/AAPL/fundamentals/history")
    assert response.status_code == 503
