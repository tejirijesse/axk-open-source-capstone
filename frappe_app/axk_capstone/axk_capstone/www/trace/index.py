"""Context for /trace, public lot search."""

import frappe

from axk_capstone import custody
from axk_capstone.verify import DT, TX_FIELDS, search
from axk_capstone.web import _stamp, page

no_cache = 1

ROW_FIELDS = ["lot_ref", "status", "passed", "commodity", "origin", "cooperative_name"] + TX_FIELDS


def _with_custody(rows):
    """Attach the micro-strip state to each row; the tx hashes and pass flag are dropped."""
    for r in rows:
        rejected = custody.is_rejected(r)
        txs = [r.get(f) for f in TX_FIELDS]
        n, nxt = custody.summary(txs, rejected)
        r.custody = {"states": custody.notches(txs, rejected), "n": n, "next": nxt, "rejected": rejected}
        for f in TX_FIELDS + ["passed"]:
            r.pop(f, None)
    return rows


def get_context(context):
    page(context, "verify", "Verify a lot · AXK")
    context.trace_css_v = _stamp("css/trace.css")
    context.q = (frappe.form_dict.get("q") or "").strip()[:128]
    hits = search(context.q) if context.q else []
    if len(hits) == 1:
        frappe.local.flags.redirect_location = "/trace/lot?ref=" + frappe.utils.quote(hits[0].lot_ref)
        raise frappe.Redirect
    context.results = _with_custody(frappe.get_all(
        DT, fields=ROW_FIELDS, filters={"lot_ref": ["in", [h.lot_ref for h in hits]]})) if hits else []
    context.recent = _with_custody(frappe.get_all(DT, fields=ROW_FIELDS, order_by="modified desc", limit=8))
    return context
