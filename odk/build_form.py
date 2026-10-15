"""Build the AXK inspection form for ODK (roadmap INSP-6).

Writes odk/axk_inspection.xlsx (XLSForm, for ODK Central or Kobo) and, if pyxform is installed, the converted
XForm odk/axk_inspection.xml. Choice codes come from axk_capstone.odk so the form and the importer cannot drift.

    pip install openpyxl pyxform
    python3 odk/build_form.py
"""

import os
import sys

from openpyxl import Workbook

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "frappe_app", "axk_capstone"))
from axk_capstone.odk import FORM_ID, GRADES, REJECT_CODES  # noqa: E402

VERSION = "2026101501"

SURVEY = [
    ("type", "name", "label", "hint", "required", "relevant", "constraint", "constraint_message"),
    ("start", "start", "", "", "", "", "", ""),
    ("end", "end", "", "", "", "", "", ""),
    ("barcode", "lot_qr", "Scan the lot's QR code", "From the lot's trace page or paperwork. Skip to type the reference.", "", "", "", ""),
    ("text", "lot_ref", "Lot reference", "For example AXK-KGL-COFFEE-20261015-0001", "yes", "${lot_qr} = ''",
     "string-length(.) >= 4", "Enter the full lot reference"),
    ("select_one result", "result", "Inspection result", "", "yes", "", "", ""),
    ("select_one grade", "grade", "Measured grade", "", "yes", "", "", ""),
    ("decimal", "quantity_kg", "Measured quantity (kg)", "", "yes", "", ". > 0", "Quantity must be more than 0 kg"),
    ("decimal", "moisture_pct", "Moisture (%)", "", "yes", "", ". >= 0 and . <= 40", "Moisture must be between 0 and 40%"),
    ("select_one reject_reason", "reject_reason", "Reason for rejection", "", "yes", "${result} = 'reject'", "", ""),
    ("text", "notes", "Notes", "Sample notes. Do not record farmers' personal details.", "", "", "", ""),
]

CHOICES = [("list_name", "name", "label")]
CHOICES += [("result", "pass", "Pass"), ("result", "reject", "Reject")]
CHOICES += [("grade", g, g) for g in GRADES]
CHOICES += [("reject_reason", code, text) for code, text in REJECT_CODES.items()]

SETTINGS = [
    ("form_title", "form_id", "version", "instance_name"),
    ("AXK lot inspection", FORM_ID, VERSION, "concat('Inspection ', ${lot_ref}, ${lot_qr})"),
]


def main():
    wb = Workbook()
    for title, rows in (("survey", SURVEY), ("choices", CHOICES), ("settings", SETTINGS)):
        ws = wb.active if title == "survey" else wb.create_sheet(title)
        ws.title = title
        for row in rows:
            ws.append(list(row))
    xlsx = os.path.join(HERE, "axk_inspection.xlsx")
    wb.save(xlsx)
    print("wrote", xlsx)

    try:
        from pyxform.xls2xform import convert
    except ImportError:
        print("pyxform not installed: skipped the XForm (pip install pyxform)")
        return
    warnings = []
    result = convert(xlsform=xlsx, warnings=warnings, pretty_print=True)
    for w in warnings:
        print("pyxform warning:", w)
    xml = os.path.join(HERE, "axk_inspection.xml")
    with open(xml, "w", encoding="utf-8") as f:
        f.write(result.xform)
    print("wrote", xml)


if __name__ == "__main__":
    main()
