# Final product walkthrough: video script (about 12 minutes)

For the "Final Version of the Product" assignment. It covers the rubric's parts A to E and the code-quality review,
in that order, so a marker can follow along. Record on the **full stack** (`make run-frappe`, Stellar testnet).
The earlier capstone demo script is in [demo-video-script.md](demo-video-script.md).

Each on-chain action takes about 10 to 20 seconds and settlement about 40: talk through the wait or trim it in editing.

## Before recording

```bash
cd ~/Documents/axk-open-source-capstone
make run-frappe            # terminal 1, off camera
make check-env             # terminal 2: must end with "Environment ready."
```

Open these tabs:
1. `http://localhost:8000/trade`
2. GitHub repo
3. `docs/AXK_Technical_Report.pdf`
4. `docs/testing/compatibility-local.md` on GitHub
5. `frappe_app/axk_capstone/axk_capstone/ledger/` on GitHub

Register one spare lot beforehand for the error demonstrations.

## Shot list

| Time | Part | Show | Say |
|---|---|---|---|
| 0:00 to 0:40 | Intro | `/trade` overview | The problem, and the one-line solution: verification and settlement in one workflow on Stellar. Five roles. |
| 0:40 to 1:30 | B. Technical setup | Terminal: `make check-env` | Frontend (Frappe pages, JavaScript), backend (Python API), database (MariaDB), cache (Redis), four smart contracts on Stellar testnet. All green. |
| 1:30 to 4:30 | A. Core functionality | Register a lot, inspect (pass), pay into escrow, dispatch, gate-in, confirm delivery | For each step, say what it does and how. The record is hashed, and only the digest goes on-chain. The escrow asks the registry whether the lot passed and who owns it, and there is no payee field. The split is 40/40/20 with no remainder lost. Open one transaction on Stellar Expert. |
| 4:30 to 5:15 | A/B. Data and verification | Lot page, then **Check records against the chain**; `/trace` with QR; **Download EPCIS** | The browser re-hashes the records and the contracts confirm they match. The public page shows no personal data. The EPCIS export follows the GS1 standard. |
| 5:15 to 6:30 | C. Different inputs | Port screen with a wrong seal gives **Tamper Alert**; reject without a reason is refused; ODK import of the same file twice is refused; Buyer screen: an uninspected lot isn't for sale | Show the error message each time, and say that nothing was recorded on-chain. Mention that the contract refuses payment for uninspected lots (error #10), as covered by the tests. |
| 6:30 to 8:30 | D. Testing strategies | Terminal: `make test-contracts`, then `make test-ledger`, then `python3 scripts/test_epcis.py` | For each strategy: why you chose it, how it works, the result, and what you improved because of it. Unit tests on contracts (65) because money logic can't be patched after deployment. Application unit tests (21) with a fake stellar-cli, so they need no network. End-to-end on testnet. Standards validation against the GS1 schema. Improvements: Logistics and Port screens went from 66 s to 1.4 s, a file-exposure fix, and the restructure into classes. |
| 8:30 to 10:00 | E. Performance and compatibility | `docs/testing/compatibility-local.md` and its screenshots (Firefox, WebKit, phone); then `docs/testing/performance.md`; then resize the browser to phone width | Three browser engines at three sizes, plus a slow phone on 3G. Pages load in under 100 ms locally, a full trade takes about 2 minutes on testnet (mostly network confirmation), and the stack uses about 170 MB of memory. |
| 10:00 to 11:30 | Code quality | GitHub: `ledger/contracts.py`, `ledger/records.py`, `ledger/workflow.py`; `contracts/` folder | Encapsulation (a contract client hides how calls are built), abstraction (base classes), inheritance (one subclass per contract and per record type), polymorphism (`attestation_key()`, a separate error table per contract), and the state machine. The algorithms: canonical hashing, the exact split, the hash chain. |
| 11:30 to 12:00 | Close | README: video link, report link, versions table | Scope status, honestly: the pilot is waiting on ethics approval; mobile-money payout is designed but not built. |

## Recording tips
- Large terminal font, browser at 100% zoom, notifications off.
- If testnet is slow: "Stellar testnet did not answer in time" is itself an error-handling example. Retry once.
- Export as MP4. The Attempt 2 ZIP must contain the video file itself.
