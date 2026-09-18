# SYNERGY TradeMux

**Venue-neutral execution fabric with smart routing, split execution and reconciliation evidence**

Version: `2.0.0` · Python 3.11+ · REST API · Docker · CI · automated tests

## Why this exists
One strategy often requires different broker/exchange adapters, routing logic and reconciliation.

## Commercial buyer
Brokers, crypto venues, prop firms, market makers and multi-venue trading teams.

## Core guarantee
The software guarantees deterministic interface behavior covered by tests. **It does not guarantee trading profit.** Live-market deployment requires customer-specific OOS validation, fees/spread/slippage/latency/capacity modelling, security review and legal/compliance approval.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
python -m synergy_trademux.api
```

Then open `http://localhost:8000/docs`.

## Commercial package
- standalone installable Python package;
- versioned FastAPI boundary;
- deterministic reference core;
- Dockerfile and GitHub Actions CI;
- sales one-pager, security boundary, deployment notes and provenance;
- proprietary evaluation licence ready for a paid pilot.

## Research lineage
MQL5 TradeMux REST / Quant Backbone lineage; Shtenco/synergy_pay_system routing and settlement architecture

See `docs/PRODUCT_STATUS.md`, `docs/SALES_ONE_PAGER.md`, `docs/SECURITY.md` and `docs/PROVENANCE.md`.

## Enterprise v2.0.0

The repository now includes a separate enterprise boundary around the product core:

- JWT/RBAC roles (`viewer`, `researcher`, `trader`, `risk`, `operator`, `admin`);
- request-id propagation and auditable product actions;
- PostgreSQL and ClickHouse audit stores;
- Bybit V5, CCXT multi-CEX and MetaTrader 5 adapters with live execution disabled by default;
- retry/circuit breaker controls;
- health and Prometheus-compatible metrics;
- Docker Compose deployment reference;
- deterministic synthetic customer dataset and HTTP/k6 load harnesses.

See `docs/ENTERPRISE_ARCHITECTURE.md`, `docs/ENTERPRISE_DEPLOYMENT.md` and `docs/CUSTOMER_ACCEPTANCE.md` before any customer deployment.
