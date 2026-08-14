from abc import ABC, abstractmethod
from typing import Any

class FundamentalsClient(ABC):
    provider_name = "unknown"
    @abstractmethod
    def get_income_statement(self, symbol: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    def get_balance_sheet(self, symbol: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    def get_cash_flow(self, symbol: str) -> list[dict[str, Any]]: ...
