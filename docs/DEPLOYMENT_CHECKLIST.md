# Deployment checklist — SYNERGY TradeMux

- [ ] Pin commit/image and rerun tests.
- [ ] Customer TLS + OIDC/mTLS/JWKS.
- [ ] KMS secrets and least-privilege venue credentials.
- [ ] PostgreSQL/ClickHouse backup/restore and audit trace.
- [ ] Validate `/enterprise/v1/execution/plan` under representative quote loads.
- [ ] Exercise dry-run and paper venue adapters.
- [ ] Prove `SYNERGY_ALLOW_LIVE_EXECUTION=false` blocks live dispatch.
- [ ] Drill timeout/429/5xx/circuit-open/DB outage/restart.
- [ ] Trading + Risk + Ops + Security/Compliance approve any live canary.