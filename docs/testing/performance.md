# Performance and resource use

Target `http://localhost:8000` · Darwin 24.5.0 (arm64) · 10 CPUs · run 2026-10-31 12:50 EAT

## Response times (local server, warm cache)

| Request | Median (ms) | 95th percentile (ms) | n |
|---|---|---|---|
| GET /trade (page) | 38.6 | 39.6 | 20 |
| GET /trace/lot (public page with QR) | 50.7 | 53.0 | 20 |
| API overview (all lots) | 3.8 | 4.1 | 20 |
| API lot detail | 3.7 | 3.9 | 20 |
| API personas (balances, cached) | 3.3 | 5.5 | 20 |
| EPCIS export | 3.3 | 3.6 | 20 |

## One full trade on Stellar testnet (AXK-LIVE-CP-20261031-0015)

| Step | Seconds |
|---|---|
| register | 6.8 |
| inspect | 10.5 |
| fund escrow | 9.0 |
| dispatch | 10.6 |
| port gate-in | 9.5 |
| settle (4 transactions) | 35.4 |
| verify against chain | 5.7 |
| **Total** | **87.5** |

## Server resources

| Component | Processes | Memory (MB) | CPU % at rest |
|---|---|---|---|
| web (gunicorn/werkzeug) | 2 | 143.6 | 5.7 |
| workers | 1 | 15.7 | 0.0 |
| redis | 2 | 12.1 | 1.8 |
| socketio | 1 | 52.0 | 0.0 |
| mariadb | 1 | 39.7 | 3.4 |

## Sizes

| File | KB | gzip KB |
|---|---|---|
| public/js/trade.js | 71.3 | 20.1 |
| public/js/chain.js | 33.3 | 10.3 |
| public/css/axk.css | 41.2 | 8.5 |
| public/css/chain.css | 9.1 | 2.2 |
| contract axk_attestation.wasm | 3.1 | |
| contract axk_escrow.wasm | 7.4 | |
| contract axk_lot_registry.wasm | 7.4 | |
| contract axk_splitter.wasm | 5.1 | |
