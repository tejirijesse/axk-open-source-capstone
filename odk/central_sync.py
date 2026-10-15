"""Pull AXK inspection submissions from ODK Central and import them into AXK (roadmap INSP-6).

Inspectors submit from ODK Collect to an ODK Central server when they get a connection. This script lists the
form's submissions on Central, downloads each one as XML and posts it to AXK, which signs the inspection
on-chain. Run it by hand or on a schedule (cron); it is safe to re-run, because AXK refuses a submission it has
already imported and the script counts that as done.

Configuration (environment variables; nothing is stored or printed):

    CENTRAL_URL        https://central.example.org
    CENTRAL_EMAIL      a Central web user with access to the project
    CENTRAL_PASSWORD
    CENTRAL_PROJECT    numeric project ID
    CENTRAL_FORM       form ID (default axk_inspection)
    AXK_URL            http://localhost:8000
    AXK_API_KEY        "<api key>:<api secret>" of a Frappe user with the AXK Capstone Demo role
                       (omit only for a local site in demo mode)

    python3 odk/central_sync.py

Uses ODK Central's REST API (v1): POST /v1/sessions, GET .../forms/{form}/submissions and
GET .../submissions/{instanceId}.xml. Standard library only.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _request(url, data=None, headers=None, method=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


class Central:
    def __init__(self, url, email, password, project, form):
        self.base = url.rstrip("/") + "/v1"
        self.project, self.form = project, form
        body = json.dumps({"email": email, "password": password}).encode()
        token = json.loads(_request(self.base + "/sessions", body, {"Content-Type": "application/json"}))["token"]
        self.auth = {"Authorization": "Bearer " + token}

    def _form_url(self):
        return f"{self.base}/projects/{self.project}/forms/{urllib.parse.quote(self.form)}"

    def submission_ids(self):
        rows = json.loads(_request(self._form_url() + "/submissions", headers=self.auth))
        # Oldest first, and skip submissions a Central reviewer marked as rejected.
        rows.sort(key=lambda r: r.get("createdAt") or "")
        return [r["instanceId"] for r in rows if r.get("reviewState") != "rejected"]

    def submission_xml(self, instance_id):
        return _request(f"{self._form_url()}/submissions/{urllib.parse.quote(instance_id)}.xml", headers=self.auth)


def import_into_axk(axk_url, api_key, xml):
    """Returns ("imported", lot_ref) | ("already imported", None) | ("refused", message)."""
    headers = {"Content-Type": "application/xml", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = "token " + api_key
    try:
        body = json.loads(_request(axk_url.rstrip("/") + "/api/method/axk_capstone.odk.import_submission", xml, headers, "POST"))
        return "imported", body["message"]["lot_ref"]
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        try:
            payload = json.loads(raw)
            msgs = payload.get("_server_messages")
            message = json.loads(json.loads(msgs)[0]).get("message") if msgs else str(payload)
        except ValueError:
            message = raw[:200].decode("utf-8", "replace")
        if "already imported" in message:
            return "already imported", None
        return "refused", message


def sync(central, axk_url, api_key, out=print):
    counts = {"imported": 0, "already imported": 0, "refused": 0}
    for iid in central.submission_ids():
        outcome, detail = import_into_axk(axk_url, api_key, central.submission_xml(iid))
        counts[outcome] += 1
        if outcome != "already imported":
            out(f"{iid}: {outcome}" + (f" ({detail})" if detail else ""))
    out(", ".join(f"{v} {k}" for k, v in counts.items()))
    return counts


def main():
    env = os.environ
    missing = [k for k in ("CENTRAL_URL", "CENTRAL_EMAIL", "CENTRAL_PASSWORD", "CENTRAL_PROJECT", "AXK_URL") if not env.get(k)]
    if missing:
        sys.exit("Set " + ", ".join(missing) + " (see the top of this file)")
    central = Central(env["CENTRAL_URL"], env["CENTRAL_EMAIL"], env["CENTRAL_PASSWORD"], env["CENTRAL_PROJECT"],
                      env.get("CENTRAL_FORM", "axk_inspection"))
    counts = sync(central, env["AXK_URL"], env.get("AXK_API_KEY"))
    sys.exit(1 if counts["refused"] else 0)


if __name__ == "__main__":
    main()
