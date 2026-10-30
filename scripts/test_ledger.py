"""Unit tests for the ledger object model (frappe_app/axk_capstone/axk_capstone/ledger).

No server, database or network: a FakeRunner stands in for stellar-cli, records every command and returns
scripted output. Covers the record classes, the contract clients' command building and error translation, and
the trade workflow's state machine from registration to settlement.

    python3 scripts/test_ledger.py
"""

import json
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frappe_app", "axk_capstone"))
from axk_capstone.ledger.contracts import (  # noqa: E402
    Attestation, ChainError, CommandRunner, ContractClient, Escrow, LotRegistry, Network, Splitter, Token,
)
from axk_capstone.ledger.records import (  # noqa: E402
    AttestedRecord, CanonicalRecord, InspectionReport, LotRecord, PortReceipt, SettlementRecord, Waybill,
    canonical, sha256_hex,
)
from axk_capstone.ledger.workflow import TRANSITIONS, Personas, TradeWorkflow  # noqa: E402

LOT_ID = "ab" * 32
NOW = datetime(2026, 10, 30, 9, 0, 0)


class FakeRunner(CommandRunner):
    """Records each stellar-cli call. Returns a transaction URL for submitted calls, and per-function output."""

    def __init__(self):
        self.calls = []
        self.fail_with = None          # (function name, stderr) to simulate a refused transaction
        self.outputs = {"register_lot": f'"{LOT_ID}"', "matches": "true", "balance": '"25000000000"'}

    def run(self, args, timeout):
        self.calls.append(args)
        if args[:2] == ["keys", "address"]:
            return 0, "G" + args[2].upper().replace("-", "")[:55].ljust(55, "A") + "\n", ""
        fn = args[args.index("--") + 1] if "--" in args else args[2]
        if self.fail_with and self.fail_with[0] == fn:
            return 1, "", self.fail_with[1]
        tx = f"{len(self.calls):064x}"
        submitted = "--send=no" not in args
        return 0, self.outputs.get(fn, "") + "\n", (f"https://stellar.expert/explorer/testnet/tx/{tx}\n" if submitted else "")

    def functions(self):
        return [a[a.index("--") + 1] for a in self.calls if "--" in a]


IDENTITIES = {r: {"identity": f"axk-{r}", "name": f"{r.title()} (demo)", "role": r}
              for r in ("coop", "inspector", "buyer", "verifier", "member1", "member2")}


def new_trade():
    return SimpleNamespace(
        lot_ref="AXK-KGL-COFFEE-20261030-0001", commodity="Coffee (parchment)", variety="Bourbon",
        declared_grade="A", quantity_kg=3850.0, origin="Huye", harvest_date="2026-10-10", status="",
        chain_lot_id=None, waybill_ref=None, seal_number=None, customs_ref=None, waybill_digest=None,
        port_receipt_digest=None, release_tx=None, split_tx=None, distribute_tx=None, attest_tx=None,
        dispatch_tx=None, port_tx=None, buyer_account=None, cooperative_account=None, trade_id=None)


def make_workflow(runner, saved=None):
    net = Network(runner)
    contracts = {"registry": LotRegistry(net, "CREG"), "escrow": Escrow(net, "CESC"),
                 "splitter": Splitter(net, "CSPL"), "attestation": Attestation(net, "CATT")}
    personas = Personas(IDENTITIES, lambda role: net.address(IDENTITIES[role]["identity"]))
    return TradeWorkflow(contracts, personas, token_id="CTOK", clock=lambda: NOW,
                         checkpoint=(saved.append if saved is not None else (lambda t: None)),
                         split_bps=[("member1", 4000), ("member2", 4000), ("coop", 2000)])


def run_to_settlement(wf, trade):
    wf.register(trade)
    wf.inspect(trade, True, "A", 3820.0, 11.5, "sampled 5 bags")
    wf.fund(trade, 250000, "cd" * 32)
    wf.dispatch(trade, "Carrier", "Driver", "RAD 000D", "RW-SEAL-1", "Kigali Logistics Platform")
    wf.receive_at_port(trade, "KLP", "CONT-1", "C-1", arriving_seal="rw-seal-1")
    wf.settle(trade)


class Records(unittest.TestCase):
    def test_class_hierarchy(self):
        for cls in (LotRecord, InspectionReport):
            self.assertTrue(issubclass(cls, CanonicalRecord))
        for cls in (Waybill, PortReceipt, SettlementRecord):
            self.assertTrue(issubclass(cls, AttestedRecord))
        with self.assertRaises(TypeError):
            CanonicalRecord(x=1)   # abstract: a record must say how it is built from a trade

    def test_canonical_json_is_order_independent(self):
        self.assertEqual(canonical({"b": 1, "a": 2}), canonical({"a": 2, "b": 1}))
        self.assertEqual(canonical({"a": 1, "b": "é"}), '{"a":1,"b":"é"}')

    def test_lot_digest_matches_the_original_format(self):
        """The refactor must not change any digest already committed on-chain."""
        t = new_trade()
        record = LotRecord.from_trade(t, cooperative="GCOOP")
        old = {"lot_ref": t.lot_ref, "commodity": t.commodity, "variety": t.variety, "declared_grade": "A",
               "quantity_kg": 3850.0, "origin": "Huye", "harvest_date": "2026-10-10", "cooperative": "GCOOP"}
        self.assertEqual(record.digest(), sha256_hex(json.dumps(old, sort_keys=True, separators=(",", ":"))))

    def test_any_change_changes_the_digest(self):
        t = new_trade()
        a = LotRecord.from_trade(t, cooperative="GCOOP")
        t.quantity_kg = 3851.0
        self.assertNotEqual(a.digest(), LotRecord.from_trade(t, cooperative="GCOOP").digest())

    def test_rejection_keeps_reason_and_pass_drops_it(self):
        t = new_trade()
        common = dict(grade="B", quantity_kg=1.0, moisture_pct=17.0, notes="", inspector="GI", inspected_at="x")
        self.assertEqual(InspectionReport.from_trade(t, passed=False, reject_reason="Moisture above tolerance", **common)
                         .fields["reject_reason"], "Moisture above tolerance")
        self.assertIsNone(InspectionReport.from_trade(t, passed=True, reject_reason="ignored", **common)
                          .fields["reject_reason"])

    def test_attestation_keys_differ_per_record_type(self):
        t = new_trade()
        t.waybill_ref, t.customs_ref, t.trade_id = "WB-1", "C-1", "ef" * 32
        keys = {Waybill.attestation_key(t), PortReceipt.attestation_key(t), SettlementRecord.attestation_key(t)}
        self.assertEqual(len(keys), 3)


class Contracts(unittest.TestCase):
    def setUp(self):
        self.runner = FakeRunner()
        self.net = Network(self.runner)

    def test_invoke_command_is_an_argument_list(self):
        LotRegistry(self.net, "CREG").register_lot("axk-coop", "aa" * 32, "bb" * 32)
        cmd = self.runner.calls[-1]
        self.assertEqual(cmd[:8], ["contract", "invoke", "--id", "CREG", "--source", "axk-coop", "--network", "testnet"])
        self.assertIn("--digest", cmd)

    def test_reads_are_not_submitted(self):
        self.assertTrue(Attestation(self.net, "CATT").matches("axk-verifier", "k", "d"))
        self.assertIn("--send=no", self.runner.calls[-1])
        self.assertEqual(Token(self.net, "CTOK").balance("axk-verifier", "GBUYER"), 25000000000)

    def test_escrow_funding_is_co_signed_and_has_no_payee(self):
        Escrow(self.net, "CESC").create("axk-verifier", "axk-buyer", "t", LOT_ID, "CTOK", 10, 99)
        cmd = self.runner.calls[-1]
        self.assertIn("--auto-sign", cmd)
        self.assertNotIn("--to", cmd)
        self.assertNotIn("--payee", cmd)

    def test_contract_errors_become_messages(self):
        self.runner.fail_with = ("create", "error: HostError: Error(Contract, #10)")
        with self.assertRaisesRegex(ChainError, "Lot has not passed inspection"):
            Escrow(self.net, "CESC").create("v", "b", "t", LOT_ID, "CTOK", 10, 99)
        self.runner.fail_with = ("inspect", "error: HostError: Error(Contract, #6)")
        with self.assertRaisesRegex(ChainError, "Inspector owns this lot"):
            LotRegistry(self.net, "CREG").inspect("i", LOT_ID, True, "A", 1, "d")

    def test_each_contract_has_its_own_error_table(self):
        self.assertIsNot(LotRegistry.ERRORS, Escrow.ERRORS)
        self.assertEqual(ContractClient.ERRORS, {})

    def test_split_shares_serialise_as_json(self):
        Splitter(self.net, "CSPL").configure("v", "t", [("GA", 4000), ("GB", 6000)])
        cmd = self.runner.calls[-1]
        self.assertEqual(json.loads(cmd[cmd.index("--shares") + 1]),
                         [{"party": "GA", "bps": "4000"}, {"party": "GB", "bps": "6000"}])


class Workflow(unittest.TestCase):
    def test_full_lifecycle(self):
        runner, saved, t = FakeRunner(), [], new_trade()
        wf = make_workflow(runner, saved)
        run_to_settlement(wf, t)
        self.assertEqual(t.status, "Settled")
        self.assertEqual(runner.functions(),
                         ["register_lot", "inspect", "create", "attest", "attest", "release", "configure",
                          "distribute", "attest"])
        for field in ("register_tx", "inspect_tx", "fund_tx", "dispatch_tx", "port_tx", "release_tx",
                      "split_tx", "distribute_tx", "attest_tx"):
            self.assertRegex(getattr(t, field), r"^[0-9a-f]{64}$", field)
        self.assertEqual(len(saved), 3, "settlement saves after release, split and distribute")
        self.assertEqual(t.chain_lot_id, LOT_ID)

    def test_amounts_are_in_token_units(self):
        runner, t = FakeRunner(), new_trade()
        run_to_settlement(make_workflow(runner), t)
        create = next(a for a in runner.calls if "create" in a)
        self.assertEqual(create[create.index("--amount") + 1], str(250000 * 10**7))

    def test_settlement_record_links_every_earlier_digest(self):
        t = new_trade()
        run_to_settlement(make_workflow(FakeRunner()), t)
        record = json.loads(t.settlement_record)
        for key in ("lot_digest", "report_digest", "waybill_digest", "port_receipt_digest"):
            self.assertEqual(record[key], getattr(t, key))
        self.assertEqual(t.attest_digest, sha256_hex(t.settlement_record))

    def test_state_machine_refuses_out_of_order_steps(self):
        wf, t = make_workflow(FakeRunner()), new_trade()
        wf.register(t)
        with self.assertRaisesRegex(ChainError, "only inspected, approved lots can be funded"):
            wf.fund(t, 1, "t")
        with self.assertRaisesRegex(ChainError, "must be In Transit"):
            wf.receive_at_port(t, "P", "C", "X")
        self.assertEqual(set(TRANSITIONS), {"register", "inspect", "fund", "dispatch", "receive_at_port", "settle"})

    def test_rejected_lot_cannot_continue(self):
        wf, t = make_workflow(FakeRunner()), new_trade()
        wf.register(t)
        wf.inspect(t, False, "C", 3000.0, 18.0, "", reject_reason="Moisture above tolerance")
        self.assertEqual(t.status, "Rejected")
        with self.assertRaises(ChainError):
            wf.fund(t, 1, "t")

    def test_seal_mismatch_is_refused_and_nothing_is_attested(self):
        runner, t = FakeRunner(), new_trade()
        wf = make_workflow(runner)
        wf.register(t)
        wf.inspect(t, True, "A", 1.0, 11.0, "")
        wf.fund(t, 1, "t")
        wf.dispatch(t, "C", "D", "P", "RW-SEAL-1", "KLP")
        before = len(runner.calls)
        with self.assertRaisesRegex(ChainError, "Tamper Alert"):
            wf.receive_at_port(t, "KLP", "C", "X", arriving_seal="RW-SEAL-9")
        self.assertEqual(t.status, "In Transit")
        self.assertEqual(len(runner.calls), before)

    def test_refused_transaction_leaves_trade_unchanged(self):
        runner, t = FakeRunner(), new_trade()
        wf = make_workflow(runner)
        wf.register(t)
        runner.fail_with = ("inspect", "error: HostError: Error(Contract, #3)")
        with self.assertRaisesRegex(ChainError, "Not an authorised inspector"):
            wf.inspect(t, True, "A", 1.0, 11.0, "")
        self.assertEqual(t.status, "Registered")
        self.assertIsNone(getattr(t, "inspect_tx", None))

    def test_settlement_resumes_after_a_partial_failure(self):
        runner, t = FakeRunner(), new_trade()
        wf = make_workflow(runner)
        wf.register(t)
        wf.inspect(t, True, "A", 1.0, 11.0, "")
        wf.fund(t, 1, "t")
        runner.fail_with = ("distribute", "error: network timeout")
        with self.assertRaises(ChainError):
            wf.settle(t)
        self.assertTrue(t.release_tx and t.split_tx and not t.distribute_tx)
        runner.fail_with = None
        wf.settle(t)
        self.assertEqual(runner.functions().count("release"), 1, "a completed step is never repeated")
        self.assertEqual(t.status, "Settled")

    def test_verify_checks_every_anchored_record(self):
        t = new_trade()
        wf = make_workflow(FakeRunner())
        run_to_settlement(wf, t)
        self.assertEqual(wf.verify(t), {"lot_record": True, "waybill_record": True,
                                        "port_receipt_record": True, "settlement_record": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
