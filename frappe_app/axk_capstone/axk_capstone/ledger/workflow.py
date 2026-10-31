"""The trade lifecycle as a state machine.

    Registered -> Approved | Rejected -> Funded -> In Transit -> At Port -> Settled

Each step checks the trade is in a state that allows it (TRANSITIONS), builds the record for that step, commits
the record's digest on-chain through the contract clients, and only then updates the trade. If a transaction is
refused, ChainError propagates and the trade is left as it was: a hash is never recorded unless it is on-chain.
"""

from datetime import timedelta

from .contracts import ChainError
from .records import InspectionReport, LotRecord, PortReceipt, SettlementRecord, Waybill

# step -> states it may start from (None: no check, the step creates the trade)
TRANSITIONS = {
    "register": None,
    "inspect": ("Registered",),
    "fund": ("Approved",),
    "dispatch": ("Funded", "Approved"),
    "receive_at_port": ("In Transit",),
    "settle": ("At Port", "In Transit", "Funded"),
}
REFUSALS = {
    "inspect": "not awaiting inspection",
    "fund": "only inspected, approved lots can be funded",
    "dispatch": "lot must be Funded or Approved to dispatch",
    "receive_at_port": "lot must be In Transit to receive at port",
    "settle": "only funded or delivered trades can be settled",
}


class Personas:
    """Which keystore identity signs for which role, and how to find its public address."""

    def __init__(self, identities, address_of):
        self._identities = identities      # role -> {"identity", "name", "role"}
        self._address_of = address_of      # role -> public address (cached by the caller)

    def identity(self, role):
        return self._identities[role]["identity"]

    def name(self, role):
        return self._identities[role]["name"]

    def address(self, role):
        return self._address_of(role)


class TradeWorkflow:
    def __init__(self, contracts, personas, token_id, clock, checkpoint, split_bps, decimals=10**7,
                 escrow_term_days=30):
        self.registry = contracts["registry"]
        self.escrow = contracts["escrow"]
        self.splitter = contracts["splitter"]
        self.attestation = contracts["attestation"]
        self.token = contracts.get("token")  # optional: checks the buyer's balance before funding
        self.personas = personas
        self.token_id = token_id
        self.clock = clock                  # returns the current (naive, site-local) datetime
        self.checkpoint = checkpoint        # persists the trade between settlement steps
        self.split_bps = split_bps          # [(role, basis points)], totalling 10,000
        self.decimals = decimals
        self.escrow_term_days = escrow_term_days

    # -- helpers ------------------------------------------------------------------------------------------

    def _require(self, step, trade):
        allowed = TRANSITIONS[step]
        if allowed is not None and trade.status not in allowed:
            raise ChainError(f"{trade.lot_ref} is {trade.status}; {REFUSALS[step]}")

    def _units(self, amount_rwf):
        return int(round(amount_rwf * self.decimals))

    def _sign(self, role):
        return self.personas.identity(role)

    # -- steps --------------------------------------------------------------------------------------------

    def register(self, trade):
        """The cooperative commits to the lot record's digest in the lot registry."""
        self._require("register", trade)
        trade.cooperative_name = self.personas.name("coop")
        trade.cooperative_account = self.personas.address("coop")
        record = LotRecord.from_trade(trade, cooperative=trade.cooperative_account)
        trade.lot_record, trade.lot_digest = record.canonical(), record.digest()
        trade.chain_lot_id, trade.register_tx = self.registry.register_lot(
            self._sign("coop"), LotRecord.registry_ref(trade), trade.lot_digest)
        trade.registered_at = self.clock()
        trade.status = "Registered"

    def inspect(self, trade, passed, grade, quantity_kg, moisture_pct, notes, reject_reason=None, field_capture=None):
        """An authorised inspector signs one pass/fail inspection. The registry refuses a second one."""
        self._require("inspect", trade)
        trade.inspector_name = self.personas.name("inspector")
        trade.inspector_account = self.personas.address("inspector")
        report = InspectionReport.from_trade(
            trade, passed=passed, grade=grade, quantity_kg=quantity_kg, moisture_pct=moisture_pct, notes=notes,
            reject_reason=reject_reason, inspector=trade.inspector_account, inspected_at=str(self.clock()),
            field_capture=field_capture)
        trade.report_record, trade.report_digest = report.canonical(), report.digest()
        trade.inspect_tx = self.registry.inspect(self._sign("inspector"), trade.chain_lot_id, passed, grade,
                                                 quantity_kg, trade.report_digest)
        trade.passed = 1 if passed else 0
        trade.inspected_grade, trade.inspected_quantity_kg = grade, quantity_kg
        trade.moisture_pct, trade.inspection_notes = moisture_pct, notes
        trade.reject_reason = None if passed else reject_reason
        trade.inspected_at = self.clock()
        trade.status = "Approved" if passed else "Rejected"

    def fund(self, trade, amount_rwf, trade_id_seed):
        """The buyer locks payment in escrow. The escrow asks the registry who the payee is."""
        self._require("fund", trade)
        trade.buyer_name = self.personas.name("buyer")
        trade.buyer_account = self.personas.address("buyer")
        if self.token:
            # The token contract's "insufficient balance" is also error #10, which would otherwise be read
            # as the escrow's #10 ("lot has not passed inspection"), so check before signing.
            held = self.token.balance(self._sign("verifier"), trade.buyer_account)
            if held < self._units(amount_rwf):
                raise ChainError(f"The buyer holds {held / self.decimals:,.0f} RWF, less than the "
                                 f"{amount_rwf:,.0f} RWF to lock in escrow")
        trade.trade_id = trade_id_seed
        deadline = self.clock() + timedelta(days=self.escrow_term_days)
        trade.fund_tx = self.escrow.create(
            self._sign("verifier"), self._sign("buyer"), trade.trade_id, trade.chain_lot_id, self.token_id,
            self._units(amount_rwf), int(deadline.timestamp()))
        trade.amount_rwf = amount_rwf
        trade.funded_at = self.clock()
        trade.deadline = deadline
        trade.status = "Funded"

    def dispatch(self, trade, carrier, driver, vehicle_plate, seal_number, destination_port):
        """The carrier records dispatch; the waybill digest is attested (by the verifier, on its behalf)."""
        self._require("dispatch", trade)
        trade.carrier_name, trade.driver_name, trade.vehicle_plate = carrier, driver, vehicle_plate
        trade.seal_number, trade.destination_port = seal_number, destination_port
        trade.waybill_ref = f"WB-{trade.lot_ref.replace('AXK-', '')}"
        waybill = Waybill.from_trade(trade, carrier=carrier, driver=driver, vehicle_plate=vehicle_plate,
                                     seal_number=seal_number, destination_port=destination_port,
                                     dispatched_at=str(self.clock()))
        trade.waybill_record, trade.waybill_digest = waybill.canonical(), waybill.digest()
        trade.dispatch_tx = self.attestation.attest(self._sign("verifier"), Waybill.attestation_key(trade),
                                                    trade.waybill_digest)
        trade.dispatched_at = self.clock()
        trade.status = "In Transit"

    def receive_at_port(self, trade, port, container_id, customs_ref, arriving_seal=None):
        """Gate-in. The arriving seal must match the waybill's, or the step is refused as tampering."""
        self._require("receive_at_port", trade)
        if arriving_seal and trade.seal_number and \
                trade.seal_number.strip().lower() != arriving_seal.strip().lower():
            raise ChainError(f"Tamper Alert: Manifest seal {trade.seal_number} does not match gate-in seal {arriving_seal}!")
        trade.port_name, trade.container_id, trade.customs_ref = port, container_id, customs_ref
        trade.seal_verified = 1
        receipt = PortReceipt.from_trade(trade, port=port, container_id=container_id, customs_ref=customs_ref,
                                         received_at=str(self.clock()))
        trade.port_receipt_record, trade.port_receipt_digest = receipt.canonical(), receipt.digest()
        trade.port_tx = self.attestation.attest(self._sign("verifier"), PortReceipt.attestation_key(trade),
                                                trade.port_receipt_digest)
        trade.port_received_at = self.clock()
        trade.status = "At Port"

    def settle(self, trade):
        """Release, split, pay members, attest. Each completed step is saved before the next, so a failure
        part-way leaves an accurate record and a retry resumes from the first step not yet done."""
        self._require("settle", trade)
        amount = self._units(trade.amount_rwf)
        if not trade.release_tx:
            trade.release_tx = self.escrow.release(self._sign("verifier"), trade.trade_id)
            self.checkpoint(trade)
        if not trade.split_tx:
            shares = [(self.personas.address(role), bps) for role, bps in self.split_bps]
            trade.split_tx = self.splitter.configure(self._sign("verifier"), trade.trade_id, shares)
            self.checkpoint(trade)
        if not trade.distribute_tx:
            trade.distribute_tx = self.splitter.distribute(self._sign("coop"), trade.trade_id, self.token_id, amount)
            self.checkpoint(trade)
        if not trade.attest_tx:
            record = SettlementRecord.from_trade(trade, amount=amount, token=self.token_id)
            trade.settlement_record, trade.attest_digest = record.canonical(), record.digest()
            trade.attest_tx = self.attestation.attest(self._sign("verifier"), SettlementRecord.attestation_key(trade),
                                                      trade.attest_digest)
        trade.settled_at = self.clock()
        trade.status = "Settled"

    # -- verification -------------------------------------------------------------------------------------

    def verify(self, trade):
        """Ask the contracts whether each stored record still hashes to what was committed."""
        source = self._sign("verifier")
        result = {}
        if trade.chain_lot_id:
            result["lot_record"] = self.registry.matches(source, trade.chain_lot_id,
                                                         LotRecord.digest_of(trade.lot_record))
        anchored = [
            ("waybill_record", trade.dispatch_tx, trade.waybill_record, Waybill),
            ("port_receipt_record", trade.port_tx, trade.port_receipt_record, PortReceipt),
            ("settlement_record", trade.attest_tx, trade.settlement_record, SettlementRecord),
        ]
        for name, tx, stored, record_class in anchored:
            if tx and stored:
                result[name] = self.attestation.matches(source, record_class.attestation_key(trade),
                                                        record_class.digest_of(stored))
        return result
