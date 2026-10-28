"""Accounts with overdraft protection."""
import threading

from ledger import Ledger
from limits import MAX_TRANSFER


def _checkpoint():
    """No-op hook between the balance check and the debit; tests use it to interleave threads."""


class InsufficientFunds(Exception):
    pass


class Bank:
    def __init__(self):
        self.ledger = Ledger()
        self._lock = threading.Lock()

    def open(self, name, deposit=0):
        self.ledger.post(name, deposit, "open")

    def balance(self, name):
        return self.ledger.balance(name)

    def withdraw(self, name, amount):
        with self._lock:
            if self.ledger.balance(name) < amount:
                raise InsufficientFunds(name)
            _checkpoint()
            self.ledger.post(name, -amount, "withdraw")

    def transfer(self, src, dst, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > MAX_TRANSFER:
            raise ValueError("amount over limit")
        self.withdraw(src, amount)
        self.ledger.post(dst, amount, "transfer in")

    def history(self, name):
        """Ledger entries of one account, oldest first."""
        return [entry for entry in self.ledger.entries if entry[0] == name]

    def names(self):
        """All account names, sorted."""
        found = {account for account, _, _ in self.ledger.entries}
        return sorted(found)

    def total_held(self):
        """Money held across every account."""
        return sum(delta for _, delta, _ in self.ledger.entries)
