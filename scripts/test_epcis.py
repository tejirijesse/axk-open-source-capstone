"""Unit tests for the GS1 EPCIS 2.0 export (frappe_app/axk_capstone/axk_capstone/epcis.py).

No server needed. If `jsonschema` is installed and the official GS1 schema can be downloaded, every exported
document is also validated against it; otherwise those checks are skipped and the structural tests still run.

    python3 scripts/test_epcis.py
"""

import json
import os
import sys
import unittest
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frappe_app", "axk_capstone"))
from axk_capstone.epcis import build_document  # noqa: E402

SCHEMA_URL = "https://ref.gs1.org/standards/epcis/epcis-json-schema.json"
EXPLORER = "https://stellar.expert/explorer/testnet"
TX = {k: (str(i) * 64)[:64] for i, k in enumerate(
    ["register_tx", "inspect_tx", "fund_tx", "dispatch_tx", "port_tx", "release_tx", "split_tx", "distribute_tx", "attest_tx"], 1)}

SETTLED = {
    "lot_ref": "AXK-KGL-COFFEE-20261015-0001", "status": "Settled", "commodity": "Coffee (parchment)",
    "declared_grade": "A", "quantity_kg": 3850.0, "origin": "Huye District, Southern Province, Rwanda",
    "cooperative_name": "Koperative Twitezimbere (demo)", "chain_lot_id": "ab" * 32, "lot_digest": "11" * 32,
    "registered_at": "2026-10-15 09:00:00", "passed": 1, "inspected_grade": "A", "inspected_quantity_kg": 3820.0,
    "moisture_pct": 11.5, "report_digest": "22" * 32, "inspected_at": "2026-10-15 10:00:00",
    "trade_id": "cd" * 32, "amount_rwf": 250000.0, "funded_at": "2026-10-15 11:00:00",
    "carrier_name": "Demo Carrier", "seal_number": "RW-SEAL-000001", "destination_port": "Kigali Logistics Platform",
    "waybill_ref": "WB-AXK-KGL-COFFEE-20261015-0001", "waybill_digest": "33" * 32, "dispatched_at": "2026-10-15 12:00:00",
    "port_name": "Kigali Logistics Platform", "container_id": "AXKU0000001", "customs_ref": "C-2026-0001",
    "seal_verified": 1, "port_receipt_digest": "44" * 32, "port_received_at": "2026-10-15 13:00:00",
    "attest_digest": "55" * 32, "settled_at": "2026-10-15 14:00:00",
    # Private fields that must never reach the export, even if a caller passes them in.
    "inspector_name": "PRIVATE-INSPECTOR", "buyer_name": "PRIVATE-BUYER", "inspection_notes": "PRIVATE-NOTES",
    **TX,
}


def iso(value):
    """Stand-in for trade_api._iso: Kigali time (+02:00)."""
    return datetime.fromisoformat(str(value)).isoformat() + "+02:00" if value else ""


def load_schema():
    try:
        import jsonschema  # noqa: F401
        with urllib.request.urlopen(SCHEMA_URL, timeout=10) as r:
            return json.load(r)
    except Exception:
        return None


SCHEMA = load_schema()


class EpcisExport(unittest.TestCase):
    def doc(self, lot):
        return build_document(lot, iso, explorer=EXPLORER, created="2026-10-15T12:00:00+00:00")

    def assertValidEpcis(self, doc):
        if SCHEMA is None:
            self.skipTest("jsonschema or the GS1 schema is not available")
        import jsonschema
        jsonschema.validate(doc, SCHEMA, format_checker=jsonschema.FormatChecker())

    def test_settled_lot_has_every_step_in_order(self):
        events = self.doc(SETTLED)["epcisBody"]["eventList"]
        self.assertEqual([e["axk:proof"]["axk:step"] for e in events],
                         ["register", "inspect", "fund", "dispatch", "gate-in", "settle"])
        self.assertEqual([e.get("bizStep") for e in events],
                         ["commissioning", "inspecting", "holding", "shipping", "receiving", "accepting"])

    def test_settled_lot_validates_against_gs1_schema(self):
        self.assertValidEpcis(self.doc(SETTLED))

    def test_steps_and_dispositions_are_standard_cbv_values(self):
        # The schema also accepts any URI here, so check against its CBV enumerations explicitly.
        if SCHEMA is None:
            self.skipTest("the GS1 schema is not available")
        defs = SCHEMA["definitions"]
        cbv = {k: next(a["enum"] for a in defs[k]["anyOf"] if "enum" in a) for k in ("bizStep", "disposition")}
        for e in self.doc(SETTLED)["epcisBody"]["eventList"]:
            self.assertIn(e["bizStep"], cbv["bizStep"])
            self.assertIn(e["disposition"], cbv["disposition"])

    def test_each_event_links_its_stellar_transaction_and_digest(self):
        events = self.doc(SETTLED)["epcisBody"]["eventList"]
        reg = events[0]
        self.assertEqual(reg["certificationInfo"], f"{EXPLORER}/tx/{TX['register_tx']}")
        self.assertEqual(reg["axk:proof"]["axk:recordSha256"], SETTLED["lot_digest"])
        self.assertEqual(events[3]["axk:proof"]["axk:recordSha256"], SETTLED["waybill_digest"])
        self.assertEqual(events[4]["axk:proof"]["axk:recordSha256"], SETTLED["port_receipt_digest"])
        self.assertTrue(all(e["eventTimeZoneOffset"] == "+02:00" for e in events))

    def test_rejected_lot_stops_at_inspection(self):
        lot = {k: v for k, v in SETTLED.items() if k in (
            "lot_ref", "commodity", "declared_grade", "quantity_kg", "origin", "cooperative_name", "chain_lot_id",
            "lot_digest", "registered_at", "register_tx", "inspected_grade", "inspected_quantity_kg", "moisture_pct",
            "report_digest", "inspected_at", "inspect_tx")}
        lot.update(passed=0, reject_reason="Moisture above tolerance")
        doc = self.doc(lot)
        events = doc["epcisBody"]["eventList"]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["disposition"], "non_conformant")
        self.assertEqual(events[1]["axk:rejectReason"], "Moisture above tolerance")
        self.assertValidEpcis(doc)

    def test_registered_only_lot(self):
        lot = {k: SETTLED[k] for k in ("lot_ref", "quantity_kg", "origin", "lot_digest", "registered_at", "register_tx")}
        events = self.doc(lot)["epcisBody"]["eventList"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "ADD")

    def test_no_private_fields_are_exported(self):
        text = json.dumps(self.doc(SETTLED))
        for secret in ("PRIVATE-INSPECTOR", "PRIVATE-BUYER", "PRIVATE-NOTES"):
            self.assertNotIn(secret, text)

    def test_event_ids_are_stable(self):
        a = [e["eventID"] for e in self.doc(SETTLED)["epcisBody"]["eventList"]]
        b = [e["eventID"] for e in self.doc(dict(SETTLED))["epcisBody"]["eventList"]]
        self.assertEqual(a, b)
        self.assertEqual(len(set(a)), len(a))


if __name__ == "__main__":
    unittest.main(verbosity=2)
