"""GS1 EPCIS 2.0 export of a lot's public history (roadmap PUB-6).

EPCIS is the GS1 standard for "what happened to this item, where and when". Exporting a lot as an EPCIS 2.0
JSON-LD document lets customs, exporters and buyers' supply-chain systems read AXK records without learning
AXK's own format. See docs/epcis.md for the mapping.

Only fields that /trace already shows publicly are exported (verify.PUBLIC_FIELDS): no inspector or buyer
names, notes, or farmer data. Each event carries the record digest and the Stellar transaction that anchors
it, so a reader can check the event against the chain.

`build_document` is pure (no Frappe), so it is unit-tested against the official GS1 JSON schema in
scripts/test_epcis.py.
"""

import re
import uuid
from datetime import datetime, timezone

EPCIS_CONTEXT = "https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"
AXK_NS = "https://github.com/tejirijesse/axk-open-source-capstone/blob/main/docs/epcis.md#"
# Stable namespace for deterministic event IDs: the same lot always exports the same event IDs.
EVENT_ID_NS = uuid.uuid5(uuid.NAMESPACE_URL, AXK_NS)


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "unknown"


def lot_uri(lot_ref):
    return "urn:axk:lot:" + _slug(lot_ref)


def location_uri(name):
    return "urn:axk:loc:" + _slug(name)


def _offset(iso):
    """'+02:00' from an ISO-8601 timestamp that carries an offset."""
    m = re.search(r"([+-]\d{2}:\d{2})$", iso)
    if m:
        return m.group(1)
    return "+00:00" if iso.endswith("Z") else None


def _event(lot, step, event_type, when, digest, tx, explorer, **fields):
    ev = {
        "type": event_type,
        "eventTime": when,
        "eventTimeZoneOffset": _offset(when) or "+00:00",
        "eventID": "urn:uuid:" + str(uuid.uuid5(EVENT_ID_NS, f"{lot['lot_ref']}:{step}")),
    }
    if tx and explorer:
        ev["certificationInfo"] = f"{explorer}/tx/{tx}"
    ev.update(fields)
    ev["axk:proof"] = {"axk:step": step, "axk:recordSha256": digest or "", "axk:stellarTx": tx or ""}
    return ev


def _quantity(lot, kg):
    return [{"epcClass": lot_uri(lot["lot_ref"]), "quantity": float(kg or 0), "uom": "KGM"}]


def build_document(lot, iso, explorer=None, created=None):
    """EPCIS 2.0 document for one lot.

    lot      -- dict with verify.PUBLIC_FIELDS
    iso      -- function turning a stored datetime into an ISO-8601 string with offset ('' if empty)
    explorer -- block explorer base URL; each anchored event links its transaction as certificationInfo
    """
    events = []
    origin = location_uri(lot.get("origin"))
    trade = [{"type": "po", "bizTransaction": "urn:axk:trade:" + lot["trade_id"]}] if lot.get("trade_id") else []

    if lot.get("register_tx") and iso(lot.get("registered_at")):
        events.append(_event(
            lot, "register", "ObjectEvent", iso(lot["registered_at"]), lot.get("lot_digest"), lot["register_tx"], explorer,
            action="ADD", bizStep="commissioning", disposition="active",
            quantityList=_quantity(lot, lot.get("quantity_kg")),
            readPoint={"id": origin}, bizLocation={"id": origin},
            **{"axk:commodity": lot.get("commodity") or "", "axk:declaredGrade": lot.get("declared_grade") or "",
               "axk:cooperative": lot.get("cooperative_name") or "", "axk:chainLotId": lot.get("chain_lot_id") or ""},
        ))

    if lot.get("inspect_tx") and iso(lot.get("inspected_at")):
        passed = bool(lot.get("passed"))
        extra = {"axk:inspectedGrade": lot.get("inspected_grade") or "", "axk:moisturePct": float(lot.get("moisture_pct") or 0)}
        if not passed:
            extra["axk:rejectReason"] = lot.get("reject_reason") or ""
        events.append(_event(
            lot, "inspect", "ObjectEvent", iso(lot["inspected_at"]), lot.get("report_digest"), lot["inspect_tx"], explorer,
            action="OBSERVE", bizStep="inspecting", disposition="conformant" if passed else "non_conformant",
            quantityList=_quantity(lot, lot.get("inspected_quantity_kg") or lot.get("quantity_kg")),
            readPoint={"id": origin}, **extra,
        ))

    if lot.get("fund_tx") and trade and iso(lot.get("funded_at")):
        events.append(_event(
            lot, "fund", "TransactionEvent", iso(lot["funded_at"]), None, lot["fund_tx"], explorer,
            action="ADD", bizStep="holding", disposition="reserved", bizTransactionList=trade,
            quantityList=_quantity(lot, lot.get("inspected_quantity_kg") or lot.get("quantity_kg")),
            **{"axk:escrowAmountRwf": float(lot.get("amount_rwf") or 0)},
        ))

    if lot.get("dispatch_tx") and iso(lot.get("dispatched_at")):
        waybill = [{"type": "bol", "bizTransaction": "urn:axk:waybill:" + _slug(lot.get("waybill_ref"))}] if lot.get("waybill_ref") else []
        events.append(_event(
            lot, "dispatch", "ObjectEvent", iso(lot["dispatched_at"]), lot.get("waybill_digest"), lot["dispatch_tx"], explorer,
            action="OBSERVE", bizStep="shipping", disposition="in_transit",
            quantityList=_quantity(lot, lot.get("inspected_quantity_kg") or lot.get("quantity_kg")),
            readPoint={"id": origin}, bizTransactionList=trade + waybill,
            destinationList=[{"type": "location", "destination": location_uri(lot.get("destination_port"))}] if lot.get("destination_port") else [],
            **{"axk:carrier": lot.get("carrier_name") or "", "axk:sealNumber": lot.get("seal_number") or ""},
        ))

    if lot.get("port_tx") and iso(lot.get("port_received_at")):
        port = location_uri(lot.get("port_name"))
        events.append(_event(
            lot, "gate-in", "ObjectEvent", iso(lot["port_received_at"]), lot.get("port_receipt_digest"), lot["port_tx"], explorer,
            action="OBSERVE", bizStep="receiving", disposition="in_progress",
            quantityList=_quantity(lot, lot.get("inspected_quantity_kg") or lot.get("quantity_kg")),
            readPoint={"id": port}, bizLocation={"id": port}, bizTransactionList=trade,
            **{"axk:containerId": lot.get("container_id") or "", "axk:customsRef": lot.get("customs_ref") or "",
               "axk:sealVerified": bool(lot.get("seal_verified"))},
        ))

    if lot.get("attest_tx") and iso(lot.get("settled_at")):
        events.append(_event(
            lot, "settle", "ObjectEvent", iso(lot["settled_at"]), lot.get("attest_digest"), lot["attest_tx"], explorer,
            action="OBSERVE", bizStep="accepting", disposition="sellable_accessible",
            quantityList=_quantity(lot, lot.get("inspected_quantity_kg") or lot.get("quantity_kg")),
            bizTransactionList=trade,
            **{"axk:releaseTx": lot.get("release_tx") or "", "axk:splitTx": lot.get("split_tx") or "",
               "axk:distributeTx": lot.get("distribute_tx") or ""},
        ))

    # Drop empty optional lists: EPCIS readers expect them to be absent rather than empty.
    for ev in events:
        for key in ("bizTransactionList", "destinationList"):
            if key in ev and not ev[key]:
                del ev[key]

    return {
        "@context": [EPCIS_CONTEXT, {"axk": AXK_NS}],
        "type": "EPCISDocument",
        "schemaVersion": "2.0",
        "creationDate": created or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "epcisBody": {"eventList": events},
    }


def _guest_get(fn):
    """frappe.whitelist when running inside Frappe; a no-op for the pure unit tests."""
    try:
        import frappe
    except ImportError:
        return fn
    return frappe.whitelist(allow_guest=True, methods=["GET"])(fn)


@_guest_get
def lot_events(ref=None, download=0):
    """Public EPCIS export: /api/method/axk_capstone.epcis.lot_events?ref=<lot ref>[&download=1]"""
    import json

    import frappe

    from axk_capstone import chain
    from axk_capstone.trade_api import _iso
    from axk_capstone.verify import public_lot

    ref = (ref or "").strip()[:128]
    lot = public_lot(ref) if ref else None
    if not lot:
        frappe.throw("No lot with that reference.", frappe.DoesNotExistError)
    doc = build_document(lot, _iso, explorer=chain.EXPLORER)
    frappe.response["type"] = "download"
    frappe.response["content_type"] = "application/ld+json"
    frappe.response["filename"] = f"{ref}.epcis.jsonld"
    frappe.response["display_content_as"] = "attachment" if str(download) == "1" else "inline"
    frappe.response["filecontent"] = json.dumps(doc, indent=2, ensure_ascii=False)
