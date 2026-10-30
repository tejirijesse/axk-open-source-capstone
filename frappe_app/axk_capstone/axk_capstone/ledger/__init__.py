"""Object model for the AXK trade ledger.

    records    canonical records: each one is hashed, and only its SHA-256 digest goes on-chain
    contracts  one client class per Soroban contract, sharing a single command runner
    workflow   the trade lifecycle as a state machine that drives the contracts

None of these modules imports Frappe: the app supplies configuration, clock, cache and persistence through
chain.py, so the whole lifecycle can be unit-tested without a server or a network (scripts/test_ledger.py).
"""
