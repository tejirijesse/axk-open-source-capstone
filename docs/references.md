# Reference projects

Open-source projects and open standards that AXK learns from. Each entry says why it matters and which roadmap
item it informs. None of them is a dependency today; check each project's current licence before reusing code.

| Project | What it is | Why it matters to AXK | Roadmap |
|---|---|---|---|
| **GS1 EPCIS** (open standard) + **openEPCIS** | EPCIS is the GS1 standard for recording what happened to an item, where and when. openEPCIS is an open-source implementation of EPCIS 2.0. | AXK's lot, inspection, dispatch and gate-in records are supply-chain events. Exporting them as EPCIS events lets customs, exporters and buyers' systems read them without learning AXK's format. | PUB-6 (done: [epcis.md](epcis.md)) |
| **farmOS** | Open-source farm record-keeping. | A model for cooperative, member and harvest data, so a lot can be built from real harvest records. | COOP-4 |
| **Open Food Network** | Open-source food marketplace software run by a global community. | A governance model for an agricultural open-source project with many local operators. | [GOVERNANCE.md](../GOVERNANCE.md) |
| **ODK (Open Data Kit)** | Offline-first field data collection (forms on Android). | Inspectors often work with poor connectivity. Inspection forms captured offline in ODK and submitted later fit how field inspection actually happens. | INSP-6 (done: [odk/README.md](../odk/README.md)), MOB-1 |
| **OpenLMIS** | Open-source logistics management system used across several African countries. | Shows how an open-source supply-chain system is adopted and funded with governments and donors. | Adoption |
| **Mojaloop** | Open-source payment interoperability software, backed by the Gates Foundation, for connecting banks and mobile-money providers. | The strongest model for how settled funds reach members' mobile-money accounts across providers. | SET-2, SET-3 ([design note](design/set-3-mojaloop-payouts.md)) |

## How they fit together

```
 field (ODK, farmOS)  →  AXK verification and escrow  →  records out (EPCIS)  →  money out (SEP-24 anchor, Mojaloop)
   capture lots and          register, inspect,            customs, exporters,       members paid in local
   inspections offline       escrow, settle on Stellar     buyers' systems           currency
```

AXK's own contribution is the middle: inspection-gated escrow and verifiable records on Stellar. The projects
above cover the edges, so AXK can connect to them instead of rebuilding them.
