# Benchmarks and acceptance — SYNERGY TradeMux

**20 tests passed**. RBAC covers trader/operator permissions and viewer denial. Local health smoke: **80/80 HTTP 200**, p50 **13.2 ms**, p95 **103.4 ms**, p99 **128.5 ms**, ~**452 req/s** at 80 requests/concurrency 16.

This is health-control-plane smoke only, not routing/execution latency or execution-quality evidence.

Customer acceptance must include representative quote sets, routing determinism, unfilled-notional behavior, sandbox/paper adapter certification, idempotent client-order identity, venue 429/5xx/timeouts and bounded canary approval.