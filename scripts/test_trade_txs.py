"""Checks that the txs list on lot rows follows the lot() step order (no server; frappe is stubbed).

    python3 scripts/test_trade_txs.py
"""
import os, sys, types, unittest
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class _dict(dict):
    __getattr__ = dict.get

fr = types.ModuleType("frappe"); fr._dict = _dict
fr.whitelist = lambda **k: (lambda f: f)
fr.PermissionError = PermissionError
fr.conf = _dict(); fr.session = _dict(user="Administrator")
fr.get_roles = lambda: ["System Manager"]
ut = types.ModuleType("frappe.utils")
ut.cint = int; ut.flt = float; ut.getdate = lambda x: x; ut.nowdate = lambda: "2026-10-30"
ut.get_datetime = lambda x: x if isinstance(x, datetime) else datetime.fromisoformat(str(x))
ut.get_system_timezone = lambda: "Africa/Kigali"
fr.utils = ut
sys.modules["frappe"] = fr; sys.modules["frappe.utils"] = ut
chain = types.ModuleType("axk_capstone.chain")
chain.tx_url = lambda t: f"u/{t}" if t else ""; chain.EXPLORER = "x"; chain.REJECT_REASONS = []
chain.conf = lambda: {}
setup = types.ModuleType("axk_capstone.setup"); setup.DEMO_ROLE = "AXK Capstone Demo"
pkg = types.ModuleType("axk_capstone"); pkg.__path__ = [os.path.join(ROOT, "frappe_app/axk_capstone/axk_capstone")]
pkg.chain = chain; pkg.setup = setup
sys.modules.update({"axk_capstone": pkg, "axk_capstone.chain": chain, "axk_capstone.setup": setup})
from axk_capstone import trade_api as T  # noqa: E402

TX = ["register_tx", "inspect_tx", "fund_tx", "dispatch_tx", "port_tx", "release_tx", "split_tx", "distribute_tx", "attest_tx"]

class Doc:
    """Document-like: attribute access plus .get, missing attrs None (BaseDocument semantics)."""
    def __init__(self, **kw): self.__dict__.update(kw)
    def __getattr__(self, k): return None
    def get(self, k, default=None): return self.__dict__.get(k, default)

def values(partial=False):
    v = {f: f"H{i}_{f}" for i, f in enumerate(TX)}
    if partial:
        for f in TX[5:]: v[f] = None
        v["port_tx"] = ""
    return v

class TestTxs(unittest.TestCase):
    def setUp(self):
        T._guard = lambda: None

    def test_lot_steps_and_txs_same_order(self):
        for partial in (False, True):
            d = Doc(name="L1", lot_ref="L1", status="Settled", passed=1, modified=datetime(2026, 10, 1), **values(partial))
            fr.get_doc = lambda dt, n: d
            out = T.lot("L1")
            self.assertEqual(len(out["txs"]), 9)
            self.assertEqual(out["txs"], [s["tx"] or "" for s in out["steps"]])
            self.assertTrue(all(isinstance(t, str) for t in out["txs"]))

    def test_overview_dict_rows(self):
        captured = {}
        def get_all(dt, fields=None, order_by=None):
            captured["fields"] = fields
            return [dict(name="L2", lot_ref="L2", status="Funded", modified="2026-10-01 10:00:00", **values(True))]
        fr.get_all = get_all
        out = T.overview()
        self.assertEqual(captured["fields"][-9:], TX)
        self.assertEqual(len(captured["fields"]), len(set(captured["fields"])))
        self.assertEqual(out["lots"][0]["txs"], ["H0_register_tx", "H1_inspect_tx", "H2_fund_tx", "H3_dispatch_tx", "", "", "", "", ""])

    def test_tx_fields_match_public_verify_list(self):
        src = open(os.path.join(ROOT, "frappe_app/axk_capstone/axk_capstone/verify.py")).read()
        line = [l for l in src.splitlines() if l.startswith("TX_FIELDS")][0]
        self.assertEqual(eval(line.split("=", 1)[1]), T.TX_FIELDS)

if __name__ == "__main__":
    unittest.main()
