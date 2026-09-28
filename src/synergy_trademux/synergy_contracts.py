from __future__ import annotations
from typing import Any
from uuid import UUID

from .core import ExecutionPlan, Fill


PLAN_CONTRACT_ID = "synergy.trading.execution-plan/v1"
RESULT_CONTRACT_ID = "synergy.trading.execution-result/v1"
AUTHORITY = "trade_execution"


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
