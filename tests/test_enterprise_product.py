import json
from fastapi.testclient import TestClient
from synergy_trademux.api import app
from synergy_trademux.enterprise.auth import sign_token
from synergy_trademux.enterprise.models import Role

SECRET="dev-only-change-me-not-for-production"

def token(role):
    return sign_token(SECRET,subject="fund-user",roles=[Role(role)],tenant_id="fund-a",ttl_seconds=3600)

def test_product_enterprise_endpoint_and_audit_linkage():
    c=TestClient(app)
    request_id="acceptance-123"
    res=c.post('/enterprise/v1/execution/plan',json={'notional': 10000, 'quotes': [{'venue': 'A', 'price': 100, 'available_notional': 6000, 'fee_bps': 2, 'slippage_bps': 1, 'latency_ms': 10, 'risk_score': 0.01}, {'venue': 'B', 'price': 100.1, 'available_notional': 6000, 'fee_bps': 1, 'slippage_bps': 1, 'latency_ms': 20, 'risk_score': 0.0}]},headers={"Authorization":"Bearer "+token('trader'),"X-Request-ID":request_id})
    assert res.status_code==200, res.text
    body=res.json()
    for key in ['correlation_id', 'slices', 'request_id']: assert key in body
    assert body["request_id"]==request_id
    admin=token("admin")
    audit=c.get('/enterprise/audit',headers={"Authorization":"Bearer "+admin})
    assert audit.status_code==200
    assert any(e["request_id"]==request_id for e in audit.json())

def test_product_endpoint_requires_authorized_role():
    c=TestClient(app)
    res=c.post('/enterprise/v1/execution/plan',json={'notional': 10000, 'quotes': [{'venue': 'A', 'price': 100, 'available_notional': 6000, 'fee_bps': 2, 'slippage_bps': 1, 'latency_ms': 10, 'risk_score': 0.01}, {'venue': 'B', 'price': 100.1, 'available_notional': 6000, 'fee_bps': 1, 'slippage_bps': 1, 'latency_ms': 20, 'risk_score': 0.0}]},headers={"Authorization":"Bearer "+token("viewer")})
    assert res.status_code==403

def test_api_exposes_enterprise_control_routes():
    paths={r.path for r in app.routes}
    assert '/enterprise/health' in paths
    assert '/enterprise/v1/execution/plan' in paths
