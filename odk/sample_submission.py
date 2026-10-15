"""Write a sample submission of the AXK inspection form, shaped like the XML ODK Collect sends.

For demos and testing without a phone or an ODK Central server:

    python3 odk/sample_submission.py AXK-LIVE-CP-20261015-0005 > ~/Desktop/inspection.xml
    python3 odk/sample_submission.py AXK-LIVE-CP-20261015-0005 reject moisture > ~/Desktop/inspection.xml

Then use "Import an offline inspection (ODK)" on /trade/inspect. Each run gets a new instanceID.
"""

import sys
import uuid
from datetime import datetime, timedelta
from xml.sax.saxutils import escape


def submission(lot_ref, result="pass", reason="", grade="A", quantity_kg="1180", moisture_pct="11.4",
               notes="Field inspection captured offline in ODK Collect"):
    end = datetime.now().astimezone().replace(microsecond=0)
    start = end - timedelta(minutes=9)
    if result == "reject":
        grade, moisture_pct = "B", "17.2"
    return (
        "<?xml version='1.0' ?>"
        '<data id="axk_inspection" version="2026101501" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">'
        f"<start>{start.isoformat()}</start><end>{end.isoformat()}</end>"
        f"<lot_qr></lot_qr><lot_ref>{escape(lot_ref)}</lot_ref><result>{result}</result><grade>{grade}</grade>"
        f"<quantity_kg>{quantity_kg}</quantity_kg><moisture_pct>{moisture_pct}</moisture_pct>"
        f"<reject_reason>{reason if result == 'reject' else ''}</reject_reason><notes>{escape(notes)}</notes>"
        f"<meta><instanceID>uuid:{uuid.uuid4()}</instanceID><instanceName>Inspection {escape(lot_ref)}</instanceName></meta>"
        "</data>\n"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    result = sys.argv[2] if len(sys.argv) > 2 else "pass"
    reason = sys.argv[3] if len(sys.argv) > 3 else ("moisture" if result == "reject" else "")
    sys.stdout.write(submission(sys.argv[1], result, reason))
