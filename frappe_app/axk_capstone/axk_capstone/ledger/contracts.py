"""Clients for the four Soroban contracts and the RWF token.

Every call goes through one CommandRunner, which runs stellar-cli with an argument list and no shell: nothing a
participant types is ever interpolated into a command string. StellarCli runs the real binary; tests pass a
runner that records commands and returns scripted output instead.

ContractClient holds what every contract shares (building the invoke command, reading the transaction hash,
translating contract error codes). Each subclass adds its own typed methods and its own error messages.
"""

import json
import re
import subprocess
from abc import ABC, abstractmethod

TX_RE = re.compile(r"/tx/([0-9a-f]{64})")
ERR_RE = re.compile(r"Error\(Contract, #(\d+)\)")


class ChainError(Exception):
    """A transaction was refused or did not complete. The message is safe to show to the participant."""


class CommandRunner(ABC):
    @abstractmethod
    def run(self, args, timeout):
        """Run stellar-cli with these arguments; return (returncode, stdout, stderr)."""


class StellarCli(CommandRunner):
    def __init__(self, binary="stellar"):
        self.binary = binary

    def run(self, args, timeout):
        try:
            p = subprocess.run([self.binary, *args], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise ChainError("Stellar testnet did not answer in time") from e
        return p.returncode, p.stdout or "", p.stderr or ""


class Network:
    """A Stellar network reached through one runner: runs commands and resolves keystore identities."""

    def __init__(self, runner, name="testnet"):
        self.runner = runner
        self.name = name

    def execute(self, args, errors=None, timeout=90):
        code, out, err = self.runner.run(args, timeout)
        text = out + err
        if code != 0:
            m = ERR_RE.search(text)
            if m and errors:
                n = int(m.group(1))
                raise ChainError(errors.get(n, f"Contract error #{n}"))
            tail = text.strip().splitlines()[-1] if text.strip() else "unknown error"
            raise ChainError(tail[:300])
        tx = TX_RE.search(text)
        return out.strip(), (tx.group(1) if tx else None)

    def address(self, identity):
        out, _ = self.execute(["keys", "address", identity])
        return out.strip()

    def pay(self, source, destination, asset, amount):
        self.execute(["tx", "new", "payment", "--destination", destination, "--asset", asset,
                      "--amount", str(amount), "--source", source, "--network", self.name])


class ContractClient:
    """One deployed contract. ERRORS maps the contract's error codes to messages for participants."""

    ERRORS = {}

    def __init__(self, network, contract_id):
        self.network = network
        self.contract_id = contract_id

    def call(self, fn, source, args, send=True, extra=None):
        cmd = ["contract", "invoke", "--id", self.contract_id, "--source", source, "--network", self.network.name]
        if extra:
            cmd += extra
        if not send:
            cmd.append("--send=no")
        cmd += ["--", fn]
        for k, v in args.items():
            cmd += [f"--{k}", str(v)]
        return self.network.execute(cmd, errors=self.ERRORS)

    def read(self, fn, source, args):
        """A simulated call: nothing is submitted, the result is returned."""
        out, _ = self.call(fn, source, args, send=False)
        return out

    def _matches(self, source, args):
        return self.read("matches", source, args).strip() == "true"


class LotRegistry(ContractClient):
    ERRORS = {1: "Lot already registered", 2: "No such lot", 3: "Not an authorised inspector",
              4: "Lot already inspected", 5: "Quantity must be positive", 6: "Inspector owns this lot"}

    def register_lot(self, cooperative, lot_ref_hash, digest):
        """Returns (lot_id, tx). The lot id is derived on-chain from the cooperative and the reference."""
        out, tx = self.call("register_lot", cooperative,
                            {"cooperative": cooperative, "lot_ref": lot_ref_hash, "digest": digest})
        return out.strip('"'), tx

    def inspect(self, inspector, lot_id, passed, grade, quantity_kg, report_digest):
        _, tx = self.call("inspect", inspector, {
            "lot_id": lot_id, "inspector": inspector, "passed": "true" if passed else "false", "grade": grade,
            "quantity_kg": int(round(quantity_kg)), "report_digest": report_digest})
        return tx

    def matches(self, source, lot_id, digest):
        return self._matches(source, {"lot_id": lot_id, "digest": digest})


class Escrow(ContractClient):
    ERRORS = {3: "Trade already exists", 4: "No such trade", 5: "Trade is not funded",
              6: "Refund deadline not reached", 7: "Deadline in the past", 8: "Amount must be positive",
              9: "Deadline too far", 10: "Lot has not passed inspection", 11: "Lot is already in escrow"}

    def create(self, verifier, buyer, trade_id, lot_id, token_id, amount, deadline):
        """Buyer and verifier both sign one transaction (--auto-sign); there is no payee argument."""
        _, tx = self.call("create", verifier, {
            "trade_id": trade_id, "lot_id": lot_id, "buyer": buyer, "token_id": token_id,
            "amount": amount, "deadline": deadline}, extra=["--auto-sign"])
        return tx

    def release(self, verifier, trade_id):
        _, tx = self.call("release", verifier, {"trade_id": trade_id})
        return tx


class Splitter(ContractClient):
    def configure(self, coordinator, trade_id, shares):
        """shares: [(address, basis points)], totalling 10,000. Write-once per trade."""
        body = [{"party": party, "bps": str(bps)} for party, bps in shares]
        _, tx = self.call("configure", coordinator, {"trade_id": trade_id, "shares": json.dumps(body)})
        return tx

    def distribute(self, payer, trade_id, token_id, amount):
        _, tx = self.call("distribute", payer,
                          {"trade_id": trade_id, "token_id": token_id, "from": payer, "amount": amount})
        return tx


class Attestation(ContractClient):
    def attest(self, attester, key, digest):
        _, tx = self.call("attest", attester, {"trade_id": key, "digest": digest})
        return tx

    def matches(self, source, key, digest):
        return self._matches(source, {"trade_id": key, "digest": digest})


class Token(ContractClient):
    def balance(self, source, account):
        """Balance in the token's smallest unit."""
        return int(self.read("balance", source, {"id": account}).strip().strip('"') or 0)
