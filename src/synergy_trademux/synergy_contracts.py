from __future__ import annotations
from typing import Any
from uuid import UUID

from .core import ExecutionPlan, Fill, VenueQuote, smart_route


PLAN_CONTRACT_ID = "synergy.trading.execution-plan/v1"
RESULT_CONTRACT_ID = "synergy.trading.execution-result/v1"
AUTHORITY = "trade_execution"
UPSTREAM_CONTRACT_ID = "synergy.trading.risk-decision/v1"


def plan_from_risk_decision(
    *,
    risk_payload: dict[str, Any],
    quotes: list[VenueQuote],
    symbol: str,
    side: str,
    max_venues: int = 4,
) -> ExecutionPlan:
    action = str(risk_payload.get("action", "")).upper()
    if action in {"REJECT", "KILL_SWITCH"}:
        raise ValueError(f"risk decision forbids execution: {action}")
    if action not in {"ALLOW", "RESIZE"}:
        raise ValueError("unknown risk action")
    approved = float(risk_payload.get("approved_notional", 0))
    if approved <= 0:
        raise ValueError("approved_notional must be positive")
    return smart_route(approved, quotes, max_venues=max_venues)


def execution_plan_payload(
    *,
    risk_event_id: UUID | str,
    symbol: str,
    side: str,
    requested_notional: float,
    plan: ExecutionPlan,
) -> dict[str, Any]:
    return {
        "risk_event_id": str(risk_event_id),
        "correlation_id": plan.correlation_id,
        "symbol": symbol,
        "side": side.upper(),
        "requested_notional": str(requested_notional),
        "slices": [
            {
                "venue": s.venue,
                "notional": str(s.notional),
                "expected_price": str(s.expected_price),
                "expected_cost_bps": float(s.expected_cost_bps),
            }
            for s in plan.slices
        ],
        "unfilled_notional": str(plan.unfilled_notional),
    }


def execution_result_payload(
    *,
    plan_event_id: UUID | str,
    symbol: str,
    side: str,
    requested_notional: float,
    fills: list[Fill],
    status: str,
) -> dict[str, Any]:
    filled = sum(float(f.filled) for f in fills)
    return {
        "plan_event_id": str(plan_event_id),
        "symbol": symbol,
        "side": side.upper(),
        "requested_notional": str(requested_notional),
        "filled_notional": str(filled),
        "fills": [
            {
                "venue": f.venue,
                "requested": str(f.requested),
                "filled": str(f.filled),
                "avg_price": str(f.avg_price),
                "fee": str(f.fee),
                "external_id": f.external_id,
            }
            for f in fills
        ],
        "status": status.upper(),
    }
