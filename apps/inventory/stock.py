"""Stock levels with reservations."""
import threading


def _checkpoint():
    """No-op hook between the availability check and the debit; tests interleave threads here."""


class OutOfStock(Exception):
    pass


class Stock:
    def __init__(self):
        self.levels = {}
        self._lock = threading.Lock()

    def add(self, sku, qty):
        """Receive qty more units of sku."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.levels[sku] = self.levels.get(sku, 0) + qty

    def available(self, sku):
        return self.levels.get(sku, 0)

    def reserve(self, sku, qty):
        """Take qty units of sku or raise OutOfStock."""
        with self._lock:
            if self.levels.get(sku, 0) < qty:
                raise OutOfStock(sku)
            _checkpoint()
            self.levels[sku] = self.levels.get(sku, 0) - qty

    def skus(self):
        """Known SKUs, sorted."""
        return sorted(self.levels)
