# Offline inspection with ODK

Inspectors often work where there is no connection. With [ODK](https://getodk.org) they fill the AXK inspection
form on an Android phone, offline, and the inspection is signed on Stellar when the submission reaches AXK
(roadmap INSP-6).

```
ODK Collect (offline)  →  ODK Central  →  odk/central_sync.py  →  AXK  →  lot registry on Stellar
        or: copy the submission file  →  Inspector screen "Import an offline inspection (ODK)"
```

## Files

| File | What it is |
|---|---|
| `axk_inspection.xlsx` | The form (XLSForm). Upload it to ODK Central, or Kobo. |
| `axk_inspection.xml` | The same form converted to XForm. |
| `build_form.py` | Generates both from code, using the importer's own choice lists so they cannot drift. |
| `central_sync.py` | Pulls submissions from ODK Central and imports them into AXK. |

The importer is `frappe_app/axk_capstone/axk_capstone/odk.py`.

## The form

- The inspector scans the lot's QR code (from its `/trace` page or paperwork) or types the lot reference.
- They enter the result (pass or reject), measured grade, quantity in kg and moisture (0–40%).
- A rejection requires one of the six reasons the Inspector screen uses.
- Notes are optional. The form asks inspectors not to record farmers' personal details.

## What AXK checks on import

- It is a submission of this form, with a valid `instanceID`, and every value is in range.
- The lot exists and is still awaiting inspection.
- The same submission has not been imported before.
- The request passes the same access guard and hourly limit as the Inspector screen.

The inspection is then signed exactly like one made on `/trade/inspect`. The report record also gets a
`field_capture` block: the form version, the submission's `instanceID`, the start and end time on the phone, and
the **SHA-256 of the original submission**. Because the report's digest is stored in the lot registry
contract, the chain commits to what was captured in the field. Changing the submission afterwards would no
longer match.

## Using it

1. **Form:** upload `axk_inspection.xlsx` to a project on ODK Central and give the inspectors app users.
2. **Field:** inspectors fill it in ODK Collect, offline, and send when they have a connection.
3. **Import**, either way:
   - **Automatically:** `python3 odk/central_sync.py` with the variables listed at the top of that file. It is
     safe to run on a schedule, because already-imported submissions are skipped.
   - **By hand:** download a submission's XML from Central and use *Import an offline inspection (ODK)* at the
     bottom of `/trade/inspect`.

To change the form, edit `build_form.py` (and `REJECT_CODES` in `odk.py` if the reasons change), then run:

```bash
pip install openpyxl pyxform
python3 odk/build_form.py
```

## Tests

```bash
make test-odk                          # parser, form and Central-sync tests; no server needed
AXK_ODK_LIVE=1 python3 scripts/test_odk.py   # also signs a real import on the running stack (testnet)
```

The Central-sync test runs against an in-process stand-in for ODK Central's API. The script has not yet been
run against a live ODK Central server; reports from anyone who does are welcome.

## Limits

- The inspection is signed by the server-held inspector key, as on the Inspector screen. ODK proves what was
  captured on the phone, not who held the phone. A per-inspector key or an ODK Central account mapped to an
  inspector address is the next step.
- Photos are not part of the form yet; see INSP-1.
