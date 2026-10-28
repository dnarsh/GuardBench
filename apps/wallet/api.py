"""Request layer over the bank."""
from accounts import Bank, InsufficientFunds


def make_transfer(bank, src, dst, amount):
    """Return (status, message)."""
    try:
        bank.transfer(src, dst, amount)
    except InsufficientFunds:
        return 402, "insufficient funds"
    except ValueError as e:
        return 400, str(e)
    return 200, "ok"
