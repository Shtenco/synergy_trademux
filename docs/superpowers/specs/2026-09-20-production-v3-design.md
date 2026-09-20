# TradeMux V3 Production Hardening Design

**Version:** 3.0.0  
**Branch:** `production/v3.0.0`  
**Status:** design approved for implementation planning

## Goal

Turn TradeMux from a routing + direct adapter dispatch API into a persistent, idempotent execution control plane with an OMS state machine, safe ambiguous-timeout handling, reconciliation, cancel/status flows, tenant isolation, and production-grade auth/readiness.

## Current-state findings

The current product exposes:
- `POST /enterprise/v1/execution/plan`;
- `POST /enterprise/v1/execution/dispatch`.

The dispatch endpoint directly instantiates Bybit/MT5 adapters per request.

The Bybit adapter:
- generates a client order ID when absent;
- signs V5 order requests;
- uses one shared retry/circuit-breaker wrapper for GET and POST;
- retries on server errors through the generic retry policy.

That generic retry behavior is safe for reads but unsafe for an ambiguous financial POST if the venue may have accepted the first request before the client observed the response.

The repository has idempotency DDL but no runtime idempotency or persistent order-state store.

## V3 invariants

1. Every live/paper order has a persistent internal `order_id`.
2. Every venue submission uses a stable `client_order_id`.
3. A create-order request is idempotent.
4. An ambiguous timeout never causes a blind duplicate order submission.
5. Unknown outcome transitions to `UNKNOWN`, then reconciliation determines the next state.
6. Order state survives process restart.
7. Partial fills, fills, rejections, cancel requests and cancellations are explicit states.
8. Venue capabilities are declared, not assumed.
9. Production live execution stays disabled by default and requires separate runtime gate + role.
10. V3 execution uses the common production auth/readiness/idempotency contract.

## OMS state machine

States:

```text
CREATED
  -> SUBMITTING
      -> ACKNOWLEDGED
          -> PARTIALLY_FILLED
              -> FILLED
          -> FILLED
          -> CANCEL_PENDING
              -> CANCELED
              -> ACKNOWLEDGED / PARTIALLY_FILLED
      -> REJECTED
      -> UNKNOWN
          -> ACKNOWLEDGED / PARTIALLY_FILLED / FILLED / REJECTED / CANCELED
```

Terminal states:
- FILLED;
- REJECTED;
- CANCELED.

UNKNOWN is non-terminal and requires reconciliation.

Illegal state transitions are rejected and audited.

## Persistent order model

```python
@dataclass(frozen=True)
class OrderRecord:
    order_id: UUID
    tenant_id: str
    venue: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None
    client_order_id: str
    external_order_id: str | None
    status: OrderStatus
    cumulative_filled_quantity: Decimal
    average_fill_price: Decimal | None
    created_at: datetime
    updated_at: datetime
    version: int
```

Use Decimal-compatible persistence for quantities/prices at the control-plane boundary. Venue formatting remains adapter-specific.

## Idempotent create

`POST /enterprise/v3/orders` requires `Idempotency-Key`.

Transaction:
1. canonicalize request;
2. reserve idempotency key;
3. create internal order with stable client ID;
4. commit local state;
5. if live gate disabled, return DRY_RUN/PAPER state without venue side effect;
6. if live enabled, transition to SUBMITTING and invoke adapter once.

If the request returns ambiguous network failure:
- set order UNKNOWN;
- persist failure context;
- never blind-retry create;
- enqueue or expose reconciliation action.

Same idempotency key + same payload returns the original order resource.
Same key + different payload returns HTTP 409.

## Adapter contract

```python
@dataclass(frozen=True)
class AdapterCapabilities:
    create_order: bool
    get_order: bool
    cancel_order: bool
    supports_client_order_lookup: bool
    supports_partial_fill_state: bool

class ExecutionAdapter(Protocol):
    @property
    def capabilities(self) -> AdapterCapabilities: ...
    def create_order(self, request: VenueOrderRequest) -> VenueOrderSnapshot: ...
    def get_order(self, *, symbol: str, external_id: str | None, client_order_id: str) -> VenueOrderSnapshot: ...
    def cancel_order(self, *, symbol: str, external_id: str | None, client_order_id: str) -> VenueOrderSnapshot: ...
```

Unsafe write methods do not use the generic automatic retry wrapper.

Read-only status/snapshot requests may use bounded retry/circuit breaker.

## Bybit V5 V3 behavior

Implement:
- create via `/v5/order/create`;
- status/query via the appropriate V5 order realtime/history endpoint;
- cancel via `/v5/order/cancel`;
- lookup by stable `orderLinkId`;
- mapping of venue status to OMS status;
- partial-fill quantities;
- rejected/canceled/filled states.

On create timeout:
- preserve stable `orderLinkId`;
- mark UNKNOWN;
- reconcile by lookup using orderLinkId before any further create attempt.

## MT5 and CCXT

Adapters expose capabilities. If reliable client-order lookup/cancel/reconciliation is not available in a deployment, TradeMux must not claim exactly-once live semantics for that adapter.

Unsupported operations return an explicit capability error, not a fake success.

## V3 API

`POST /enterprise/v3/orders`
- role: OPERATOR
- Idempotency-Key required
- live flag still subject to `SYNERGY_ALLOW_LIVE_EXECUTION=true`

`GET /enterprise/v3/orders/{order_id}`
- roles: TRADER, OPERATOR, RISK, ADMIN

`POST /enterprise/v3/orders/{order_id}/cancel`
- role: OPERATOR
- idempotent cancel semantics

`POST /enterprise/v3/orders/{order_id}/reconcile`
- roles: OPERATOR, RISK
- read venue truth and apply legal OMS transition

`GET /enterprise/v3/orders?status=...&venue=...`
- tenant-scoped bounded pagination

Existing V1 plan/dispatch endpoints remain during migration. V1 dispatch is documented as non-OMS legacy behavior.

## Persistence

PostgreSQL authoritative tables:
- orders;
- order_events;
- idempotency_keys;
- audit_events.

Order mutations use optimistic versioning or row locking to prevent conflicting transitions.

`order_events` is append-only and records every transition.

## Reconciliation

Reconciliation must be callable:
- on demand;
- after UNKNOWN;
- after service restart for non-terminal orders;
- periodically in production deployment.

Reconciliation never invents a fill. It maps only venue-reported information into legal state transitions.

## Cancel semantics

Cancel is an intent, not an immediate terminal result:
- local state -> CANCEL_PENDING;
- adapter cancel call;
- venue response/reconciliation decides CANCELED vs already FILLED vs still active.

Repeated cancel requests must be idempotent.

## Common V3 runtime requirements

TradeMux adopts:
- AuthVerifier interface;
- JWKS production verifier;
- HS256 dev/test verifier only;
- runtime PostgreSQL idempotency;
- pooled DB access;
- `/enterprise/live`;
- `/enterprise/ready`;
- structured JSON logging;
- Prometheus metrics;
- optional OpenTelemetry trace propagation.

## Live gate

Live execution requires all:
- OPERATOR role;
- request explicitly asks for live;
- `SYNERGY_ALLOW_LIVE_EXECUTION=true`;
- production adapter credentials available;
- control store ready;
- adapter capability required by requested operation.

Otherwise no venue side effect occurs.

## Failure semantics

- auth failure: 401/403;
- unsupported venue/capability: 400/409 as appropriate;
- idempotency mismatch: 409;
- live gate disabled: 409;
- control store unavailable: 503;
- ambiguous create timeout: persisted UNKNOWN, not automatic duplicate retry;
- audit failure on privileged live state transition: fail closed where transactionally possible;
- venue rejection: persisted REJECTED with sanitized venue reason.

## CI and test requirements

PostgreSQL integration tests must cover:
- duplicate Idempotency-Key same payload -> same order;
- same key different payload -> 409;
- create timeout -> UNKNOWN;
- timeout test proves create was invoked exactly once;
- reconciliation UNKNOWN -> ACKNOWLEDGED;
- partial fill -> PARTIALLY_FILLED;
- partial fill -> FILLED;
- cancel race where venue fills before cancel;
- repeated cancel;
- 429 and 5xx read retries;
- no blind create retry on 5xx/timeout ambiguity;
- restart recovery of non-terminal orders;
- cross-tenant order isolation;
- readiness 503 when DB unavailable;
- live gate prevents side effect;
- V2 test suite remains green.

## Acceptance gates

TradeMux V3 is customer-grade only after:
- persistent OMS survives process restart;
- duplicate create cannot create a duplicate order under tested adapter semantics;
- UNKNOWN state is reconciled safely;
- partial fill/cancel/fill transitions are persisted and auditable;
- live gate is independently testable;
- production auth is JWKS/asymmetric;
- PostgreSQL integration suite passes in CI;
- documentation clearly distinguishes execution-control correctness from promises about fills, slippage, latency or profitability.
