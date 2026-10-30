"""Unit tests for the Custody Strip state (frappe_app/axk_capstone/axk_capstone/custody.py).

Pure Python, no server and no Frappe.

    python3 scripts/test_custody.py
"""

import importlib.util
import os
import unittest

_PATH = os.path.join(os.path.dirname(__file__), "..", "frappe_app", "axk_capstone", "axk_capstone", "custody.py")
_spec = importlib.util.spec_from_file_location("custody", _PATH)
custody = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(custody)

TX = "ab" * 32


class TestCustody(unittest.TestCase):
    def test_nine_steps(self):
        self.assertEqual(len(custody.STEPS), 9)

    def test_all_on(self):
        txs = [TX] * 9
        self.assertEqual(custody.notches(txs), ["on"] * 9)
        self.assertEqual(custody.summary(txs), (9, None))

    def test_partial_marks_first_unfilled_next(self):
        txs = [TX] * 4 + [None] * 5
        self.assertEqual(custody.notches(txs), ["on"] * 4 + ["next"] + ["pending"] * 4)
        self.assertEqual(custody.summary(txs), (4, custody.STEPS[4]))

    def test_empty(self):
        txs = [None] * 9
        self.assertEqual(custody.notches(txs), ["next"] + ["pending"] * 8)
        self.assertEqual(custody.summary(txs)[0], 0)

    def test_filled_only_with_tx(self):
        for blank in (None, "", 0):
            self.assertNotIn("on", custody.notches([blank] * 9))

    def test_gap_does_not_fill_later_notch_by_inference(self):
        txs = [TX, None, TX] + [None] * 6
        st = custody.notches(txs)
        self.assertEqual(st[:3], ["on", "next", "on"])

    def test_rejected(self):
        txs = [TX, TX] + [None] * 7
        self.assertEqual(custody.notches(txs, rejected=True), ["on", "failed"] + ["off"] * 7)

    def test_only_a_64_hex_hash_counts(self):
        for junk in ("  ", "\n", "garbage", "ab" * 31, "zz" * 32, 0, 1, True, ["x"]):
            self.assertNotIn("on", custody.notches([junk] * 9), repr(junk))
        self.assertEqual(custody.notches([" " + TX + "\n"] * 9), ["on"] * 9)

    def test_length_is_normalised_to_nine(self):
        for txs in (None, [], [TX] * 3, [TX] * 12):
            self.assertEqual(len(custody.notches(txs)), 9, txs)
        self.assertEqual(custody.summary([TX] * 3), (3, custody.STEPS[3]))
        self.assertEqual(custody.summary([TX] * 12), (9, None))
        self.assertEqual(custody.summary(None), (0, custody.STEPS[0]))

    def test_rejected_never_hides_a_later_hash(self):
        txs = [TX, TX, TX] + [None] * 6
        self.assertEqual(custody.notches(txs, rejected=True), ["on", "failed", "on"] + ["off"] * 6)

    def test_rejected_without_inspection_hash(self):
        self.assertEqual(custody.notches([TX] + [None] * 8, rejected=True), ["on", "failed"] + ["off"] * 7)
        self.assertEqual(custody.notches([None] * 9, rejected=True), ["pending", "failed"] + ["off"] * 7)
        self.assertEqual(custody.summary([None] * 9, rejected=True), (0, None))

    def test_summary_counts_every_proven_step(self):
        cases = [[TX] * 9, [None] * 9, [TX, None, TX] + [None] * 6, ["  "] * 9, [TX] * 4]
        for txs in cases:
            self.assertEqual(custody.summary(txs)[0], custody.notches(txs).count("on"))
        self.assertEqual(custody.summary([TX, TX] + [None] * 7, rejected=True), (2, None))
        self.assertEqual(custody.summary([TX, None] + [None] * 7, rejected=True), (1, None))
        self.assertEqual(custody.summary([TX, TX, TX] + [None] * 6, rejected=True), (3, None))

    def test_proven_is_exposed_for_the_page(self):
        self.assertTrue(custody.proven(TX))
        self.assertFalse(custody.proven("garbage"))
        self.assertFalse(custody.proven(None))

    def test_one_rejected_rule_for_both_pages(self):
        self.assertTrue(custody.is_rejected({"status": "Rejected"}))
        self.assertTrue(custody.is_rejected({"status": "Inspected", "inspect_tx": TX, "passed": 0}))
        self.assertFalse(custody.is_rejected({"status": "Approved", "inspect_tx": TX, "passed": 1}))
        self.assertFalse(custody.is_rejected({"status": "Registered", "inspect_tx": None, "passed": 0}))
        self.assertFalse(custody.is_rejected({"status": "Registered", "inspect_tx": TX}))

    def test_real_caller_inputs(self):
        steps = [{"label": l, "tx": TX if i < 2 else None} for i, l in enumerate(custody.STEPS)]
        self.assertEqual(custody.notches([s["tx"] for s in steps]), ["on", "on", "next"] + ["pending"] * 6)
        row = {"status": "Approved", "register_tx": TX, "inspect_tx": TX, "passed": 1}
        txs = [row.get(f) for f in ("register_tx", "inspect_tx", "fund_tx")]
        self.assertEqual(custody.summary(txs, custody.is_rejected(row)), (2, custody.STEPS[2]))


if __name__ == "__main__":
    unittest.main()
