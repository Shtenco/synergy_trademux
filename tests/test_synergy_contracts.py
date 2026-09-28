from uuid import UUID

from synergy_trademux.core import Fill, VenueQuote, smart_route
from synergy_trademux.synergy_contracts import execution_plan_payload, execution_result_payload


def test_execution_contracts_derive_from_core_plan_and_fills():
    plan = smart_route(
        1000,
        [VenueQuote("paper", 1.1, 1000, 1.0, 1.0, 5.0)],
    )
    p = execution_plan_payload(
        risk_event_id=UUID("33333333-3333-4333-8333-333333333333"),
        symbol="EURUSD",
        side="BUY",
        requested_notional=1000,
        plan=plan,
    )
    assert p["unfilled_notional"] == "0.0"
    r = execution_result_payload(
        plan_event_id=UUID("44444444-4444-4444-8444-444444444444"),
        symbol="EURUSD",
        side="BUY",
        requested_notional=1000,
        fills=[Fill("paper", 1000, 1000, 1.1, 0.2, "fill-1")],
        status="FILLED",
    )
    assert r["filled_notional"] == "1000.0"
    assert r["fills"][0]["external_id"] == "fill-1"
