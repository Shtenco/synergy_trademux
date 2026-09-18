# Architecture — SYNERGY TradeMux

```mermaid
flowchart LR
A[Strategy]-->B[Trade intent]
B-->C[RBAC + tenant]
C-->D[Smart router]
D-->E[Execution plan]
E-->F{Live gate}
F-->|dry/paper|G[No capital at risk]
F-->|approved|H[Bybit V5 / MT5]
E-->I[Audit + request ID]
I-->J[(PostgreSQL)]
I-->K[(ClickHouse)]
```

Planning endpoint: `/enterprise/v1/execution/plan`. Explicit live dispatch: `POST /enterprise/v1/execution/dispatch` and requires operator role plus environment gate.