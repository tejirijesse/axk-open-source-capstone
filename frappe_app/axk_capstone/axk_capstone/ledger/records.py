"""Canonical records.

Every record a participant signs for (a lot, an inspection report, a waybill, a port receipt, a settlement) is
serialised as canonical JSON (sorted keys, no whitespace) and hashed with SHA-256. The record stays in the
application database; only the 64-character digest is written to Stellar. Anyone holding the record can re-hash
it and compare with the chain, so a changed record is detectable without trusting the database.
"""

import hashlib
import json
from abc import ABC, abstractmethod


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(obj):
    """Deterministic JSON: the same fields always produce the same bytes, and so the same digest."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CanonicalRecord(ABC):
    """A record whose canonical JSON is hashed. Subclasses decide which trade fields it carries."""

    def __init__(self, **fields):
        self._fields = fields

    @classmethod
    @abstractmethod
    def from_trade(cls, trade, **context):
        """Build the record from a trade document plus the values the current step supplies."""

    @property
    def fields(self):
        return dict(self._fields)

    def canonical(self):
        return canonical(self._fields)

    def digest(self):
        return sha256_hex(self.canonical())

    def matches(self, digest):
        return self.digest() == digest

    @staticmethod
    def digest_of(stored_canonical):
        """Re-hash a record as stored in the database, to compare with what the chain holds."""
        return sha256_hex(stored_canonical)


class AttestedRecord(CanonicalRecord):
    """A record anchored in the attestation contract under a key derived from the trade."""

    @staticmethod
    @abstractmethod
    def attestation_key(trade):
        """The 32-byte key (hex) the attestation contract stores this record's digest under."""


class LotRecord(CanonicalRecord):
    """What the cooperative declares when it registers a lot."""

    @classmethod
    def from_trade(cls, trade, cooperative):
        return cls(
            lot_ref=trade.lot_ref, commodity=trade.commodity, variety=trade.variety or "",
            declared_grade=trade.declared_grade, quantity_kg=trade.quantity_kg, origin=trade.origin,
            harvest_date=str(trade.harvest_date or ""), cooperative=cooperative,
        )

    @staticmethod
    def registry_ref(trade):
        """The lot reference as the registry sees it: hashed, so the plain reference never goes on-chain."""
        return sha256_hex("lot:" + trade.lot_ref)


class InspectionReport(CanonicalRecord):
    """The inspector's signed result. field_capture links an offline (ODK) submission to the report."""

    @classmethod
    def from_trade(cls, trade, passed, grade, quantity_kg, moisture_pct, notes, reject_reason, inspector,
                   inspected_at, field_capture=None):
        fields = dict(
            lot_ref=trade.lot_ref, chain_lot_id=trade.chain_lot_id, passed=bool(passed), grade=grade,
            quantity_kg=quantity_kg, moisture_pct=moisture_pct, notes=notes or "",
            reject_reason=None if passed else reject_reason, inspector=inspector, inspected_at=inspected_at,
        )
        if field_capture:
            fields["field_capture"] = field_capture
        return cls(**fields)


class Waybill(AttestedRecord):
    """The carrier's dispatch record: who carries the lot, in which vehicle, under which seal."""

    @classmethod
    def from_trade(cls, trade, carrier, driver, vehicle_plate, seal_number, destination_port, dispatched_at):
        return cls(
            lot_ref=trade.lot_ref, chain_lot_id=trade.chain_lot_id, waybill_ref=trade.waybill_ref,
            carrier=carrier, driver=driver, vehicle_plate=vehicle_plate, seal_number=seal_number,
            origin=trade.origin, destination_port=destination_port, dispatched_at=dispatched_at,
        )

    @staticmethod
    def attestation_key(trade):
        return sha256_hex("waybill:" + trade.waybill_ref)


class PortReceipt(AttestedRecord):
    """The terminal's gate-in record, written only after the arriving seal matched the waybill."""

    @classmethod
    def from_trade(cls, trade, port, container_id, customs_ref, received_at):
        return cls(
            lot_ref=trade.lot_ref, chain_lot_id=trade.chain_lot_id, port=port, container_id=container_id,
            customs_ref=customs_ref, manifest_seal=trade.seal_number, verified_seal=trade.seal_number,
            seal_verified=True, received_at=received_at,
        )

    @staticmethod
    def attestation_key(trade):
        return sha256_hex("port:" + trade.lot_ref + ":" + str(trade.customs_ref))


class SettlementRecord(AttestedRecord):
    """Ties the whole trade together: every earlier digest plus the payment transactions."""

    @classmethod
    def from_trade(cls, trade, amount, token):
        fields = dict(
            lot_ref=trade.lot_ref, chain_lot_id=trade.chain_lot_id, lot_digest=trade.lot_digest,
            report_digest=trade.report_digest, trade_id=trade.trade_id, amount=str(amount), token=token,
            buyer=trade.buyer_account, cooperative=trade.cooperative_account,
            release_tx=trade.release_tx, distribute_tx=trade.distribute_tx,
        )
        if trade.waybill_digest:
            fields["waybill_digest"] = trade.waybill_digest
        if trade.port_receipt_digest:
            fields["port_receipt_digest"] = trade.port_receipt_digest
        return cls(**fields)

    @staticmethod
    def attestation_key(trade):
        return trade.trade_id
