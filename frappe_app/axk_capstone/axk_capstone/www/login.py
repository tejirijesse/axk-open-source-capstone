"""Context for /login. Overrides Frappe's login page for this site."""

import frappe

from axk_capstone.trade_api import DT, TX_FIELDS
from axk_capstone.web import _stamp

no_cache = 1
STEPS = ["Registered", "Inspected", "Escrow funded", "Dispatched", "At port", "Released", "Split 40/40/20", "Members paid", "Attested"]


def _specimen():
    """Lot ref and nine tx hashes of the newest settled lot, shown as the brand-panel custody strip. Read-only,
    and the same facts /trace already serves to guests. Empty when no lot has settled: the strip then shows nine
    pending notches rather than invented hashes."""
    try:
        rows = frappe.get_all(DT, filters={"status": "Settled"}, fields=["lot_ref"] + TX_FIELDS,
                              order_by="modified desc", limit=1, ignore_permissions=True)
    except Exception:
        frappe.log_error(title="axk login specimen")
        rows = []
    if not rows:
        return None
    r = rows[0]
    return {"lot_ref": r.lot_ref, "txs": [r.get(f) or "" for f in TX_FIELDS]}


def get_context(context):
    context.title = "Sign in · AXK Trade"
    context.no_breadcrumbs = True
    context.show_sidebar = False
    network = (frappe.conf.get("axk_stellar") or {}).get("network", "testnet")
    context.axk_network = network
    context.axk_explorer = network != "offline-simulation"
    context.steps = STEPS
    context.specimen = _specimen()
    context.css_v = _stamp("css/axk.css")
    context.login_js_v = _stamp("js/login.js")
    return context
