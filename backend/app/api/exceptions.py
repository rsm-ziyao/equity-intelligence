"""Application exceptions used by the HTTP API."""


class StockNotFoundError(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Stock symbol '{symbol}' was not found.")


class InvalidDateRangeError(Exception):
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        super().__init__("end_date must be greater than or equal to start_date.")


class DatabaseUnavailableError(Exception):
    def __init__(self, message: str = "The database is unavailable."):
        super().__init__(message)
