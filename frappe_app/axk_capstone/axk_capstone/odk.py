"""Offline inspection with ODK (roadmap INSP-6).

Inspectors often work where there is no connection. They fill the AXK inspection form (odk/axk_inspection.xlsx)
in ODK Collect, offline; when the submission reaches AXK it is signed on-chain exactly like an inspection made
on /trade/inspect. The report record (and so its on-chain digest) includes the SHA-256 of the original ODK
submission and its instance ID, so the chain commits to what was captured in the field, and the same
submission can never be imported twice.

`parse_submission` is pure (no Frappe) and unit-tested in scripts/test_odk.py.
"""

import hashlib
import re
import xml.etree.ElementTree as ET

FORM_ID = "axk_inspection"

# Choice codes used in the form -> the reason text stored on the lot. Must match chain.REJECT_REASONS
# (checked when the endpoint runs).
REJECT_CODES = {
    "moisture": "Moisture above tolerance",
    "weight": "Weight below declared",
    "foreign_matter": "Foreign matter or defects",
    "grade": "Grade below declared",
    "pests": "Pest or mould damage",
    "documents": "Documents missing or inconsistent",
}
GRADES = ("A", "B", "C")


class SubmissionError(ValueError):
    pass


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _fields(root):
    """Flatten the instance: {leaf element name: text}. ODK nests meta/ and any groups."""
    out = {}
    for el in root.iter():
        if len(el) == 0:
            out[_local(el.tag)] = (el.text or "").strip()
    return out


def lot_ref_from(value):
    """A lot reference, typed or scanned. The lot's QR encodes the /trace/lot?ref=... URL."""
    value = (value or "").strip()
    m = re.search(r"[?&]ref=([^&#\s]+)", value)
    if m:
        from urllib.parse import unquote

        value = unquote(m.group(1))
    return value[:128]


def _number(fields, name, low, high):
    raw = fields.get(name, "")
    try:
        n = float(raw)
    except ValueError:
        raise SubmissionError(f"{name} is not a number: {raw!r}")
    if not (low <= n <= high):
        raise SubmissionError(f"{name} {n} is outside {low}–{high}")
    return n


def parse_submission(xml_bytes):
    """Validate an ODK submission of the AXK inspection form and return the inspection it describes."""
    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode("utf-8")
    if len(xml_bytes) > 256 * 1024:
        raise SubmissionError("Submission is larger than 256 KB")
    if b"<!DOCTYPE" in xml_bytes or b"<!ENTITY" in xml_bytes:
        raise SubmissionError("DTDs and entities are not accepted")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise SubmissionError(f"Not valid XML: {e}")
    if root.get("id") != FORM_ID:
        raise SubmissionError(f"This is not an AXK inspection submission (form id {root.get('id')!r})")
    f = _fields(root)

    instance_id = f.get("instanceID", "")
    if not re.fullmatch(r"uuid:[0-9a-fA-F-]{36}", instance_id):
        raise SubmissionError("Submission has no valid instanceID")
    lot_ref = lot_ref_from(f.get("lot_qr") or f.get("lot_ref"))
    if len(lot_ref) < 4:
        raise SubmissionError("Submission has no lot reference")

    result = f.get("result", "")
    if result not in ("pass", "reject"):
        raise SubmissionError("result must be pass or reject")
    passed = result == "pass"
    grade = f.get("grade", "")
    if grade not in GRADES:
        raise SubmissionError(f"grade must be one of {', '.join(GRADES)}")
    reject_reason = None
    if not passed:
        reject_reason = REJECT_CODES.get(f.get("reject_reason", ""))
        if not reject_reason:
            raise SubmissionError("A rejection needs a reason from the list")

    return {
        "lot_ref": lot_ref,
        "passed": passed,
        "grade": grade,
        "quantity_kg": _number(f, "quantity_kg", 0.001, 1_000_000),
        "moisture_pct": _number(f, "moisture_pct", 0, 40),
        "reject_reason": reject_reason,
        "notes": f.get("notes", "")[:500],
        "field_capture": {
            "source": "odk",
            "form_id": FORM_ID,
            "form_version": root.get("version") or "",
            "instance_id": instance_id,
            "captured_start": f.get("start", ""),
            "captured_end": f.get("end", ""),
            "submission_sha256": hashlib.sha256(xml_bytes).hexdigest(),
        },
    }


def _guest_post(fn):
    """frappe.whitelist when running inside Frappe; a no-op for the pure unit tests."""
    try:
        import frappe
    except ImportError:
        return fn
    return frappe.whitelist(allow_guest=True, methods=["POST"])(fn)


@_guest_post
def import_submission():
    """Sign the inspection described by one ODK submission. Same access guard and rate limit as the
    Inspector screen.

    POST /api/method/axk_capstone.odk.import_submission with the submission XML as the request body
    (Content-Type: application/xml). The raw body is used because form fields are HTML-escaped by Frappe,
    which would change the XML and its digest."""
    import frappe

    from axk_capstone import chain, trade_api

    trade_api._guard()
    xml = frappe.request.get_data(cache=True) or b""
    if sorted(REJECT_CODES.values()) != sorted(chain.REJECT_REASONS):
        frappe.throw("ODK rejection codes are out of step with chain.REJECT_REASONS")
    try:
        s = parse_submission(xml or "")
    except SubmissionError as e:
        frappe.throw(str(e), title="ODK submission refused")

    if frappe.get_all(trade_api.DT, filters={"report_record": ["like", f"%{s['field_capture']['instance_id']}%"]}, limit=1):
        frappe.throw(f"Submission {s['field_capture']['instance_id']} was already imported", title="ODK submission refused")
    name = frappe.db.get_value(trade_api.DT, {"lot_ref": s["lot_ref"]}, "name")
    if not name:
        frappe.throw(f"No lot {s['lot_ref']}", title="ODK submission refused")

    trade_api._throttle()
    doc = frappe.get_doc(trade_api.DT, name)
    if doc.status != "Registered":
        frappe.throw(f"{doc.lot_ref} is {doc.status}, not awaiting inspection", title="ODK submission refused")
    try:
        chain.inspect_lot(doc, s["passed"], s["grade"], s["quantity_kg"], s["moisture_pct"], s["notes"],
                          s["reject_reason"], field_capture=s["field_capture"])
        doc.last_error = None
        doc.save(ignore_permissions=True)
    except chain.ChainError as e:
        trade_api._fail(doc, e)
    frappe.db.commit()
    chain.forget_balances()
    return trade_api.lot(doc.name) | {"field_capture": s["field_capture"]}
