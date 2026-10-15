# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- GS1 EPCIS 2.0 export of each lot's public history (`/api/method/axk_capstone.epcis.lot_events`), linked
  from `/trace/lot`, validated against the official GS1 schema in `scripts/test_epcis.py` (PUB-6).
- Offline inspection with ODK: an XLSForm (`odk/`), an importer that signs the inspection and hashes the
  original submission into the report digest, an ODK Central sync script, and an import card on
  `/trade/inspect` (INSP-6).
- Design note on paying members through Mojaloop (`docs/design/set-3-mojaloop-payouts.md`, SET-3) and roadmap
  item SET-4 for attested payout records.
- `docs/references.md`: open standards and open-source projects AXK learns from (GS1 EPCIS, farmOS,
  Open Food Network, ODK, OpenLMIS, Mojaloop).
- Roadmap items INSP-6 (offline inspection with ODK), SET-3 (Mojaloop payout study) and PUB-6 (GS1 EPCIS export).

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
