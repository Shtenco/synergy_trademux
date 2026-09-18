# API examples — SYNERGY TradeMux

Primary planning action: `POST /enterprise/v1/execution/plan` — roles **trader, operator**.

```json
{"notional":10000,"quotes":[{"venue":"A","price":100,"available_notional":6000,"fee_bps":2,"slippage_bps":1,"latency_ms":10,"risk_score":0.01},{"venue":"B","price":100.1,"available_notional":6000,"fee_bps":1,"slippage_bps":1,"latency_ms":20,"risk_score":0.0}]
```

```bash
curl -X POST http://127.0.0.1:8000/enterprise/v1/execution/plan -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "X-Request-ID: pilot-001" -d @request.json
```

Expected: **correlation_id, slices, unfilled_notional, request_id**. Live dispatch is a separate endpoint and remains disabled unless the environment gate is explicitly enabled. Canonical interface: `/docs`.