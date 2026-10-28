"""Transfer fees."""
from limits import FEE_FREE_BELOW

FEE_RATE_PERCENT = 1


def fee_for(amount):
    """Whole-unit fee: nothing below FEE_FREE_BELOW, else FEE_RATE_PERCENT percent rounded up."""
    if amount < FEE_FREE_BELOW:
        return 0
    return -(-amount * FEE_RATE_PERCENT // 100)


def with_fee(amount):
    return amount + fee_for(amount)
