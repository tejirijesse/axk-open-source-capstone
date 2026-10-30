# Performance and resource use

Target `http://localhost:8000` · Darwin 24.5.0 (arm64) · 10 CPUs · run 2026-10-30 15:04 EAT

## Response times (local server, warm cache)

| Request | Median (ms) | 95th percentile (ms) | n |
|---|---|---|---|
| GET /trade (page) | 72.6 | 77.9 | 20 |
| GET /trace/lot (public page with QR) | 84.1 | 87.4 | 20 |
| API overview (all lots) | 3.3 | 4.1 | 20 |
| API lot detail | 4.0 | 4.5 | 20 |
| API personas (balances, cached) | 3.0 | 4.1 | 20 |
| EPCIS export | 4.0 | 4.6 | 20 |

## One full trade on Stellar testnet (AXK-LIVE-CP-20261030-0011)

| Step | Seconds |
|---|---|
| register | 13.2 |
| inspect | 9.5 |
| fund escrow | 15.6 |
| dispatch | 22.6 |
| port gate-in | 17.3 |
| settle (4 transactions) | 38.7 |
| verify against chain | 9.8 |
| **Total** | **126.7** |

## Server resources

| Component | Processes | Memory (MB) | CPU % at rest |
|---|---|---|---|
| web (gunicorn/werkzeug) | 2 | 105.2 | 22.7 |
| workers | 1 | 6.7 | 0.0 |
| redis | 2 | 7.3 | 0.9 |
| socketio | 1 | 11.1 | 0.0 |
| mariadb | 1 | 41.3 | 1.4 |

## Sizes

| File | KB | gzip KB |
|---|---|---|
| public/js/trade.js | 62.3 | 15.7 |
| public/js/chain.js | 27.7 | 8.4 |
| public/css/axk.css | 19.2 | 4.3 |
| public/css/chain.css | 9.3 | 2.5 |
| contract axk_attestation.wasm | 3.1 | |
| contract axk_escrow.wasm | 7.4 | |
| contract axk_lot_registry.wasm | 7.4 | |
| contract axk_splitter.wasm | 5.1 | |
