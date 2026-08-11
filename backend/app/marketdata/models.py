from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from .exceptions import ValidationError


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    # try ISO format
    try:
        return datetime.fromisoformat(value)
    except Exception:
        # try numeric (epoch)
        try:
            return datetime.utcfromtimestamp(float(value))
        except Exception:
            raise ValidationError(f"Invalid timestamp: {value}")


@dataclass
class Bar:
    symbol: str
    provider: str
    provider_timestamp: datetime = field(repr=False)
    retrieved_at: datetime = field(repr=False)
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __post_init__(self):
        # parse timestamps if necessary
        try:
            self.provider_timestamp = _parse_timestamp(self.provider_timestamp)
        except ValidationError as e:
            raise

        try:
            self.retrieved_at = _parse_timestamp(self.retrieved_at)
        except ValidationError:
            raise

        # required fields
        if not self.symbol:
            raise ValidationError("symbol is required")
        if not self.provider:
            raise ValidationError("provider is required")

        # numeric validation
        for name in ("open", "high", "low", "close"):
            val = getattr(self, name)
            try:
                if not (isinstance(val, (int, float))):
                    raise ValidationError(f"{name} must be numeric")
            except TypeError:
                raise ValidationError(f"{name} must be numeric")
            if val < 0:
                raise ValidationError(f"{name} must be >= 0")

        if not isinstance(self.volume, int):
            # allow numeric volumes but cast if possible
            try:
                self.volume = int(self.volume)
            except Exception:
                raise ValidationError("volume must be integer")
        if self.volume < 0:
            raise ValidationError("volume must be >= 0")

        # relational checks
        if self.high < max(self.open, self.close, self.low):
            raise ValidationError("high must be >= max(open, close, low)")
        if self.low > min(self.open, self.close, self.high):
            raise ValidationError("low must be <= min(open, close, high)")

    @property
    def timestamp(self) -> datetime:
        """Canonical timestamp for the price (parsed provider_timestamp)."""
        return self.provider_timestamp
