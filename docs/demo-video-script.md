# Demo video script (target 9:30, limit 10:00)

**Recorded video:** https://youtu.be/MrSXiJG_MAU

The brief asks for demonstration over description. Everything below runs on the **full stack** (`make
run-frappe`, Stellar testnet). Never record the offline simulation (`make run`) as the product.

The *Say* column holds cues, not lines to read. Every on-chain action takes 5–10 seconds (settlement about 40),
so talk through the wait or trim it when editing.

---

## 1. The day before

```bash
cd ~/Documents/axk-open-source-capstone
make test-contracts              # 65 passing: proves the toolchain before recording day
```

- Do one complete practice trade on the screens. That also refreshes the explorer's live events, which only
  reach back about 7 days.
- Log into Frappe Desk once (`http://localhost:8000/app/axk-chain-trade`) with your own administrator account,
  so the backend list view is ready to show.

## 2. Ten minutes before recording

**Terminal 1** starts the stack. Leave it running and off camera:

```bash
cd ~/Documents/axk-open-source-capstone
make run-frappe
```

**Terminal 2** is the on-camera terminal. Use a large font (18 pt or more) and a dark theme, and run:

```bash
cd ~/Documents/axk-open-source-capstone
make check-env                   # must end with "Environment ready."
python3 odk/sample_submission.py AXK-LIVE-CP-20261015-0005 > ~/Desktop/odk-inspection.xml
clear
```

The ODK file is for the lot already waiting in the inspector queue. If `AXK-LIVE-CP-20261015-0005` has been
inspected since, register another lot first and use its reference.

**Browser:** 1280×800 or larger, zoom 100%, notifications off. Open these tabs in this order:

| # | Tab | URL |
|---|---|---|
| 1 | Overview | `http://localhost:8000/trade` |
| 2 | GitHub repo | `https://github.com/tejirijesse/axk-open-source-capstone` |
| 3 | Architecture | `https://github.com/tejirijesse/axk-open-source-capstone/blob/main/docs/architecture.md` |
| 4 | Frappe Desk | `http://localhost:8000/app/axk-chain-trade` |
| 5 | Stellar Expert | `https://stellar.expert/explorer/testnet` |
| 6 | Security | `https://github.com/tejirijesse/axk-open-source-capstone/blob/main/docs/security.md` |

**Final checks:**
- [ ] Buyer screen shows at least 500,000 RWF. If not, use **Top up 500,000 RWF (testnet)**.
- [ ] `/trade/inspect` shows `AXK-LIVE-CP-20261015-0005` first in the queue.
- [ ] Screen recorder captures the browser and terminal 2, with the microphone on.

---

## 3. Shot list

| Time | Where | Do | Say |
|---|---|---|---|
| **0:00–0:30** | Tab 1 `/trade` | Nothing; let the overview sit | The problem in one line: a buyer across a border can't verify quality or custody, and payment is slow and untrusted. AXK puts verification and settlement in one workflow on Stellar. Name the five roles on screen. |
| **0:30–1:10** | Terminal 2 | `make check-env` | My development environment: Rust and stellar-cli for the contracts; MariaDB and Redis; the Frappe v15 server with my `axk_capstone` app; four contracts deployed on Stellar testnet. All green. |
| **1:10–1:40** | Terminal 2, then tab 4 | `make show-db`, then show the Desk list view | The backend keeps each record in MariaDB, with the transaction hash of every step. The database holds the records; the blockchain holds their fingerprints and enforces the rules. |
| **1:40–2:10** | Tab 2, then tab 3 | Scroll the README stack table; then the system schematic and sequence diagram | It's open source under MIT, with a roadmap for contributors. This is the architecture: screens, API, signer, contracts. |
| **2:10–2:40** | Terminal 2 | `make test-contracts` | 65 contract tests across the lot registry, escrow, splitter and attestation. |
| **2:40–3:30** | `/trade/coop` | Register: Coffee (parchment), grade A, 3,850 kg, Huye. **Register lot on-chain**, then click the transaction link in the toast | Only a SHA-256 digest goes on-chain. The lot ID is bound to the cooperative's address, so nobody can claim someone else's lot. *(Stellar Expert opens: a real transaction.)* |
| **3:30–3:45** | `/trade/buy` | Show the new lot is **not** listed | A buyer can't pay for an uninspected lot. The escrow contract refuses it even if you try (`LotNotApproved`). |
| **3:45–4:20** | `/trade/inspect`, bottom card | **Import an offline inspection (ODK)**: choose `~/Desktop/odk-inspection.xml`, **Import and sign** | Inspectors work offline. They fill a form in ODK Collect on a phone, and when it syncs it's signed on-chain. The digest covers the original field submission, so it can't be edited afterwards. |
| **4:20–5:00** | `/trade/inspect`, top | Your new lot is now first. Use `j`/`k` to move and `r` to show the reject reasons, then `a`, adjust moisture, **Sign: pass** | Oldest first. A rejection needs a reason and is permanent. A cooperative can't inspect its own lot. Signed once, on-chain. |
| **5:00–5:40** | `/trade/buy` | The lot is listed, with "Inspected by…". **Pay into escrow** 250,000 RWF, then **Sign and pay into escrow** | The buyer and the AXK verifier both sign. There's no payee field: the escrow asks the registry who owns this inspected lot. The balance drops. |
| **5:40–6:30** | `/trade/logistics`, then `/trade/port` | Select the lot, **Seal container & dispatch on-chain**; on port, the same seal number, **Verify seal & clear gate-in on-chain** | Waybill and port-receipt digests are attested on-chain. To be precise: the verifier key signs these on the carrier's and port's behalf, and the seal match is an application check. That's on the roadmap. |
| **6:30–7:15** | `/trade/buy` | **Confirm delivery (at port)** | Four transactions: release the escrow, record the 40/40/20 split, pay the members, attest the settlement. |
| **7:15–7:45** | Lot page (click the lot) | Scroll the nine-step timeline; **Check records against the chain**; **Download record** | Every payment traces back to inspection and registration. The browser re-hashes the records and the contracts confirm they match. |
| **7:45–8:15** | **Public page ↗** (`/trace/lot`) | Show the verdict and QR; **Download EPCIS (JSON-LD)**, then **View ↗** | What a buyer's own customer sees, with no login and no personal data. It also exports as GS1 EPCIS, the standard customs and traceability systems read. |
| **8:15–9:00** | `/chain` | Money-flow diagram, *Verified before paid*; scroll to the hash chain: **Verify chain**, then **Tamper with an event** | Live testnet data at the top. In the hash chain, changing one weight breaks that event and every one after it. The history charts are synthetic demo data, labelled as such. |
| **9:00–9:30** | Tab 6 `docs/security.md` | Scroll the guarantees table, then back to tab 1 | Fourteen contract guarantees, each pinned by a test, and the known limits stated openly. Close: verified at source, paid safely, split fairly, checkable by anyone. |

---

## 4. Commands on camera (in order)

```bash
make check-env
make show-db
make test-contracts
```

## 5. If something goes wrong on camera

| Problem | Fix |
|---|---|
| "Stellar testnet did not answer in time" | Testnet is slow; retry once. Nothing is saved unless the transaction succeeds. |
| `make check-env` shows a red ✕ | It names the fix. Usually terminal 1 isn't running `make run-frappe`. |
| Buyer balance shows "—" | A testnet read timed out; reload the page. |
| Buyer can't pay | **Top up 500,000 RWF (testnet)** on the Buyer screen, or pay a smaller amount. |
| ODK import says "already imported" | Make a new file: `python3 odk/sample_submission.py <lot ref> > ~/Desktop/odk-inspection.xml` |
| ODK import says the lot is not awaiting inspection | That lot was already inspected; register a new one and make a file for it. |
| Explorer shows no live events | Do one trade on the screens, or run `make demo`. The RPC only keeps about a week. |
| Desk asks you to log in | Log in off camera, then come back to the tab. |

## 6. After recording

1. Trim the transaction waits; keep the total under 10 minutes.
2. Upload (YouTube unlisted, or Google Drive with link access).
3. Put the link in `README.md` (the *Demo video* line) and commit.
