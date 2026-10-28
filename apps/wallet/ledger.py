"""Append-only ledger; balances are the sum of entries."""


class Ledger:
    def __init__(self):
        self.entries = []

    def post(self, account, delta, memo=""):
        self.entries.append((account, delta, memo))

    def balance(self, account):
        return sum(delta for acct, delta, _ in self.entries if acct == account)
