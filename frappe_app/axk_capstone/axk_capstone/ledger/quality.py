"""Quality criteria: the limits a lot is inspected against, and the check of an inspector's measurements.

When a cooperative registers a lot, the limits for its commodity are copied into the lot (and so into the lot
record whose digest goes on-chain). The buyer sees them before funding, and they cannot change afterwards.

At inspection the inspector enters what was measured. assess() compares each measurement with its limit:

    grade      measured grade is at least the declared grade          (A is best, C is lowest)
    quantity   measured weight is at least declared x (1 - tolerance)  (a lot may not be lighter than sold)
    moisture   measured moisture is at most the commodity's limit      (only where moisture applies)

The system proposes the verdict. A pass is refused when any check fails, so payment can never be released for
a lot outside its agreed limits. The inspector may still reject a lot that meets every limit, for defects the
numbers do not capture (pests, mould, foreign matter, missing documents), but must give a listed reason.

The default limits below are configurable demo values for this capstone, chosen to be in line with common
East African trade practice. A real deployment replaces them with the standard named in the sales contract.
No Frappe import: this module is tested on its own (scripts/test_ledger.py).
"""

from dataclasses import dataclass, field

GRADE_ORDER = ("A", "B", "C")       # best first
QUANTITY_TOLERANCE_PCT = 2.0        # measured weight may be up to 2% under the declared weight

# commodity -> maximum moisture in percent (None: moisture is not checked for this commodity)
MAX_MOISTURE_PCT = {
    "Coffee (parchment)": 12.0,
    "Maize (dry grain)": 13.5,
    "Beans (dry)": 14.0,
    "Irish Potato": None,           # fresh produce: judged on defects and weight, not moisture
    "Rice (paddy)": 14.0,
    "Cassava (dried chips)": 13.0,
    "Sorghum": 13.5,
    "Wheat": 13.5,
}

BASIS = "AXK default limits for the commodity (configurable; replace with the contract's agreed standard)"

# reason labels, shared with chain.REJECT_REASONS
REASON_GRADE = "Grade below declared"
REASON_WEIGHT = "Weight below declared"
REASON_MOISTURE = "Moisture above tolerance"


@dataclass(frozen=True)
class QualityCriteria:
    """The agreed limits for one lot."""

    commodity: str
    min_grade: str
    declared_quantity_kg: float
    quantity_tolerance_pct: float = QUANTITY_TOLERANCE_PCT
    max_moisture_pct: float | None = None
    basis: str = BASIS

    @classmethod
    def for_lot(cls, commodity, declared_grade, declared_quantity_kg):
        return cls(commodity=commodity or "", min_grade=declared_grade or "C",
                   declared_quantity_kg=float(declared_quantity_kg or 0),
                   max_moisture_pct=MAX_MOISTURE_PCT.get(commodity))

    @property
    def min_quantity_kg(self):
        return round(self.declared_quantity_kg * (1 - self.quantity_tolerance_pct / 100), 3)

    def to_dict(self):
        return {"commodity": self.commodity, "min_grade": self.min_grade,
                "declared_quantity_kg": self.declared_quantity_kg,
                "quantity_tolerance_pct": self.quantity_tolerance_pct, "min_quantity_kg": self.min_quantity_kg,
                "max_moisture_pct": self.max_moisture_pct, "basis": self.basis}

    @classmethod
    def from_dict(cls, d):
        return cls(commodity=d["commodity"], min_grade=d["min_grade"],
                   declared_quantity_kg=float(d["declared_quantity_kg"]),
                   quantity_tolerance_pct=float(d["quantity_tolerance_pct"]),
                   max_moisture_pct=None if d.get("max_moisture_pct") is None else float(d["max_moisture_pct"]),
                   basis=d.get("basis", BASIS))


@dataclass
class Assessment:
    """The result of checking measurements against criteria: one entry per check, in a fixed order."""

    checks: list = field(default_factory=list)

    @property
    def passed(self):
        return all(c["ok"] for c in self.checks)

    @property
    def failed(self):
        return [c for c in self.checks if not c["ok"]]

    def suggested_reason(self):
        """The listed rejection reason for the first failed check, or None when every check passed."""
        return self.failed[0]["reason"] if self.failed else None

    def summary(self):
        return "; ".join(c["message"] for c in self.failed)

    def to_list(self):
        return [dict(c) for c in self.checks]


def _grade_rank(grade):
    return GRADE_ORDER.index(grade) if grade in GRADE_ORDER else len(GRADE_ORDER)


def assess(criteria, grade, quantity_kg, moisture_pct):
    """Check the inspector's measurements against the lot's criteria."""
    checks = []

    ok = _grade_rank(grade) <= _grade_rank(criteria.min_grade)
    checks.append({"check": "grade", "limit": f"{criteria.min_grade} or better", "measured": grade, "ok": ok,
                   "reason": None if ok else REASON_GRADE,
                   "message": f"grade {grade} meets {criteria.min_grade}" if ok
                   else f"grade {grade} is below the declared {criteria.min_grade}"})

    qty = float(quantity_kg)
    ok = qty >= criteria.min_quantity_kg
    checks.append({"check": "quantity", "limit": f">= {criteria.min_quantity_kg:g} kg", "measured": qty, "ok": ok,
                   "reason": None if ok else REASON_WEIGHT,
                   "message": f"{qty:g} kg is within {criteria.quantity_tolerance_pct:g}% of the declared "
                              f"{criteria.declared_quantity_kg:g} kg" if ok
                   else f"{qty:g} kg is below the minimum {criteria.min_quantity_kg:g} kg "
                        f"({criteria.quantity_tolerance_pct:g}% under the declared {criteria.declared_quantity_kg:g} kg)"})

    if criteria.max_moisture_pct is not None:
        limit = criteria.max_moisture_pct
        if moisture_pct is None:
            ok, msg = False, f"moisture was not measured (limit {limit:g}%)"
        else:
            ok = float(moisture_pct) <= limit
            msg = (f"moisture {float(moisture_pct):g}% is within the {limit:g}% limit" if ok
                   else f"moisture {float(moisture_pct):g}% is above the {limit:g}% limit")
        checks.append({"check": "moisture", "limit": f"<= {limit:g}%", "measured": moisture_pct, "ok": ok,
                       "reason": None if ok else REASON_MOISTURE, "message": msg})

    return Assessment(checks)
