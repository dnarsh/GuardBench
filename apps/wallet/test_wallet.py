import threading
import unittest

import accounts
from accounts import Bank, InsufficientFunds
from api import get_balance, make_transfer
from fees import fee_for, with_fee
from limits import MAX_TRANSFER
from statements import statement


class WalletTests(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.bank.open("a", 100)
        self.bank.open("b", 0)

    def test_transfer_moves_money(self):
        self.bank.transfer("a", "b", 40)
        self.assertEqual((self.bank.balance("a"), self.bank.balance("b")), (60, 40))

    def test_overdraft_is_refused(self):
        with self.assertRaises(InsufficientFunds):
            self.bank.withdraw("a", 101)
        self.assertEqual(self.bank.balance("a"), 100)

    def test_non_positive_amounts_are_rejected_and_move_nothing(self):
        for amount in (0, -5):
            with self.assertRaises(ValueError):
                self.bank.transfer("a", "b", amount)
        self.assertEqual((self.bank.balance("a"), self.bank.balance("b")), (100, 0))

    def test_transfer_limit(self):
        self.bank.open("rich", MAX_TRANSFER * 2)
        with self.assertRaises(ValueError):
            self.bank.transfer("rich", "b", MAX_TRANSFER + 1)
        self.bank.transfer("rich", "b", MAX_TRANSFER)

    def test_api_status_codes(self):
        self.assertEqual(make_transfer(self.bank, "a", "b", 10)[0], 200)
        self.assertEqual(make_transfer(self.bank, "a", "b", -1)[0], 400)
        self.assertEqual(make_transfer(self.bank, "a", "b", 500)[0], 402)

    def test_concurrent_withdrawals_cannot_overdraw(self):
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        outcomes = []

        def attempt():
            try:
                self.bank.withdraw("a", 100)
                outcomes.append("ok")
            except InsufficientFunds:
                outcomes.append("refused")

        original = accounts._checkpoint
        accounts._checkpoint = hook
        try:
            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            accounts._checkpoint = original
        self.assertEqual(sorted(outcomes), ["ok", "refused"])
        self.assertEqual(self.bank.balance("a"), 0)


class HelperTests(unittest.TestCase):
    def test_history_names_and_totals(self):
        bank = Bank()
        bank.open("a", 50)
        bank.open("b", 5)
        bank.transfer("a", "b", 20)
        self.assertEqual(bank.names(), ["a", "b"])
        self.assertEqual([e[1] for e in bank.history("a")], [50, -20])
        self.assertEqual(bank.total_held(), 55)
        self.assertEqual(bank.ledger.count(), 4)
        self.assertEqual(bank.ledger.memos("b"), ["open", "transfer in"])

    def test_get_balance(self):
        bank = Bank()
        bank.open("a", 7)
        self.assertEqual(get_balance(bank, "a"), (200, "7"))
        self.assertEqual(get_balance(bank, "zzz")[0], 404)

    def test_statement_and_fees(self):
        bank = Bank()
        bank.open("a", 10)
        bank.withdraw("a", 4)
        self.assertEqual(statement(bank.ledger.entries, "a"),
                         ["a        +10 open", "a        -4 withdraw", "balance 6"])
        self.assertEqual([fee_for(x) for x in (0, 99, 100, 250, 1001)], [0, 0, 1, 3, 11])
        self.assertEqual(with_fee(200), 202)


if __name__ == "__main__":
    unittest.main()
