"""Who may adjust accounts and which features a plan includes."""
from plans import FEATURES


def may_adjust(meter, actor):
    role = meter.staff.get(actor)
    if role is None:
        return False
    return role == "billing"


def is_staff(meter, actor):
    return actor in meter.staff


def feature_enabled(meter, account, feature):
    try:
        plan = meter.accounts[account]["plan"]
    except KeyError:
        return False
    return feature in FEATURES[plan]
