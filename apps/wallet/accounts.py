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
