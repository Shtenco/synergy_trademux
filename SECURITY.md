# Security policy — SYNERGY TradeMux

- No live secrets in Git; use KMS/secret manager.
- Live dispatch requires request `live=true` **and** `SYNERGY_ALLOW_LIVE_EXECUTION=true`, plus customer Trading/Risk/Ops approval.
- Prefer customer OIDC/mTLS/JWKS; included HS256 is evaluation/reference only.
- Least-privilege venue keys, withdrawals disabled where possible.
- Stable client order IDs are required before retrying operations with possible financial side effects.
- PostgreSQL is authoritative audit; ClickHouse is analytical mirror.

No SOC 2/ISO/regulatory certification is claimed.