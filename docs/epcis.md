# GS1 EPCIS 2.0 export

Every lot's public history can be downloaded as a [GS1 EPCIS 2.0](https://ref.gs1.org/standards/epcis/)
JSON-LD document, the standard that customs, exporters and traceability systems use for "what happened to this
item, where and when". The export is built in `frappe_app/axk_capstone/axk_capstone/epcis.py` (roadmap PUB-6).

```
GET /api/method/axk_capstone.epcis.lot_events?ref=<lot ref>              view (application/ld+json)
GET /api/method/axk_capstone.epcis.lot_events?ref=<lot ref>&download=1   download <ref>.epcis.jsonld
```

No login. The public trace page (`/trace/lot`) links to it under *Export for supply-chain systems*. It
works on the full stack only; the offline simulation does not serve it.

## What is exported

Only the fields `/trace` already shows publicly (`verify.PUBLIC_FIELDS`). Inspector and buyer names, notes and
anything about individual farmers are never exported, and a unit test checks this.

## Mapping

| AXK step | EPCIS event | `action` | `bizStep` | `disposition` | Record digest |
|---|---|---|---|---|---|
| Lot registered | ObjectEvent | ADD | `commissioning` | `active` | `lot_digest` |
| Inspected | ObjectEvent | OBSERVE | `inspecting` | `conformant` / `non_conformant` | `report_digest` |
| Escrow funded | TransactionEvent | ADD | `holding` | `reserved` | — |
| Dispatched | ObjectEvent | OBSERVE | `shipping` | `in_transit` | `waybill_digest` |
| Port gate-in | ObjectEvent | OBSERVE | `receiving` | `in_progress` | `port_receipt_digest` |
| Settled | ObjectEvent | OBSERVE | `accepting` | `sellable_accessible` | `attest_digest` |

An event appears only once its step has a Stellar transaction, so a rejected lot exports two events and a
settled lot six.

- **What:** the lot is a class-level quantity, `quantityList: [{epcClass: "urn:axk:lot:<ref>", quantity, uom: "KGM"}]`.
- **Where:** `readPoint` / `bizLocation` use `urn:axk:loc:<slug>` built from the origin district or port name.
- **Why:** the trade is a business transaction of type `po` (`urn:axk:trade:<trade id>`); the waybill is a `bol`.
- **Proof:** `certificationInfo` is the Stellar Expert link to the transaction that anchored the step, and
  `axk:proof` holds the step name, the record's SHA-256 digest and the transaction hash.
- **Event IDs** are UUIDv5 values derived from the lot reference and step, so re-exporting a lot gives the
  same IDs and a receiving system can de-duplicate.

## The `axk:` extension fields

EPCIS allows extension fields in a declared namespace. AXK's namespace is this page
(`https://github.com/tejirijesse/axk-open-source-capstone/blob/main/docs/epcis.md#`).

| Field | Event | Meaning |
|---|---|---|
| `axk:proof` | all | `axk:step`, `axk:recordSha256`, `axk:stellarTx` |
| `axk:commodity`, `axk:declaredGrade`, `axk:cooperative`, `axk:chainLotId` | register | Lot details; `chainLotId` is the lot's ID in the lot registry contract |
| `axk:inspectedGrade`, `axk:moisturePct`, `axk:rejectReason` | inspect | Inspection result |
| `axk:escrowAmountRwf` | fund | Amount locked in escrow (RWF test token) |
| `axk:carrier`, `axk:sealNumber` | dispatch | Carrier and container seal |
| `axk:containerId`, `axk:customsRef`, `axk:sealVerified` | gate-in | Port receipt details |
| `axk:releaseTx`, `axk:splitTx`, `axk:distributeTx` | settle | The other settlement transactions |

## Checking an export

1. Validate it against the official schema (`https://ref.gs1.org/standards/epcis/epcis-json-schema.json`), or
   load it into any EPCIS 2.0 repository such as openEPCIS.
2. For any event, open `certificationInfo` to see the transaction on Stellar testnet, and compare
   `axk:recordSha256` with the digest the contract stored.

## Tests

```bash
make test-epcis     # python3 scripts/test_epcis.py
```

The tests need no server. If `jsonschema` is installed (`pip install jsonschema`) and the GS1 schema can be
downloaded, each document is validated against it and every `bizStep` and `disposition` is checked against the
standard CBV values; otherwise those checks are skipped.

## Limits and next steps

- Identifiers are AXK URNs, not GS1 keys. A cooperative with a GS1 company prefix could export SGTIN/LGTIN
  identifiers and GLN locations instead; that needs a per-cooperative setting.
- The port step is attested by the AXK verifier key on the port's behalf (see [security.md](security.md)).
  The EPCIS event records what the application attested, not a signature by the port itself.
- There is no EPCIS query interface; this is a per-lot export. Capturing events into an external EPCIS
  repository automatically is a natural follow-up.
