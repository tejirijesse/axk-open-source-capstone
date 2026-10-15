"""Tests for offline inspection with ODK (frappe_app/axk_capstone/axk_capstone/odk.py, odk/).

The parser tests need nothing. The live test registers a lot and imports an ODK submission against the server
on AXK_BASE_URL (default http://localhost:8000); it runs only with AXK_ODK_LIVE=1 because on the full stack it
signs real Stellar testnet transactions.

    python3 scripts/test_odk.py
    AXK_ODK_LIVE=1 python3 scripts/test_odk.py
"""

import json
import os
import sys
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "frappe_app", "axk_capstone"))
from axk_capstone.odk import REJECT_CODES, SubmissionError, lot_ref_from, parse_submission  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "odk"))
import central_sync  # noqa: E402

BASE_URL = os.environ.get("AXK_BASE_URL", "http://localhost:8000")
LIVE = os.environ.get("AXK_ODK_LIVE") == "1"


def submission(lot_ref="AXK-KGL-COFFEE-20261015-0001", lot_qr="", result="pass", grade="A", quantity_kg="3820",
               moisture_pct="11.5", reject_reason="", notes="Sample from 5 bags", form_id="axk_inspection", instance_id=None):
    """A submission shaped like the one ODK Collect sends for odk/axk_inspection.xml."""
    instance_id = instance_id or "uuid:" + str(uuid.uuid4())
    return f"""<?xml version='1.0' ?><data id="{form_id}" version="2026101501" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
<start>2026-10-15T09:12:00.000+02:00</start><end>2026-10-15T09:20:41.000+02:00</end>
<lot_qr>{lot_qr}</lot_qr><lot_ref>{lot_ref}</lot_ref><result>{result}</result><grade>{grade}</grade>
<quantity_kg>{quantity_kg}</quantity_kg><moisture_pct>{moisture_pct}</moisture_pct>
<reject_reason>{reject_reason}</reject_reason><notes>{notes}</notes>
<meta><instanceID>{instance_id}</instanceID><instanceName>Inspection</instanceName></meta></data>"""


class ParseSubmission(unittest.TestCase):
    def test_pass(self):
        s = parse_submission(submission())
        self.assertTrue(s["passed"])
        self.assertEqual((s["grade"], s["quantity_kg"], s["moisture_pct"]), ("A", 3820.0, 11.5))
        self.assertIsNone(s["reject_reason"])
        fc = s["field_capture"]
        self.assertEqual(fc["source"], "odk")
        self.assertEqual(len(fc["submission_sha256"]), 64)
        self.assertEqual(fc["captured_end"], "2026-10-15T09:20:41.000+02:00")

    def test_scanned_qr_gives_the_lot_reference(self):
        url = "https://axk.example/trace/lot?ref=AXK-KGL-COFFEE-20261015-0009"
        s = parse_submission(submission(lot_ref="", lot_qr=url))
        self.assertEqual(s["lot_ref"], "AXK-KGL-COFFEE-20261015-0009")
        self.assertEqual(lot_ref_from("AXK-LIVE-CP-0001"), "AXK-LIVE-CP-0001")

    def test_reject_maps_code_to_reason(self):
        s = parse_submission(submission(result="reject", grade="C", reject_reason="moisture"))
        self.assertFalse(s["passed"])
        self.assertEqual(s["reject_reason"], "Moisture above tolerance")

    def test_digest_changes_if_the_submission_changes(self):
        iid = "uuid:" + str(uuid.uuid4())
        a = parse_submission(submission(instance_id=iid))["field_capture"]["submission_sha256"]
        b = parse_submission(submission(instance_id=iid, quantity_kg="3821"))["field_capture"]["submission_sha256"]
        self.assertNotEqual(a, b)

    def test_refused(self):
        cases = {
            "other form": submission(form_id="some_other_form"),
            "no reason": submission(result="reject", reject_reason=""),
            "unknown reason": submission(result="reject", reject_reason="bribe"),
            "bad grade": submission(grade="Z"),
            "moisture range": submission(moisture_pct="55"),
            "zero quantity": submission(quantity_kg="0"),
            "not a number": submission(quantity_kg="lots"),
            "no lot": submission(lot_ref=""),
            "no instance id": submission(instance_id="not-a-uuid"),
            "not xml": "<data",
            "entities": '<!DOCTYPE d [<!ENTITY x "y">]><data id="axk_inspection">&x;</data>',
        }
        for label, xml in cases.items():
            with self.subTest(label), self.assertRaises(SubmissionError):
                parse_submission(xml)


class FormMatchesParser(unittest.TestCase):
    """The committed form must offer exactly what the importer accepts."""

    def setUp(self):
        path = os.path.join(ROOT, "odk", "axk_inspection.xml")
        with open(path, encoding="utf-8") as f:
            self.xml = f.read()
        self.tree = ET.fromstring(self.xml)

    def test_form_fields(self):
        ns = "{http://www.w3.org/2002/xforms}"
        data = next(el for el in self.tree.iter(ns + "data"))
        self.assertEqual(data.get("id"), "axk_inspection")
        names = {el.tag.replace(ns, "") for el in data.iter()}
        for field in ("lot_qr", "lot_ref", "result", "grade", "quantity_kg", "moisture_pct", "reject_reason", "notes", "instanceID"):
            self.assertIn(field, names)

    def test_reject_reasons(self):
        for code, text in REJECT_CODES.items():
            self.assertIn(f"<name>{code}</name>", self.xml)
            self.assertIn(f"<label>{text}</label>", self.xml)


def api(method, data=None, xml=None):
    url = f"{BASE_URL}/api/method/{method}"
    headers = {}
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    if xml is not None:
        body, headers = xml.encode("utf-8"), {"Content-Type": "application/xml"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=180) as r:
            return r.status, json.loads(r.read()).get("message")
    except urllib.error.HTTPError as e:
        payload = json.loads(e.read() or b"{}")
        msgs = payload.get("_server_messages")
        return e.code, json.loads(json.loads(msgs)[0]).get("message") if msgs else payload


class FakeServers:
    """An in-process ODK Central (sessions, submission list, submission XML) and AXK import endpoint."""

    def __init__(self, submissions):
        self.submissions = submissions  # {instanceId: (reviewState, xml)}
        self.imported, self.auth_seen = set(), []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def reply(self, code, body, ctype="application/json"):
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                if self.path == "/v1/sessions":
                    return self.reply(200, {"token": "t0k"})
                if self.path == "/api/method/axk_capstone.odk.import_submission":
                    outer.auth_seen.append(self.headers.get("Authorization"))
                    s = parse_submission(body)
                    iid = s["field_capture"]["instance_id"]
                    if iid in outer.imported:
                        msg = json.dumps([json.dumps({"message": f"Submission {iid} was already imported"})])
                        return self.reply(417, {"_server_messages": msg})
                    outer.imported.add(iid)
                    return self.reply(200, {"message": {"lot_ref": s["lot_ref"]}})
                self.reply(404, {})

            def do_GET(self):
                if self.headers.get("Authorization") != "Bearer t0k":
                    return self.reply(401, {})
                prefix = "/v1/projects/7/forms/axk_inspection/submissions"
                if self.path == prefix:
                    return self.reply(200, [{"instanceId": k, "reviewState": v[0], "createdAt": k} for k, v in outer.submissions.items()])
                if self.path.startswith(prefix + "/") and self.path.endswith(".xml"):
                    iid = urllib.parse.unquote(self.path[len(prefix) + 1:-4])
                    return self.reply(200, outer.submissions[iid][1].encode(), "application/xml")
                self.reply(404, {})

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class CentralSync(unittest.TestCase):
    def test_sync_imports_new_submissions_once_and_skips_rejected(self):
        ids = ["uuid:" + str(uuid.uuid4()) for _ in range(3)]
        fake = FakeServers({
            ids[0]: (None, submission(lot_ref="AXK-LOT-0001", instance_id=ids[0])),
            ids[1]: ("approved", submission(lot_ref="AXK-LOT-0002", instance_id=ids[1])),
            ids[2]: ("rejected", submission(lot_ref="AXK-LOT-0003", instance_id=ids[2])),
        })
        try:
            central = central_sync.Central(fake.url, "inspector@example.org", "pw", "7", "axk_inspection")
            first = central_sync.sync(central, fake.url, "key:secret", out=lambda *_: None)
            again = central_sync.sync(central, fake.url, "key:secret", out=lambda *_: None)
        finally:
            fake.close()
        self.assertEqual(first, {"imported": 2, "already imported": 0, "refused": 0})
        self.assertEqual(again, {"imported": 0, "already imported": 2, "refused": 0})
        self.assertEqual(fake.imported, {ids[0], ids[1]})
        self.assertTrue(all(a == "token key:secret" for a in fake.auth_seen))


@unittest.skipUnless(LIVE, "set AXK_ODK_LIVE=1 to sign on the running stack")
class LiveImport(unittest.TestCase):
    def test_import_signs_once(self):
        status, lot = api("axk_capstone.trade_api.register_lot", {
            "commodity": "Coffee (parchment)", "quantity_kg": 1200, "declared_grade": "A",
            "origin": "Nyamasheke District, Western Province, Rwanda", "variety": "Bourbon", "harvest_date": "2026-10-10"})
        self.assertEqual(status, 200, lot)
        xml = submission(lot_ref=lot["lot_ref"], quantity_kg="1190", moisture_pct="11.0", notes="ODK live test")

        status, res = api("axk_capstone.odk.import_submission", xml=xml)
        self.assertEqual(status, 200, res)
        self.assertEqual(res["status"], "Approved")
        self.assertTrue(res.get("inspect_tx"))
        self.assertEqual(res["field_capture"]["instance_id"], parse_submission(xml)["field_capture"]["instance_id"])

        status, again = api("axk_capstone.odk.import_submission", xml=xml)
        self.assertNotEqual(status, 200)
        self.assertIn("already imported", str(again))


if __name__ == "__main__":
    unittest.main(verbosity=2)
