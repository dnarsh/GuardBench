import threading
import unittest

import accounts
from accounts import Bank, InsufficientFunds
from api import make_transfer
from limits import MAX_TRANSFER


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


if __name__ == "__main__":
    unittest.main()
