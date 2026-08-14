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
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_analysis_endpoint_contract_and_defaults(api_client, test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AAPL", "Apple Inc.")
    persist_financial_period(test_db_session, stock.id, "annual", 2024)
    persist_financial_period(test_db_session, stock.id, "annual", 2025)
    response = api_client.get("/api/v1/stocks/AAPL/fundamentals/analysis")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["period_type"] == "annual"
    assert set(body["data"]["signals"]) == {"growth", "profitability", "cash_flow", "margins", "financial_strength", "overall"}
    assert body["data"]["signals"]["growth"]["evidence"] == [] or isinstance(body["data"]["signals"]["growth"]["evidence"], list)
    assert body["data"]["provenance"]["freshness"] == "PERIODIC"


def test_analysis_quarterly_and_unavailable(api_client, test_db_session):
    stock = StockRepository.get_or_create(test_db_session, "AMD")
    for year in (2024, 2025):
        persist_financial_period(test_db_session, stock.id, "quarterly", year, 2)
    response = api_client.get("/api/v1/stocks/AMD/fundamentals/analysis", params={"period_type": "quarterly", "limit": 8})
    assert response.status_code == 200
    assert response.json()["data"]["period_type"] == "quarterly"
    StockRepository.get_or_create(test_db_session, "NVDA")
    unavailable = api_client.get("/api/v1/stocks/NVDA/fundamentals/analysis")
    assert unavailable.status_code == 200
    assert unavailable.json()["data"] is None
    assert unavailable.json()["meta"]["reason"] == "NO_PERSISTED_FUNDAMENTALS"


@pytest.mark.parametrize("params", [{"period_type": "monthly"}, {"limit": 0}, {"limit": 21}, {"limit": "bad"}])
def test_analysis_rejects_invalid_parameters(api_client, params):
    assert api_client.get("/api/v1/stocks/AAPL/fundamentals/analysis", params=params).status_code == 422


def test_analysis_unknown_stock_and_database_error(api_client, test_db_session, monkeypatch):
    assert api_client.get("/api/v1/stocks/UNKNOWN/fundamentals/analysis").status_code == 404
    StockRepository.get_or_create(test_db_session, "AAPL")
    from app.repositories import fundamentals_repository
    monkeypatch.setattr(fundamentals_repository.FundamentalsRepository, "get_financial_history", lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("down")))
    assert api_client.get("/api/v1/stocks/AAPL/fundamentals/analysis").status_code == 503
