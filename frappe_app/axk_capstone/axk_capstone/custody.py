"""Custody Strip state: which of the nine on-chain steps are proven, and what each notch shows.

A notch is filled only when its step has a transaction hash. Nothing here infers progress.
"""

import re

STEPS = ["Registered", "Inspected", "Escrow funded", "Dispatched", "At port", "Released",
         "Split 40/40/20", "Members paid", "Attested"]

_HASH = re.compile(r"[0-9a-fA-F]{64}")


def proven(t):
    """A Stellar transaction hash (64 hex characters). Blanks, whitespace and anything else are not proof."""
    return isinstance(t, str) and bool(_HASH.fullmatch(t.strip()))


def _done(txs):
    """One proven flag per step, padded or cut to exactly len(STEPS) so the strip never misreads a short list."""
    done = [proven(t) for t in (txs or [])][:len(STEPS)]
    return done + [False] * (len(STEPS) - len(done))


def is_rejected(lot):
    """One rule for every page: the lot's status says Rejected, or a proven inspection did not pass."""
    if lot.get("status") == "Rejected":
        return True
    return proven(lot.get("inspect_tx")) and "passed" in lot and not lot.get("passed")


def notches(txs, rejected=False):
    """Per-notch state for the nine steps: on, next, pending, failed or off.

    On a rejected lot the inspection notch is `failed` (linked only if its hash exists) and later unproven
    notches are `off` (will not happen).
    A step that does carry a hash still shows `on`: the page never hides a transaction that exists.
    """
    done = _done(txs)
    if rejected:
        return ["failed" if i == 1 else "on" if d else "off" if i > 1 else "pending" for i, d in enumerate(done)]
    nxt = done.index(False) if False in done else -1
    return ["on" if d else "next" if i == nxt else "pending" for i, d in enumerate(done)]


def summary(txs, rejected=False):
    """(steps proven, label of the next step or None) for the aria text.

    Counts every proven step, including a failed inspection that carries its hash.
    """
    states = notches(txs, rejected)
    n = sum(_done(txs))
    return n, (STEPS[states.index("next")] if "next" in states else None)
