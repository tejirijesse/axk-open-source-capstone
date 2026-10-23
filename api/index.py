"""Vercel entry point for the offline simulation (scripts/server.py).

Vercel runs this as a Python function: every request is routed here (vercel.json) and handled by the same
request handler `make run` uses locally. Nothing is signed and nothing touches Stellar; every page says
"Offline simulation · not on-chain".

Vercel's code directory is read-only, so the simulation keeps its SQLite data in /tmp. A fresh instance
starts again from the seeded demo lots, so trades made on the public site do not last.
"""

import os
import sys
import urllib.parse

os.environ.setdefault("AXK_SIM_DB", "/tmp/axk-sim.db")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import server  # noqa: E402

server.init_db()


class handler(server.AXKHandler):
    """Vercel's rewrite (vercel.json) delivers every request as /api/index?__path=<original path>&<query>.
    Restore the original path and query before the simulation routes the request."""

    def _restore_path(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        original = query.pop("__path", [None])[0]
        if original is not None:
            self.path = original + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")

    def do_GET(self):
        self._restore_path()
        super().do_GET()

    def do_POST(self):
        self._restore_path()
        super().do_POST()
