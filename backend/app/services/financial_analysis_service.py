from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from .financial_trend_service import FinancialTrendService


BP = Decimal("0.01")
GROWTH_STRONG = Decimal("0.20")
GROWTH_DECLINE = Decimal("-0.10")
FLOW_CHANGE = Decimal("0.10")


class FinancialAnalysisService:
    """Apply explainable, deterministic rules to persisted financial trends."""

    GROWTH_METRICS = (
        ("revenue_yoy_growth", "Revenue", True),
        ("net_income_yoy_growth", "Net income", True),
        ("eps_yoy_growth", "EPS", False),
        ("free_cash_flow_yoy_growth", "Free cash flow", False),
    )
    MARGIN_METRICS = (
        ("gross_margin", "Gross margin"),
        ("operating_margin", "Operating margin"),
        ("profit_margin", "Profit margin"),
    )

    def __init__(self, trend_service: FinancialTrendService | None = None):
        self.trend_service = trend_service or FinancialTrendService()

    @staticmethod
    def _label(record: dict[str, Any] | None) -> str | None:
        if not record:
            return None
        if record["period_type"] == "quarterly" and record.get("fiscal_quarter") is not None:
            return f"Q{record['fiscal_quarter']} FY{record['fiscal_year']}"
        return f"FY{record['fiscal_year']}"

    @staticmethod
    def _fmt_number(value: Decimal | None, places: int = 1) -> str:
        if value is None:
            return "—"
        return f"{float(value):.{places}f}"

    @classmethod
    def _fmt_percent(cls, value: Decimal | None) -> str:
        if value is None:
            return "—"
        return f"{float(value * 100):+.1f}%"

    @classmethod
    def _fmt_money(cls, value: Decimal | None, record: dict[str, Any] | None = None) -> str:
        if value is None:
            return "—"
        unit = (record or {}).get("unit") or ""
        suffix = f" {unit}" if unit else ""
        absolute = abs(value)
        if absolute >= 1_000_000_000:
            return f"${float(value / Decimal('1000000000')):.1f}B{suffix}"
        if absolute >= 1_000_000:
            return f"${float(value / Decimal('1000000')):.1f}M{suffix}"
        return f"${float(value):.1f}{suffix}"

    @classmethod
    def _basis(cls, records: list[dict[str, Any]], periods_used: int | None = None) -> dict[str, Any]:
        latest = records[-1] if records else None
        previous = records[-2] if len(records) > 1 else None
        return {
            "period_type": latest.get("period_type") if latest else None,
            "latest_period": cls._label(latest),
            "comparison_period": cls._label(previous),
            "periods_used": periods_used if periods_used is not None else len(records),
        }

    @classmethod
    def _signal(
        cls,
        name: str,
        status: str,
        records: list[dict[str, Any]],
        evidence: list[str],
        metrics_used: list[str],
        metrics_missing: list[str],
        periods_used: int | None = None,
    ) -> dict[str, Any]:
        available = status != "UNAVAILABLE"
        return {
            "signal": name,
            "status": status,
            "available": available,
            "evidence": evidence,
            "basis": cls._basis(records, periods_used),
            "metrics_used": metrics_used,
            "metrics_missing": metrics_missing,
        }

    @classmethod
    def growth(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        latest = records[-1] if records else {}
        valid = [(key, label, core, latest.get(key)) for key, label, core in cls.GROWTH_METRICS if latest.get(key) is not None]
        missing = [label for key, label, _core in cls.GROWTH_METRICS if latest.get(key) is None]
        used = [label for _key, label, _core, _value in valid]
        if len(valid) < 2:
            return cls._signal("GROWTH", "UNAVAILABLE", records, [], used, missing)

        values = [value for _key, _label, _core, value in valid]
        positive = sum(value > 0 for value in values)
        strong = sum(value >= GROWTH_STRONG for value in values)
        declining = sum(value < GROWTH_DECLINE for value in values)
        core_values = [value for _key, _label, core, value in valid if core]
        evidence = [
            f"{label} YoY {cls._fmt_percent(value)} in {cls._label(latest)}"
            for _key, label, _core, value in valid
        ]
        if strong >= 2 and not any(value < GROWTH_DECLINE for value in core_values):
            status = "STRONG"
        elif declining >= 2 or len(core_values) == 2 and all(value < GROWTH_DECLINE for value in core_values):
            status = "DECLINING"
        elif positive > len(values) / 2 and any(value >= Decimal("0.05") for value in values):
            status = "MODERATE"
        else:
            status = "WEAK"
        return cls._signal("GROWTH", status, records, evidence, used, missing)

    @classmethod
    def _margin_deltas(cls, records: list[dict[str, Any]]) -> dict[str, Decimal]:
        deltas: dict[str, Decimal] = {}
        for key, _label in cls.MARGIN_METRICS:
            values = [record.get(key) for record in records]
            if len(records) >= 4 and all(value is not None for value in values[-4:]):
                deltas[key] = (values[-2] + values[-1]) / 2 - (values[-4] + values[-3]) / 2
            elif len(records) >= 2 and values[-1] is not None and values[-2] is not None:
                deltas[key] = values[-1] - values[-2]
        return deltas

    @classmethod
    def profitability(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        deltas = cls._margin_deltas(records)
        latest = records[-1] if records else {}
        missing = [label for key, label in cls.MARGIN_METRICS if key not in deltas]
        used = [label for key, label in cls.MARGIN_METRICS if key in deltas]
        net_growth = latest.get("net_income_yoy_growth")
        if len(deltas) < 2:
            return cls._signal("PROFITABILITY", "UNAVAILABLE", records, [], used, missing)
        improved = sum(delta >= BP for delta in deltas.values())
        weakened = sum(delta <= -BP for delta in deltas.values())
        evidence = [f"{label} {delta * 100:+.1f} percentage points" for key, label in cls.MARGIN_METRICS if (delta := deltas.get(key)) is not None]
        if net_growth is not None:
            evidence.append(f"Net income YoY {cls._fmt_percent(net_growth)}")
        if improved >= 2 and not (net_growth is not None and net_growth < Decimal("-0.20")):
            status = "IMPROVING"
        elif weakened >= 2 or (net_growth is not None and net_growth < Decimal("-0.20") and weakened >= 1):
            status = "DETERIORATING"
        else:
            status = "STABLE"
        if net_growth is not None:
            used.append("Net income trend")
        return cls._signal("PROFITABILITY", status, records, evidence, used, missing)

    @classmethod
    def margins(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        deltas = cls._margin_deltas(records)
        missing = [label for key, label in cls.MARGIN_METRICS if key not in deltas]
        used = [label for key, label in cls.MARGIN_METRICS if key in deltas]
        if len(deltas) < 2:
            return cls._signal("MARGINS", "UNAVAILABLE", records, [], used, missing)
        expanding = sum(delta >= BP for delta in deltas.values())
        contracting = sum(delta <= -BP for delta in deltas.values())
        if expanding >= 2:
            status = "EXPANDING"
        elif contracting >= 2:
            status = "CONTRACTING"
        else:
            status = "STABLE"
        evidence = [f"{label} {delta * 100:+.1f} percentage points" for key, label in cls.MARGIN_METRICS if (delta := deltas.get(key)) is not None]
        periods_used = 4 if len(records) >= 4 and all(all(record.get(key) is not None for record in records[-4:]) for key, _label in cls.MARGIN_METRICS if key in deltas) else 2
        return cls._signal("MARGINS", status, records, evidence, used, missing, periods_used)

    @classmethod
    def _flow_change(cls, current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous in (None, 0) or (current < 0) != (previous < 0):
            return None
        return (current - previous) / abs(previous)

    @classmethod
    def cash_flow(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        latest = records[-1] if records else {}
        previous = records[-2] if len(records) > 1 else {}
        fcf, prev_fcf = latest.get("free_cash_flow"), previous.get("free_cash_flow")
        ocf, prev_ocf = latest.get("operating_cash_flow"), previous.get("operating_cash_flow")
        used = [label for label, value in (("Free cash flow", fcf), ("Operating cash flow", ocf), ("Capital expenditures", latest.get("capital_expenditures"))) if value is not None]
        missing = [label for label, value in (("Free cash flow", fcf), ("Operating cash flow", ocf), ("Capital expenditures", latest.get("capital_expenditures"))) if value is None]
        if fcf is None and ocf is None or len(records) < 2:
            return cls._signal("CASH_FLOW", "UNAVAILABLE", records, [], used, missing)
        evidence: list[str] = []
        if fcf is not None:
            evidence.append(f"FCF {cls._fmt_money(fcf, latest)} in {cls._label(latest)}")
        if ocf is not None:
            evidence.append(f"Operating cash flow {cls._fmt_money(ocf, latest)} in {cls._label(latest)}")
        if fcf is not None and prev_fcf is not None and (fcf < 0 or prev_fcf < 0 or fcf != prev_fcf):
            evidence.append(f"FCF changed from {cls._fmt_money(prev_fcf, previous)} to {cls._fmt_money(fcf, latest)}")
        if fcf is not None and fcf < 0:
            status = "NEGATIVE"
        elif ocf is not None and ocf < 0:
            status = "WEAKENING"
            evidence.append("Operating cash flow is negative")
        else:
            fcf_change = cls._flow_change(fcf, prev_fcf)
            ocf_change = cls._flow_change(ocf, prev_ocf)
            crossing_to_positive = prev_fcf is not None and prev_fcf < 0 and fcf is not None and fcf >= 0
            if crossing_to_positive and ocf is not None and prev_ocf is not None and ocf > prev_ocf and ocf > 0:
                status = "IMPROVING"
            elif fcf_change is not None and ocf_change is not None and fcf > 0 and ocf > 0 and fcf_change >= FLOW_CHANGE and ocf_change >= FLOW_CHANGE:
                status = "IMPROVING"
            elif (fcf_change is not None and fcf_change <= -FLOW_CHANGE) or (ocf_change is not None and ocf_change <= -FLOW_CHANGE):
                status = "WEAKENING"
            elif fcf is not None and fcf > 0 and ocf is not None and ocf > 0:
                status = "STABLE"
            else:
                status = "UNAVAILABLE"
        return cls._signal("CASH_FLOW", status, records, evidence, used, missing)

    @classmethod
    def financial_strength(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        latest = records[-1] if records else {}
        values = {
            "Cash": latest.get("cash_and_cash_equivalents"),
            "Total debt": latest.get("total_debt"),
            "Operating cash flow": latest.get("operating_cash_flow"),
            "Free cash flow": latest.get("free_cash_flow"),
        }
        used = [key for key, value in values.items() if value is not None]
        missing = [key for key, value in values.items() if value is None]
        if len(used) < 2:
            return cls._signal("FINANCIAL_STRENGTH", "UNAVAILABLE", records, [], used, missing, 1)
        cash, debt, ocf, fcf = values.values()
        evidence = [f"{key}: {cls._fmt_money(value, latest)}" for key, value in values.items() if value is not None]
        if cash is not None and debt is not None and cash >= debt and ocf is not None and ocf > 0 and fcf is not None and fcf >= 0:
            status = "HEALTHY"
            evidence.append("Cash is at least total debt and both cash-flow measures are positive")
        elif cash is not None and debt is not None and cash < debt and ((ocf is not None and ocf < 0) or (fcf is not None and fcf < 0)):
            status = "WEAK"
            evidence.append("Cash is below total debt and at least one cash-flow measure is negative")
        else:
            status = "MIXED"
            evidence.append("Available cash, debt, and cash-flow measures do not establish a clear condition")
        return cls._signal("FINANCIAL_STRENGTH", status, records, evidence, used, missing, 1)

    @classmethod
    def overall(cls, signals: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
        positive_statuses = {"STRONG", "MODERATE", "IMPROVING", "STABLE", "EXPANDING", "HEALTHY"}
        negative_statuses = {"DECLINING", "DETERIORATING", "WEAKENING", "NEGATIVE", "CONTRACTING", "WEAK"}
        available = [signal for signal in signals if signal["available"]]
        positive = sum(signal["status"] in positive_statuses for signal in available)
        negative = sum(signal["status"] in negative_statuses for signal in available)
        if len(available) < 2:
            status = "UNAVAILABLE"
        elif positive >= 3 and negative <= 1:
            status = "POSITIVE"
        elif negative >= 3 and positive <= 1:
            status = "NEGATIVE"
        else:
            status = "MIXED"
        evidence = [f"{positive} positive and {negative} negative signals are available"] if available else []
        return cls._signal("OVERALL", status, records, evidence, [signal["signal"] for signal in available], [signal["signal"] for signal in signals if not signal["available"]])

    def get_analysis(self, session: Session, symbol: str, period_type: str = "annual", limit: int = 8) -> dict[str, Any]:
        trend = self.trend_service.get_history(session, symbol, period_type, limit)
        if not trend["meta"]["available"] or trend["data"] is None:
            return {"data": None, "meta": {"available": False, "periods_used": 0, "missing_metrics": [], "data_availability": {}, "reason": "NO_PERSISTED_FUNDAMENTALS"}}
        records = trend["data"]["periods"]
        signals = [self.growth(records), self.profitability(records), self.cash_flow(records), self.margins(records), self.financial_strength(records)]
        overall = self.overall(signals, records)
        signals_by_name = {signal["signal"].lower(): signal for signal in signals}
        signals_by_name["overall"] = overall
        return {
            "data": {
                "symbol": trend["data"]["symbol"],
                "company_name": trend["data"].get("company_name"),
                "period_type": trend["data"]["period_type"],
                "signals": signals_by_name,
                "provenance": trend["data"]["provenance"],
            },
            "meta": {
                "available": True,
                "periods_used": len(records),
                "missing_metrics": trend["meta"]["missing_metrics"],
                "data_availability": trend["meta"]["metric_coverage"],
            },
        }
