# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-15

First public release.

### Added
- Soroban contracts: lot registry (inspection gate), escrow (payee from the registry, one live escrow per lot),
  splitter (exact 40/40/20 payouts), attestation (write-once digests). 65 tests.
- Frappe app `axk_capstone`, running on a plain Frappe v15 site: Cooperative, Inspector, Buyer, Logistics and
  Port screens; lot timeline; public `/trace` with QR; `/chain` explorer with live testnet flow and an
  in-browser hash-chain verifier.
- `scripts/demo.sh`: deploys fresh contracts and runs a verified trade on Stellar testnet.
- Offline simulation (`scripts/server.py`), labelled as a simulation on every page, and an end-to-end test
  suite (`scripts/test_trade.py`).
- Optional synthetic five-year history for the explorer (`axk_seed/`), with fictional names and every row
  tagged synthetic.
- Open-source scaffolding: contribution guide, code of conduct, security policy, governance, roadmap,
  issue and pull request templates.
