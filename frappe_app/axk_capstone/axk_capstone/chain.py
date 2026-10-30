"""Frappe-facing entry point to the AXK ledger (see the ledger package for the object model).

Custodial signing, matching AXK's Stellar design: the server holds one testnet identity per role in the
stellar-cli keystore and signs on the participant's behalf. The CLI is used rather than hand-built transactions
because escrow funding needs two signatures in one transaction (buyer and verifier), and the CLI assembles and
signs those auth entries correctly.

This module supplies what the ledger classes deliberately do not know about: the site configuration, Frappe's
cache, the site clock and saving a document. The functions below keep the interface trade_api, verify, epcis
and odk already use.
"""

import re

import frappe
from frappe.utils import now_datetime

from axk_capstone.ledger.contracts import (
    Attestation, ChainError, Escrow, LotRegistry, Network, Splitter, StellarCli, Token,
)
from axk_capstone.ledger.records import PortReceipt, Waybill, canonical, sha256_hex
from axk_capstone.ledger.workflow import Personas, TradeWorkflow

__all__ = ["ChainError", "canonical", "sha256_hex"]

EXPLORER = "https://stellar.expert/explorer/testnet"
DECIMALS = 10**7
ESCROW_TERM_DAYS = 30

# Demo personas: which keystore identity signs for which role. Names are fictional.
PERSONAS = {
    "coop": {"identity": "axk-coop", "name": "Koperative Twisungane (demo)", "role": "Cooperative"},
    "inspector": {"identity": "axk-inspector", "name": "Inspector J. Mukamana (demo)", "role": "Inspector"},
    "logistics": {"identity": "axk-logistics", "name": "Swift Freight Logistics (demo)", "role": "Logistics Carrier"},
    "port": {"identity": "axk-port", "name": "Kigali Logistics Platform & Terminal (demo)", "role": "Port / Terminal Operator"},
    "buyer": {"identity": "axk-buyer", "name": "Goma Grain Traders (demo)", "role": "Buyer"},
    "verifier": {"identity": "axk-verifier", "name": "AXK verifier service", "role": "Verifier"},
    "member1": {"identity": "axk-member1", "name": "Member 1", "role": "Cooperative member"},
    "member2": {"identity": "axk-member2", "name": "Member 2", "role": "Cooperative member"},
    "issuer": {"identity": "axk-issuer", "name": "RWF test issuer", "role": "Token issuer"},
}
SPLIT_BPS = [("member1", 4000), ("member2", 4000), ("coop", 2000)]

REJECT_REASONS = [
    "Moisture above tolerance", "Weight below declared", "Foreign matter or defects",
    "Grade below declared", "Pest or mould damage", "Documents missing or inconsistent",
]

# Balances are re-read after every transaction (forget_balances), so the cache only has to cover page loads.
BALANCE_TTL = 120
TOKEN_HOLDERS = ("coop", "buyer")
CONTRACT_KEYS = ("registry", "escrow", "splitter", "attestation", "token")


# -- wiring --------------------------------------------------------------------------------------------------

def conf():
    c = frappe.conf.get("axk_stellar") or {}
    missing = [k for k in CONTRACT_KEYS if not c.get(k)]
    if missing:
        raise ChainError(f"axk_stellar site config is missing {', '.join(missing)}")
    return c


def _network(c=None):
    c = c or conf()
    return Network(StellarCli(c.get("stellar_bin") or "stellar"), c.get("network", "testnet"))


def _checkpoint(doc):
    doc.save(ignore_permissions=True)
    frappe.db.commit()


def _workflow():
    c = conf()
    net = _network(c)
    contracts = {"registry": LotRegistry(net, c["registry"]), "escrow": Escrow(net, c["escrow"]),
                 "splitter": Splitter(net, c["splitter"]), "attestation": Attestation(net, c["attestation"])}
    return TradeWorkflow(contracts, Personas(PERSONAS, address), token_id=c["token"], clock=now_datetime,
                         checkpoint=_checkpoint, split_bps=SPLIT_BPS, decimals=DECIMALS,
                         escrow_term_days=ESCROW_TERM_DAYS)


def address(persona):
    key = f"axk_capstone:addr:{persona}"
    cached = frappe.cache().get_value(key)
    if cached:
        return cached
    value = _network().address(PERSONAS[persona]["identity"])
    frappe.cache().set_value(key, value)
    return value


def balance_rwf(persona):
    key = f"axk_capstone:bal:{persona}"
    cached = frappe.cache().get_value(key)
    if cached is not None:
        return cached
    c = conf()
    units = Token(_network(c), c["token"]).balance(PERSONAS["verifier"]["identity"], address(persona))
    value = units / DECIMALS
    frappe.cache().set_value(key, value, expires_in_sec=BALANCE_TTL)
    return value


def forget_balances():
    for p in PERSONAS:
        frappe.cache().delete_value(f"axk_capstone:bal:{p}")


def tx_url(h):
    return f"{EXPLORER}/tx/{h}" if h else None


# -- lifecycle -----------------------------------------------------------------------------------------------

def register_lot(doc):
    """Cooperative commits to the lot record's digest in the lot registry."""
    c = conf()
    for k in CONTRACT_KEYS:
        doc.set(k, c[k])
    _workflow().register(doc)


def inspect_lot(doc, passed, grade, quantity_kg, moisture_pct, notes, reject_reason=None, field_capture=None):
    """Authorised inspector signs one pass/fail inspection against the lot.

    field_capture: for an inspection captured offline (odk.py), the source submission's ID and SHA-256, so the
    report digest on-chain commits to exactly what was recorded in the field."""
    grade = re.sub(r"[^A-Za-z0-9_]", "", grade or "")[:9] or "NA"
    _workflow().inspect(doc, passed, grade, quantity_kg, moisture_pct, notes, reject_reason, field_capture)


def fund_escrow(doc, amount_rwf):
    """Buyer locks payment in escrow. Buyer and verifier both sign; the payee comes from the registry."""
    trade_id = sha256_hex("trade:" + doc.lot_ref + ":" + str(now_datetime()))
    _workflow().fund(doc, amount_rwf, trade_id)


def dispatch_logistics(doc, carrier_name=None, driver_name="Demo Driver", vehicle_plate="RAD 000D",
                       seal_number="RW-SEAL-882194", destination_port="Kigali Logistics Platform"):
    """Logistics carrier takes custody and seals the container; the waybill digest is attested."""
    _workflow().dispatch(
        doc,
        carrier=(carrier_name or PERSONAS["logistics"]["name"]).strip(),
        driver=(driver_name or "Demo Driver").strip(),
        vehicle_plate=(vehicle_plate or "RAD 000D").strip(),
        seal_number=(seal_number or f"SEAL-{doc.lot_ref[-6:]}").strip(),
        destination_port=(destination_port or "Kigali Logistics Platform").strip(),
    )


def receive_port(doc, port_name=None, container_id="MSKU-9182374", customs_ref="RW-CUST-2026-9041", seal_number=None):
    """Port/terminal gate-in: verifies the seal against the waybill and records the customs entry."""
    _workflow().receive_at_port(
        doc,
        port=(port_name or PERSONAS["port"]["name"]).strip(),
        container_id=(container_id or f"CONT-{doc.lot_ref[-6:]}").strip(),
        customs_ref=(customs_ref or f"CUST-RW-{doc.lot_ref[-8:]}").strip(),
        arriving_seal=seal_number,
    )


def settle(doc):
    """Delivery confirmed: release, split, pay members, attest. Resumable after a part-way failure."""
    _workflow().settle(doc)


def waybill_attestation_id(doc):
    return Waybill.attestation_key(doc)


def port_attestation_id(doc):
    return PortReceipt.attestation_key(doc)


def matches_on_chain(doc):
    """Ask the contracts whether the stored records still hash to what was committed."""
    return _workflow().verify(doc)


def top_up_buyer(amount_rwf):
    """Testnet only: the RWF test issuer pays the buyer so demos never run dry."""
    _network().pay(PERSONAS["issuer"]["identity"], address("buyer"), "RWF:" + address("issuer"),
                   int(amount_rwf * DECIMALS))
