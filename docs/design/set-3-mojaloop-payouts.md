# SET-3 · Paying members through Mojaloop: design note

**Status:** draft for review. **Roadmap:** SET-3 (design), related to SET-2 (cash-out through a SEP-24 anchor).

## Problem

Settlement ends today with each member's share paid in the RWF test token to a Stellar account. Members of a
rural cooperative do not use Stellar accounts; they use mobile money. The question is how a settled share
reaches a member's mobile-money wallet, and what AXK must record so the payout stays as verifiable as the
rest of the trade.

## Background: what Mojaloop is

[Mojaloop](https://mojaloop.io) is open-source software for running a payment switch that connects banks and
mobile-money providers (in Mojaloop terms, DFSPs: digital financial service providers). A payment on Mojaloop
has three phases:

1. **Discovery:** the payer's DFSP asks the switch who holds an identifier, such as a phone number
   (`GET /parties/MSISDN/{number}`).
2. **Agreement:** the two DFSPs agree the amount and fees (`POST /quotes`).
3. **Transfer:** the funds move, conditionally, and are committed or rejected (`POST /transfers`).

Settlement between DFSPs happens afterwards, under the switch's settlement model. Several national switches
in Africa are built on Mojaloop; check the current list on mojaloop.io before citing one.

## Constraint that shapes the design

**Only licensed DFSPs connect to a Mojaloop switch.** AXK is not a DFSP and will not become one. So AXK never
calls Mojaloop itself; a licensed partner does. AXK's job is to:

1. hand the partner a precise, signed payout instruction, and
2. record the partner's result, so `/trace` can show the member was paid.

## Two routes

| | A · Stellar anchor (SET-2) | B · DFSP partner on a Mojaloop switch |
|---|---|---|
| How the money leaves Stellar | The cooperative's account sends tokens to an anchor through SEP-24; the anchor pays out locally | A DFSP that holds a Stellar account receives the tokens, then pays members through the switch |
| Who AXK integrates with | One anchor, through a published Stellar standard (SEP-24) | One DFSP, through a bilateral API; Mojaloop is behind the DFSP |
| Reach | Whatever providers the anchor pays into | Every bank and wallet on the switch, through one partner |
| Testable without a partner | Yes, with the Stellar test anchor | Partly: the Mojaloop Testing Toolkit simulates a switch and DFSPs |
| Main risk | Few anchors serve RWF payouts to mobile money | Partnering with a licensed DFSP takes commercial and regulatory work |

They are not exclusive. Both start from the same thing: a payout instruction AXK can prove it issued.

## Proposed design: a route-agnostic payout record

After `distribute`, AXK creates one **payout instruction** per member share:

```json
{
  "trade_id": "…",
  "member_index": 0,
  "amount_rwf": 100000,
  "payee_ref": "sha256(salt ‖ MSISDN)",
  "route": "sep24 | dfsp",
  "issued_at": "2026-10-15T14:00:00+02:00"
}
```

- **Privacy:** the phone number is never on-chain or on `/trace`. AXK stores a salted hash; the plaintext is
  sent only to the payout partner over its authenticated API.
- **Commitment:** the SHA-256 of the instruction is attested on-chain with the existing attestation contract
  (`attest(sha256("payout:" ‖ trade ‖ index), digest)`), so AXK cannot later change who was meant to be
  paid, or how much.
- **Result:** the partner returns its reference (the SEP-24 transaction ID, or the DFSP's transfer ID, which
  for route B corresponds to the Mojaloop `transferId`) and a status. AXK records a payout-result record and
  attests its digest the same way.
- **Trace:** `/trace` gains a "Members paid out" step per share: instruction attested, result attested,
  partner reference, and no personal data.

For route B, the partner DFSP keeps the Mojaloop side entirely: discovery by MSISDN, quote and transfer. A
DFSP typically connects to the switch with Mojaloop's SDK scheme adapter. AXK needs only the partner's payout
API, ideally a thin request/response mirroring the instruction above.

## Failure cases

| Case | Handling |
|---|---|
| The phone number is not found on the switch (discovery fails) | Result `payee_not_found`; the share stays with the cooperative's account and `/trace` shows "payout pending" |
| The transfer is rejected or times out | Result `failed` with the partner's reason; retry under a new instruction index, never by editing the old one |
| A duplicate request reaches the partner | The instruction digest is the idempotency key |
| The partner reports success but the member disputes it | The attested instruction and result, plus the partner's transfer ID, are the audit trail |

## Recommendation

1. Build the **payout instruction and result records** and their attestations now. They are needed by both
   routes and testable on testnet (new roadmap item, SET-4).
2. Prove route A in a sandbox first (SET-2), since it needs no commercial partner.
3. For route B, run the partner API against the **Mojaloop Testing Toolkit** with a simulated DFSP before
   approaching a real DFSP. That shows the integration works without anyone's money.

## Open questions for reviewers

- Should the cooperative or AXK hold the payout float between `distribute` and cash-out?
- Is a salted phone-number hash enough, or does the partner need a stronger pseudonymous member ID?
- Which regulator approvals does each route need in Rwanda? (Legal input, not engineering.)
